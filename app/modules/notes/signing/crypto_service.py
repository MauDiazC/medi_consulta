from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, utils


def load_private_key(pem_bytes: bytes, password: bytes = None):
    return serialization.load_pem_private_key(pem_bytes, password)

def load_public_key(pem_bytes: bytes):
    return serialization.load_pem_public_key(pem_bytes)

def sign_hash(private_key, hash_hex: str) -> str:
    sig = private_key.sign(
        bytes.fromhex(hash_hex),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        utils.Prehashed(hashes.SHA256()),
    )
    return sig.hex()

def verify_signature(public_key, hash_hex: str, signature_hex: str) -> bool:
    try:
        public_key.verify(
            bytes.fromhex(signature_hex),
            bytes.fromhex(hash_hex),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            utils.Prehashed(hashes.SHA256()),
        )
        return True
    except Exception:
        return False