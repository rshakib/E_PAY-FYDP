"""
Hybrid Transaction Envelope Cryptography (v2)

Implements:
- AES-256-GCM for payload encryption
- AES-256-CBC for PII encryption at rest
- HMAC-SHA256 for lookup hashes (blind indexing)
"""

import base64
import hashlib
import hmac
import json
import os
import secrets

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend


# ============================================
# HybridEnvelopeCrypto: Transaction Envelope
# ============================================

class HybridEnvelopeCrypto:
    """Implements the Hybrid Transaction Envelope (HTE) scheme from the paper:
    - P-256 ECDH for ephemeral-static key exchange
    - HKDF-SHA256 for context-bound session key derivation
    - AES-256-GCM for authenticated payload encryption
    - P-256 ECDSA-SHA256 for device-bound biometric authorization
    """

    # ----------------------------------------------------
    # Paper Specification: P-256 ECDH + HKDF + ECDSA
    # ----------------------------------------------------

    @staticmethod
    def generate_server_ecdh_keypair():
        """Generate long-term NIST P-256 ECDH key pair for the bank server."""
        from cryptography.hazmat.primitives.asymmetric import ec
        private_key = ec.generate_private_key(ec.SECP256R1(), backend=default_backend())
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

        # Also get uncompressed point hex (04 || X || Y) for simple transport
        public_point_hex = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        ).hex()

        return private_pem, public_pem, public_point_hex

    @staticmethod
    def load_server_ecdh_private_key(private_key_pem: str):
        """Loads P-256 EC private key from PEM string."""
        return serialization.load_pem_private_key(
            private_key_pem.encode(), password=None, backend=default_backend()
        )

    @staticmethod
    def load_ec_public_key(pub_key_str: str):
        """Loads P-256 EC public key from PEM string or uncompressed hex string."""
        from cryptography.hazmat.primitives.asymmetric import ec
        pub_key_str = pub_key_str.strip()
        if pub_key_str.startswith('-----BEGIN'):
            return serialization.load_pem_public_key(pub_key_str.encode(), backend=default_backend())
        else:
            pub_bytes = bytes.fromhex(pub_key_str)
            return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), pub_bytes)

    @staticmethod
    def derive_hte_session_key(server_private_key, ephemeral_pub_hex: str, aad: dict, key_id: str, shared_z: bytes = None) -> bytes:
        """Derive transaction-specific AES-256 key KT according to paper equations (2)-(6):
        Z = ECDH(SK_B^dh, ePK)
        salt = H(HTE-v1-salt || S || TxID || N)
        info = HTE-v1/AES-256-GCM || T || ePK || KeyID
        KT = HKDF-Expand(HKDF-Extract(salt, Z), info, 32)

        `shared_z` is the Mode B (HSM) path: when the receiver's ECDH private key
        lives inside AWS KMS, Z is computed by KMS and passed in here, so this
        process never needs the private key. When omitted, Z is computed locally
        from `server_private_key` (Vault/DB software key).
        """
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF

        # Ephemeral public key
        eph_pub_bytes = bytes.fromhex(ephemeral_pub_hex)

        # 1. Z = ECDH(SK_B^dh, ePK)  — from the HSM when supplied, else locally.
        if shared_z is None:
            if server_private_key is None:
                raise ValueError("derive_hte_session_key requires server_private_key or shared_z")
            eph_pub_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), eph_pub_bytes)
            shared_z = server_private_key.exchange(ec.ECDH(), eph_pub_key)

        # 2. salt = SHA256(HTE-v1-salt || S || TxID || N)
        salt_data = ('HTE-v1-salt' + str(aad.get('S', '')) + str(aad.get('TxID', '')) + str(aad.get('N', ''))).encode('utf-8')
        salt = hashlib.sha256(salt_data).digest()

        # 3. info = HTE-v1/AES-256-GCM || T || ePK || KeyID
        info = ('HTE-v1/AES-256-GCM' + str(aad.get('T', ''))).encode('utf-8') + eph_pub_bytes + str(key_id).encode('utf-8')

        # 4. KT = HKDF-Expand(PRK, info, 32)
        hkdf_inst = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=info,
            backend=default_backend()
        )
        return hkdf_inst.derive(shared_z)

    @staticmethod
    def decrypt_hte_payload(ciphertext_hex: str, iv_hex: str, tag_hex: str, aad_bytes: bytes, session_key: bytes) -> dict:
        """Decrypt AES-256-GCM payload with authenticated associated data (AAD)."""
        c_bytes = bytes.fromhex(ciphertext_hex)
        iv_bytes = bytes.fromhex(iv_hex)
        tag_bytes = bytes.fromhex(tag_hex)

        aesgcm = AESGCM(session_key)
        # cryptography AESGCM expects ciphertext + 16-byte tag
        plaintext_bytes = aesgcm.decrypt(iv_bytes, c_bytes + tag_bytes, aad_bytes)
        return json.loads(plaintext_bytes.decode('utf-8'))

    @staticmethod
    def verify_hte_signature(canonical_bytes: bytes, sig_hex: str, user_ecdsa_pub_str: str) -> bool:
        """Verify biometric-authorized ECDSA P-256 signature over the canonical envelope.
        Supports both 64-byte raw (r || s) signature and DER-encoded signature.
        """
        from cryptography.hazmat.primitives.asymmetric import ec, utils
        try:
            pub_key = HybridEnvelopeCrypto.load_ec_public_key(user_ecdsa_pub_str)
            sig_bytes = bytes.fromhex(sig_hex)

            if len(sig_bytes) == 64:
                # Raw r || s (from WebCrypto / Noble / Android Keystore)
                r = int.from_bytes(sig_bytes[:32], 'big')
                s = int.from_bytes(sig_bytes[32:], 'big')
                der_sig = utils.encode_dss_signature(r, s)
            else:
                # Already DER formatted
                der_sig = sig_bytes

            pub_key.verify(der_sig, canonical_bytes, ec.ECDSA(hashes.SHA256()))
            return True
        except Exception as e:
            print(f"[CRYPTO V2] ECDSA signature verification failed: {e}", flush=True)
            return False

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
