from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os, base64, json

class EncryptedMappingStore:
    def __init__(self, key:bytes):
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256-GCM")
        self.key = key
        self.aesgcm = AESGCM(self.key)

    def encrypt_mapping(self, mapping:dict) -> str:
        nonce = os.urandom(12)
        ct = self.aesgcm.encrypt(nonce, json.dumps(mapping).encode(), None)
        return base64.b64encode(nonce+ct).decode()

    def decrypt_mapping(self, token:str) -> dict:
        data = base64.b64decode(token)
        nonce, ct = data[:12], data[12:]
        pt = self.aesgcm.decrypt(nonce, ct, None)
        return json.loads(pt.decode())
