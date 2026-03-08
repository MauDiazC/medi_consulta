from app.modules.notes.signing.utils import canonical_json
from app.modules.notes.signing.utils import sha256_hex
from datetime import datetime, timezone
import os
import hashlib

def build_clinical_snapshot(note, version, professional_info: dict, previous_snapshot_hash: str = None):
    """
    Builds the clinical snapshot including Trust Chain and NOM-004 identity binding.
    """
    # 1) Mandatory SOAP Validation (Structural Integrity)
    soap = {
        "S": version.get("subjective", ""),
        "O": version.get("objective", ""),
        "A": version.get("assessment", ""),
        "P": version.get("plan", ""),
    }
    
    for key, val in soap.items():
        if not val or len(val.strip()) < 2:
            raise ValueError(f"NOM-004 Violation: SOAP section '{key}' is mandatory and cannot be empty.")

    # 2) Identity Binding (Authorship)
    author_identity = {
        "full_name": professional_info.get("full_name"),
        "professional_license": professional_info.get("professional_license"),
        "role": professional_info.get("role"),
    }

    if not author_identity["professional_license"]:
        raise ValueError("NOM-004 Violation: Professional license number is required for signing.")

    # 3) System Clock Hash (Time Integrity)
    # Provides a fingerprint of the system environment at the moment of signing
    clock_seed = f"{datetime.now(timezone.utc).isoformat()}-{os.getpid()}"
    system_clock_hash = hashlib.sha256(clock_seed.encode()).hexdigest()

    payload = {
        "note_id": str(note["id"]),
        "version_id": str(version["id"]),
        "encounter_id": str(note["encounter_id"]),
        "author_id": str(note["created_by"]),
        "author_identity": author_identity,
        "soap": soap,
        "metadata": {
            "schema_version": "1.0-nom004",
            "app_version": "mediconsulta-1.1-compliant",
            "previous_snapshot_hash": previous_snapshot_hash,
            "system_clock_hash": system_clock_hash,
            "signed_at_utc": datetime.now(timezone.utc).isoformat()
        },
    }

    canonical = canonical_json(payload)
    content_hash = sha256_hex(canonical)

    return payload, content_hash