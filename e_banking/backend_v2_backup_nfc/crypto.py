import base64
import binascii
import hashlib
import hmac
import json

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class CryptoEngine:
    def __init__(self):
        self.block_size = 16

    def generate_hmac(self, key_k1, message):
        """Generate F1/F2 from message M and key K1."""
        byte_key = key_k1.encode("utf-8")
        byte_message = message.encode("utf-8")
        h = hmac.new(byte_key, byte_message, hashlib.sha256)
        return h.hexdigest()

    def stretch_password(self, password, nid):
        """Stretch password with PBKDF2-SHA256 using NID as salt."""
        salt = nid.encode("utf-8")
        iterations = 100000
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return binascii.hexlify(dk).decode("utf-8")

    def _derive_aes_key(self, password_k2, fingerprint_bp, last_t):
        """Derive a 32-byte AES key from K2, BP, and T using HMAC-SHA256."""
        # Fingerprint input is intentionally fixed to match the protocol.
        fixed_bp = hashlib.sha256(b"123456").hexdigest()
        message = f"{fixed_bp}{last_t}"
        byte_key = password_k2.encode("utf-8")
        byte_message = message.encode("utf-8")
        h = hmac.new(byte_key, byte_message, hashlib.sha256)
        return h.digest()

    def encrypt_data(self, message, f1, k2, bp, t):
        """Encrypt M + F1 with AES-CBC using K2, BP, and T."""
        combined_data = f"{message}|{f1}"
        key = self._derive_aes_key(k2, bp, t)

        cipher = AES.new(key, AES.MODE_CBC)
        iv = cipher.iv

        ct_bytes = cipher.encrypt(pad(combined_data.encode("utf-8"), self.block_size))

        return {
            "payload": base64.b64encode(ct_bytes).decode("utf-8"),
            "iv": base64.b64encode(iv).decode("utf-8"),
        }

    def decrypt_data(self, encrypted_payload_base64, iv_base64, k2, bp, t):
        """Decrypt ciphertext and recover M and F1."""
        try:
            ct = base64.b64decode(encrypted_payload_base64)
            iv = base64.b64decode(iv_base64)
            key = self._derive_aes_key(k2, bp, t)

            cipher = AES.new(key, AES.MODE_CBC, iv)
            pt_bytes = unpad(cipher.decrypt(ct), self.block_size)

            decrypted_string = pt_bytes.decode("utf-8")
            parts = decrypted_string.split("|")
            if len(parts) < 2:
                return None

            f1 = parts.pop()
            m = "|".join(parts)

            return {"M": m, "F1": f1}
        except Exception as e:
            print(f"Decryption error: {e}")
            return None

    def decrypt_outer_envelope(self, envelope_dict: dict, secret_key: str) -> dict:
        """Decrypt the outer secure envelope sent by apiClient.postSecure."""
        try:
            payload = envelope_dict.get("payload")
            hmac_val = envelope_dict.get("hmac")
            nonce = envelope_dict.get("nonce")
            timestamp = envelope_dict.get("timestamp")

            if not all([payload, hmac_val, nonce, timestamp is not None]):
                print("Missing envelope parameters")
                return None

            integrity_str = f"{payload}|{timestamp}|{nonce}"
            byte_key = secret_key.encode("utf-8")
            byte_message = integrity_str.encode("utf-8")
            h = hmac.new(byte_key, byte_message, hashlib.sha256)
            expected_hmac = h.hexdigest()

            if not hmac.compare_digest(expected_hmac, hmac_val):
                print("Outer envelope HMAC mismatch")
                return None

            iv_b64, ct_b64 = payload.split(":")
            iv = base64.b64decode(iv_b64)
            ct = base64.b64decode(ct_b64)
            key = secret_key[:32].encode("utf-8")

            cipher = AES.new(key, AES.MODE_CBC, iv)
            pt_bytes = unpad(cipher.decrypt(ct), self.block_size)
            decrypted_str = pt_bytes.decode("utf-8")

            return json.loads(decrypted_str)
        except Exception as e:
            print(f"Outer envelope decryption failed: {e}")
            return None

    def encrypt_outer_envelope(self, data_dict: dict, secret_key: str) -> dict:
        """Encrypt response data in the outer secure envelope format."""
        try:
            data_str = json.dumps(data_dict)
            key = secret_key[:32].encode("utf-8")
            cipher = AES.new(key, AES.MODE_CBC)
            iv = cipher.iv

            ct_bytes = cipher.encrypt(pad(data_str.encode("utf-8"), self.block_size))
            iv_b64 = base64.b64encode(iv).decode("utf-8")
            ct_b64 = base64.b64encode(ct_bytes).decode("utf-8")
            payload = f"{iv_b64}:{ct_b64}"

            byte_key = secret_key.encode("utf-8")
            byte_message = payload.encode("utf-8")
            h = hmac.new(byte_key, byte_message, hashlib.sha256)
            generated_hmac = h.hexdigest()

            return {
                "payload": payload,
                "hmac": generated_hmac,
            }
        except Exception as e:
            print(f"Outer envelope encryption failed: {e}")
            return None
