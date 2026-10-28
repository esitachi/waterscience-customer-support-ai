"""
Packaging Script for WaterScience Customer Support AI Submission.
Ensures strict exclusion of private credentials (.env, API keys), git metadata (.git/),
caches (__pycache__, .pytest_cache), and scratch files.
Validates the actual contents of the created ZIP archive.
"""

import os
import re
import shutil
import zipfile
from pathlib import Path

# Explicit exclusion patterns
EXCLUDE_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode"
}

EXCLUDE_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    ".gitignore",
    "package_submission.py",
    "waterscience-customer-support-ai-submission.zip"
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".zip"
}

API_KEY_PATTERNS = [
    re.compile(r"gsk_[a-zA-Z0-9]{20,}"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}")
]

def create_submission_zip(output_zip_path: str = "waterscience-customer-support-ai.zip"):
    root_dir = Path(".")
    zip_path = Path(output_zip_path)
    parent_zip = Path("..") / output_zip_path
    
    # Remove old/stale zip archives
    for old_zip in [zip_path, parent_zip, Path("waterscience-customer-support-ai-submission.zip")]:
        if old_zip.exists():
            try:
                old_zip.unlink()
                print(f"Removed stale archive: {old_zip}")
            except Exception as e:
                print(f"Warning: could not remove {old_zip}: {e}")
        
    print(f"\nCreating clean submission archive: {output_zip_path}...")
    files_added = []
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(root_dir):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(root_dir)
                
                # Check exclusions
                if file in EXCLUDE_FILES:
                    print(f"  [EXCLUDED] Sensitive / internal file: {rel_path}")
                    continue
                if file_path.suffix in EXCLUDE_EXTENSIONS:
                    continue
                if any(part in EXCLUDE_DIRS for part in rel_path.parts):
                    continue
                if file.startswith("scratch_") or file.endswith(".tmp"):
                    print(f"  [EXCLUDED] Scratch file: {rel_path}")
                    continue
                    
                # Scan text file contents for API key leakage before adding
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    for pat in API_KEY_PATTERNS:
                        if pat.search(content):
                            raise ValueError(f"SECURITY ALERT: Potential API key detected in {rel_path}!")
                except Exception as e:
                    if "SECURITY ALERT" in str(e):
                        raise
                
                zipf.write(file_path, arcname=str(rel_path))
                files_added.append(str(rel_path))
                
    print(f"\nSuccessfully created {output_zip_path} with {len(files_added)} files.")
    
    # Also replicate clean archive to Desktop / parent directory
    try:
        shutil.copy2(zip_path, parent_zip)
        print(f"Copied clean archive to parent directory: {parent_zip}")
    except Exception as e:
        print(f"Notice: could not copy to parent directory ({e})")
    
    # Audit ZIP contents directly from the archive
    print("\nAuditing actual ZIP archive contents:")
    for target in [zip_path, parent_zip]:
        if not target.exists():
            continue
        print(f"Inspecting {target}:")
        with zipfile.ZipFile(target, "r") as zipf:
            namelist = zipf.namelist()
            for n in namelist:
                if n == ".env" or (n.startswith(".env.") and n != ".env.example") or n.endswith("/.env"):
                    raise RuntimeError(f"AUDIT FAILED: Found sensitive env file in {target}: {n}")
                if any(forbidden in n for forbidden in [".git/", ".git\\", "__pycache__", ".pytest_cache"]):
                    raise RuntimeError(f"AUDIT FAILED: Found forbidden content in {target}: {n}")
            print(f"  [OK] No .env, .git, __pycache__, or cache directories found in {target}.")
            print(f"  [OK] All {len(namelist)} packaged files passed static credential scan.")
            print(f"  [OK] Archive size: {round(target.stat().st_size / 1024, 1)} KB")

if __name__ == "__main__":
    create_submission_zip()
