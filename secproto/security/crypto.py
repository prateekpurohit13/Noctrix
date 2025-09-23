import os, base64, json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ALG = "AES-256-GCM"

def generate_dek()->bytes:
    return os.urandom(32)

def encrypt_at_rest(plaintext: bytes, dek: bytes) -> dict:
    aes = AESGCM(dek)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext, None)
    return {"alg": ALG,
            "nonce": base64.b64encode(nonce).decode(),
            "ct": base64.b64encode(ct).decode()}

def decrypt_at_rest(blob: dict, dek: bytes) -> bytes:
    aes = AESGCM(dek)
    nonce = base64.b64decode(blob["nonce"])
    ct = base64.b64decode(blob["ct"])
    return aes.decrypt(nonce, ct, None)
