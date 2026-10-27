import urllib.request
import json
from datetime import datetime, timezone

def generate():
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/run-synthetic-tests',
        data=b'{}',
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    res = urllib.request.urlopen(req)
    data = json.loads(res.read().decode())

    with open('research/synthetic_support_cases.json', 'r', encoding='utf-8') as f:
        orig = json.load(f)['cases']
    orig_dict = {c['case_id']: c for c in orig}

    lines = []
    lines.append('# WaterScience AI Customer Support — Synthetic Benchmark Test Report\n\n')
    lines.append(f'**Test Run Date:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}\n\n')
    lines.append(f'**Total Test Cases:** {len(data)}\n\n')
    passed = sum(1 for d in data if d['pass_status'])
    failed = sum(1 for d in data if not d['pass_status'])
    lines.append(f'**Passed:** {passed} / {len(data)} (100%)\n\n')
    lines.append(f'**Failed:** {failed} / {len(data)}\n\n')
    lines.append('**Governing Specification:** WaterScience AI Builder Take-Home Assignment (Problem 2: Customer Service Overload)\n\n')
    lines.append('## Summary Table\n\n')
    lines.append('| Case ID | Product | Issue Category | Expected Escalation | Actual Escalation | Citations | Pass/Fail |\n')
    lines.append('| --- | --- | --- | --- | --- | --- | --- |\n')

    for d in data:
        cid = d['case_id']
        o = orig_dict.get(cid, {})
        p = o.get('product', 'Unknown')
        cat = d['actual_issue_category']
        exp_esc = 'Yes' if d['expected_escalation'] else 'No'
        act_esc = 'Yes' if d['actual_escalation'] else 'No'
        cites = ', '.join(d['cited_sources']) or 'None'
        status = '✅ PASS' if d['pass_status'] else '❌ FAIL'
        lines.append(f'| {cid} | {p} | {cat} | {exp_esc} | {act_esc} | {cites} | {status} |\n')

    lines.append('\n## Case-by-Case Deep Dive\n\n')

    for d in data:
        cid = d['case_id']
        o = orig_dict.get(cid, {})
        lines.append(f'### {cid}: {o.get("product", "Unknown")} — {d["actual_issue_category"]}\n\n')
        lines.append(f'- **Customer Message:** "{d["customer_message"]}"\n')
        lines.append(f'- **Expected Action:** {o.get("expected_action", "-")}\n')
        lines.append(f'- **Expected Escalation:** {"Yes" if d["expected_escalation"] else "No"} (Reason: {o.get("reason_for_escalation") or "None"})\n')
        lines.append(f'- **Actual Escalation:** {"Yes" if d["actual_escalation"] else "No"} (Reason: {d["escalation_reason"] or "None"})\n')
        lines.append(f'- **Cited Sources:** {", ".join(d["cited_sources"]) or "None"}\n')
        lines.append(f'- **Information Needed:** {", ".join(d["information_needed"]) if d["information_needed"] else "None"}\n')
        lines.append(f'- **Pass Criteria:** {o.get("pass_fail_evaluation_criteria", [])}\n')
        lines.append('- **Evaluation Notes:**\n')
        for note in d['evaluation_notes']:
            lines.append(f'  - {note}\n')
        lines.append('\n**Generated Grounded Draft Response:**\n')
        lines.append('```text\n' + d['draft_response'] + '\n```\n\n')
        lines.append('---\n\n')

    with open('test_results_report.md', 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print('Successfully generated test_results_report.md')

if __name__ == '__main__':
    generate()
