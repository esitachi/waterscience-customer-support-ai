"""
WaterScience Support Platform — Asynchronous Queue & Concurrency Manager
Provides queue coordination, idempotent deduplication, exponential backoff retries,
dead-letter queue (DLQ), and live telemetry.
Uses multithreaded worker pool for reliable cross-environment concurrency.
"""

import time
import queue
import threading
import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from app.config import settings
from app.database import SessionLocal, ProcessingJobRecord, MessageRecord, ConversationRecord, TicketRecord
from app.models import IngestMessageRequest, IngestMessageResponse, ProcessingJobStatus, ResolutionLevel

logger = logging.getLogger("queue_manager")

class QueueManager:
    def __init__(self):
        self.queue: queue.Queue = queue.Queue()
        self.dead_letter_queue: List[Dict[str, Any]] = []
        self.active_workers_count: int = 0
        self.total_processed: int = 0
        self.total_failed: int = 0
        self.total_retries: int = 0
        self.latencies_ms: List[float] = []
        self._threads: List[threading.Thread] = []
        self._is_running: bool = False
        self._lock = threading.Lock()

    def start_workers(self):
        """Starts the background worker thread pool if not already running."""
        with self._lock:
            if self._is_running:
                return
            self._is_running = True
            for i in range(settings.WORKER_CONCURRENCY):
                t = threading.Thread(
                    target=self._worker_loop,
                    args=(i + 1,),
                    name=f"support-worker-{i+1}",
                    daemon=True
                )
                t.start()
                self._threads.append(t)
            logger.info(f"Started {settings.WORKER_CONCURRENCY} background queue worker threads.")

    def scale_workers(self, target_concurrency: int):
        """Dynamically scales the worker thread pool up to target_concurrency."""
        with self._lock:
            if not self._is_running:
                self.start_workers()
            current = len(self._threads)
            if target_concurrency > current:
                for i in range(current, target_concurrency):
                    t = threading.Thread(
                        target=self._worker_loop,
                        args=(i + 1,),
                        name=f"support-worker-{i+1}",
                        daemon=True
                    )
                    t.start()
                    self._threads.append(t)
                logger.info(f"Scaled workers from {current} to {len(self._threads)}.")

    def stop_workers(self):
        """Gracefully signals workers to stop."""
        with self._lock:
            self._is_running = False
        # Insert poison pills to wake up waiting workers
        for _ in self._threads:
            self.queue.put(None)
        self._threads.clear()

    def enqueue_message(self, req: IngestMessageRequest) -> IngestMessageResponse:
        """
        Ingests a message idempotently, saves to DB, enqueues background processing job,
        and returns a fast acknowledgement (<50ms).
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        job_id = f"JOB-{req.message_id}"

        # 1. Idempotency Check in DB
        with SessionLocal() as db:
            existing_msg = db.query(MessageRecord).filter_by(message_id=req.message_id).first()
            if existing_msg:
                existing_job = db.query(ProcessingJobRecord).filter_by(message_id=req.message_id).first()
                return IngestMessageResponse(
                    status="duplicate_ignored",
                    message_id=req.message_id,
                    conversation_id=req.conversation_id,
                    job_id=existing_job.job_id if existing_job else job_id,
                    received_at=now_iso
                )

            # Persist Conversation if not exists
            conv = db.query(ConversationRecord).filter_by(conversation_id=req.conversation_id).first()
            if not conv:
                conv = ConversationRecord(
                    conversation_id=req.conversation_id,
                    customer_id=req.customer_id,
                    channel=req.channel,
                    status="active"
                )
                db.add(conv)

            # Persist incoming message
            msg_record = MessageRecord(
                message_id=req.message_id,
                conversation_id=req.conversation_id,
                customer_id=req.customer_id,
                channel=req.channel,
                role="customer",
                content=req.message,
                timestamp=req.timestamp or now_iso,
                processed=False
            )
            db.add(msg_record)

            # Persist Job record
            job_record = ProcessingJobRecord(
                job_id=job_id,
                message_id=req.message_id,
                conversation_id=req.conversation_id,
                status="queued",
                attempts=0,
                enqueued_at=datetime.now(timezone.utc)
            )
            db.add(job_record)
            db.commit()

        # 2. Enqueue into background worker queue
        job_payload = {
            "job_id": job_id,
            "message_id": req.message_id,
            "conversation_id": req.conversation_id,
            "customer_id": req.customer_id,
            "channel": req.channel,
            "message": req.message,
            "attempts": 0,
            "enqueued_time": time.time()
        }
        self.queue.put(job_payload)

        return IngestMessageResponse(
            status="accepted",
            message_id=req.message_id,
            conversation_id=req.conversation_id,
            job_id=job_id,
            received_at=now_iso
        )

    def _worker_loop(self, worker_id: int):
        """Worker consumer loop with retry backoff and dead-letter queue handling."""
        from app.engine import get_support_engine
        engine = get_support_engine()

        while self._is_running:
            try:
                job = self.queue.get(timeout=1.0)
                if job is None:  # Poison pill
                    break

                with self._lock:
                    self.active_workers_count += 1

                start_time = time.time()
                job_id = job["job_id"]
                message_id = job["message_id"]

                # Update job status in DB -> processing
                with SessionLocal() as db:
                    job_rec = db.query(ProcessingJobRecord).filter_by(job_id=job_id).first()
                    if job_rec:
                        job_rec.status = "processing"
                        job_rec.started_at = datetime.now(timezone.utc)
                        job_rec.attempts += 1
                        db.commit()

                try:
                    if settings.EMERGENCY_AUTOMATION_PAUSED:
                        raise RuntimeError("Outbound automation is temporarily paused by operations manager.")

                    # Execute autonomous pipeline
                    is_fast = job.get("fast_mode", False) or str(job.get("message_id", "")).startswith("SIM-")
                    result = engine.process_autonomous_interaction(
                        message=job["message"],
                        channel=job["channel"],
                        customer_id=job["customer_id"],
                        fast_mode=is_fast
                    )

                    duration_ms = (time.time() - start_time) * 1000.0
                    with self._lock:
                        self.latencies_ms.append(duration_ms)
                        if len(self.latencies_ms) > 1000:
                            self.latencies_ms.pop(0)

                    # Persist outcomes in DB
                    with SessionLocal() as db:
                        job_rec = db.query(ProcessingJobRecord).filter_by(job_id=job_id).first()
                        if job_rec:
                            job_rec.status = "completed"
                            job_rec.resolution_level = result.resolution_level.value
                            job_rec.response_text = result.response_text
                            job_rec.auto_dispatched = result.auto_dispatched
                            job_rec.completed_at = datetime.now(timezone.utc)

                        # Update message as processed
                        msg_rec = db.query(MessageRecord).filter_by(message_id=message_id).first()
                        if msg_rec:
                            msg_rec.processed = True

                        # Update conversation
                        conv_rec = db.query(ConversationRecord).filter_by(conversation_id=job["conversation_id"]).first()
                        if conv_rec:
                            conv_rec.status = result.status
                            conv_rec.resolution_level = result.resolution_level.value

                        # If Level 3: Create Escalation Ticket
                        if result.resolution_level == ResolutionLevel.LEVEL_3_ESCALATED:
                            ticket_id = f"TCK-{uuid_short()}"
                            is_urgent = any(w in (result.reason_for_escalation or "").lower() for w in ["leak", "hazard", "flood", "safety"])
                            ticket = TicketRecord(
                                ticket_id=ticket_id,
                                conversation_id=job["conversation_id"],
                                customer_id=job["customer_id"],
                                status="open",
                                priority="urgent" if is_urgent else "normal",
                                category="escalated_support",
                                escalation_reason=result.reason_for_escalation or "Human escalation required",
                                customer_message=job["message"],
                                ai_draft=result.response_text,
                                recommended_action="Contact customer to verify details and arrange service."
                            )
                            db.add(ticket)

                        db.commit()

                    with self._lock:
                        self.total_processed += 1

                except Exception as e:
                    logger.error(f"Worker {worker_id} error processing job {job_id}: {e}")
                    attempts = job.get("attempts", 0) + 1
                    job["attempts"] = attempts

                    if attempts <= settings.MAX_JOB_RETRIES:
                        with self._lock:
                            self.total_retries += 1
                        backoff = 0.1 * (2 ** (attempts - 1))
                        time.sleep(backoff)
                        self.queue.put(job)
                        try:
                            with SessionLocal() as db:
                                job_rec = db.query(ProcessingJobRecord).filter_by(job_id=job_id).first()
                                if job_rec:
                                    job_rec.status = "queued"
                                    job_rec.error_message = f"Retry {attempts}/{settings.MAX_JOB_RETRIES}: {str(e)}"
                                    db.commit()
                        except Exception:
                            pass
                    else:
                        # Exceeded retries -> Dead-Letter Queue
                        with self._lock:
                            self.total_failed += 1
                            self.dead_letter_queue.append({
                                "job": job,
                                "error": str(e),
                                "traceback": traceback.format_exc(),
                                "failed_at": datetime.now(timezone.utc).isoformat()
                            })
                        try:
                            with SessionLocal() as db:
                                job_rec = db.query(ProcessingJobRecord).filter_by(job_id=job_id).first()
                                if job_rec:
                                    job_rec.status = "dead_letter"
                                    job_rec.error_message = f"Dead-lettered after {attempts} attempts: {str(e)}"
                                    job_rec.completed_at = datetime.now(timezone.utc)
                                    db.commit()
                        except Exception:
                            pass

                finally:
                    with self._lock:
                        self.active_workers_count = max(0, self.active_workers_count - 1)
                    self.queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Unexpected worker thread exception: {e}")
                time.sleep(0.1)

    def get_stats(self) -> Dict[str, Any]:
        """Returns real-time queue performance and reliability telemetry."""
        with self._lock:
            avg_lat = sum(self.latencies_ms) / len(self.latencies_ms) if self.latencies_ms else 0.0
            sorted_lats = sorted(self.latencies_ms) if self.latencies_ms else [0.0]
            p95 = sorted_lats[int(len(sorted_lats) * 0.95)] if sorted_lats else 0.0
            p99 = sorted_lats[int(len(sorted_lats) * 0.99)] if sorted_lats else 0.0

            return {
                "queue_depth": self.queue.qsize(),
                "active_workers": self.active_workers_count,
                "configured_concurrency": settings.WORKER_CONCURRENCY,
                "total_processed": self.total_processed,
                "total_failed": self.total_failed,
                "total_retries": self.total_retries,
                "dead_letter_queue_count": len(self.dead_letter_queue),
                "average_latency_ms": round(avg_lat, 2),
                "p95_latency_ms": round(p95, 2),
                "p99_latency_ms": round(p99, 2),
                "automation_paused": settings.EMERGENCY_AUTOMATION_PAUSED
            }

def uuid_short():
    import uuid
    return uuid.uuid4().hex[:8].upper()

_queue_manager_instance = None

def get_queue_manager() -> QueueManager:
    global _queue_manager_instance
    if _queue_manager_instance is None:
        _queue_manager_instance = QueueManager()
    return _queue_manager_instance
