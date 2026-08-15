import base64
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def canonical_payload(action: str, payload: dict) -> bytes:
    return json.dumps(
        {"action": action, **payload},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def verify_signature(public_key: str, action: str, payload: dict, signature: str) -> bool:
    try:
        key = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key, validate=True))
        key.verify(base64.b64decode(signature, validate=True), canonical_payload(action, payload))
    except (InvalidSignature, TypeError, ValueError):
        return False
    return True
