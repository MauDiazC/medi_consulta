import hashlib
import json
from typing import Any


def canonical_json(data: Any) -> str:
    """
    Serialización determinística para generar hash reproducible.
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_hex(canonical_string: str) -> str:
    return hashlib.sha256(canonical_string.encode("utf-8")).hexdigest()