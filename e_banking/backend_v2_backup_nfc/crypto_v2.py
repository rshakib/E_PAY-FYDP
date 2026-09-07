"""
Hybrid Transaction Envelope Cryptography (v2)

Implements:
- AES-256-GCM for payload encryption
- RSA-OAEP for session key encapsulation
- RSA-PSS for envelope signing
- AES-256-CBC for PII encryption at rest
- HMAC-SHA256 for lookup hashes (blind indexing)
"""

import base64
import hashlib
import hmac
import json
import os
import secrets

from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend


# ============================================
# HybridEnvelopeCrypto: Transaction Envelope
# ============================================

class HybridEnvelopeCrypto:
    """Implements the Hybrid Transaction Envelope scheme from the paper."""

    @staticmethod
    def generate_server_rsa_keypair():
        """Generate RSA-2048 key pair for the server."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        return private_pem, public_pem

    @staticmethod
    def decrypt_session_key(encrypted_key_b64: str, private_key_pem: str) -> bytes:
        """Decrypt the AES session key using RSA-OAEP."""
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(), password=None, backend=default_backend()
        )
        encrypted_key = base64.b64decode(encrypted_key_b64)
        session_key = private_key.decrypt(
            encrypted_key,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return session_key

    @staticmethod
    def decrypt_payload(ciphertext_b64: str, nonce_b64: str, session_key: bytes) -> dict:
        """Decrypt AES-256-GCM payload."""
        ciphertext = base64.b64decode(ciphertext_b64)
        nonce = base64.b64decode(nonce_b64)
        aesgcm = AESGCM(session_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return json.loads(plaintext.decode())

    @staticmethod
    def verify_signature(message: bytes, signature_b64: str, public_key_pem: str) -> bool:
        """Verify RSA-PSS signature."""
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(), backend=default_backend()
            )
            signature = base64.b64decode(signature_b64)
            public_key.verify(
                signature,
                message,
                asym_padding.PSS(
                    mgf=asym_padding.MGF1(hashes.SHA256()),
                    salt_length=asym_padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except Exception as e:
            print(f"[CRYPTO V2] Signature verification failed: {e}")
            return False

    @staticmethod
    def encrypt_payload(payload_dict: dict, session_key: bytes) -> tuple:
        """Encrypt payload with AES-256-GCM. Returns (ciphertext_b64, nonce_b64)."""
        plaintext = json.dumps(payload_dict).encode()
        nonce = secrets.token_bytes(12)  # 96-bit nonce
        aesgcm = AESGCM(session_key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return base64.b64encode(ciphertext).decode(), base64.b64encode(nonce).decode()

    @staticmethod
    def encrypt_session_key(session_key: bytes, public_key_pem: str) -> str:
        """Encrypt the AES session key using RSA-OAEP with server's public key."""
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode(), backend=default_backend()
        )
        encrypted = public_key.encrypt(
            session_key,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return base64.b64encode(encrypted).decode()


# ============================================
# PIIEncryption: Encrypt PII at rest
# ============================================

class PIIEncryption:
    """AES-256-CBC encryption for PII fields (name, mobile, NID, email)."""

    def __init__(self, encryption_key_hex: str):
        if not encryption_key_hex or len(encryption_key_hex) < 64:
            raise ValueError("PII_ENCRYPTION_KEY must be a 64-char hex string (32 bytes)")
        self.key = bytes.fromhex(encryption_key_hex[:64])

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string, returns base64-encoded ciphertext with IV prepended."""
        if not plaintext:
            return ''
        iv = secrets.token_bytes(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # PKCS7 padding
        pad_len = 16 - (len(plaintext.encode()) % 16)
        padded = plaintext.encode() + bytes([pad_len] * pad_len)

        ciphertext = encryptor.update(padded) + encryptor.finalize()
        # Prepend IV to ciphertext
        return base64.b64encode(iv + ciphertext).decode()

    def decrypt(self, encrypted_b64: str) -> str:
        """Decrypt a base64-encoded ciphertext (with IV prepended)."""
        if not encrypted_b64:
            return ''
        raw = base64.b64decode(encrypted_b64)
        iv = raw[:16]
        ciphertext = raw[16:]

        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()

        # Remove PKCS7 padding
        pad_len = padded[-1]
        return padded[:-pad_len].decode()


# ============================================
# LookupHash: HMAC-based blind indexing
# ============================================

class LookupHash:
    """HMAC-SHA256 for generating lookup hashes (mobile, NID uniqueness checks)."""

    def __init__(self, pepper_hex: str):
        if not pepper_hex or len(pepper_hex) < 64:
            raise ValueError("PII_HMAC_PEPPER must be a 64-char hex string (32 bytes)")
        self.pepper = bytes.fromhex(pepper_hex[:64])

    def compute(self, value: str) -> str:
        """Compute HMAC-SHA256 hash for lookup."""
        if not value:
            return ''
        return hmac.new(self.pepper, value.encode(), hashlib.sha256).hexdigest()
