import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'e_banking', 'backend')))

import pytest
import base64
from crypto import CryptoEngine


@pytest.fixture
def engine():
    return CryptoEngine()


SAMPLE_K2 = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
SAMPLE_BP = "123456"
SAMPLE_T = "2026-06-10T00:00:00.000Z"


class TestCryptoEngine:

    def test_tc1_1_encrypt_decrypt_roundtrip(self, engine):
        """TC-1.1: AES-256 CBC encryption followed by decryption returns original"""
        message = "Receiver:Alice|Amt:500"
        f1 = engine.generate_hmac("key_k1", message)
        result = engine.encrypt_data(message, f1, SAMPLE_K2, SAMPLE_BP, SAMPLE_T)

        assert "payload" in result, "Encryption should return a payload"
        assert "iv" in result, "Encryption should return an IV"
        assert isinstance(result["payload"], str), "Payload should be base64 string"
        assert isinstance(result["iv"], str), "IV should be base64 string"

        decrypted = engine.decrypt_data(result["payload"], result["iv"], SAMPLE_K2, SAMPLE_BP, SAMPLE_T)
        assert decrypted is not None, "Decryption should succeed"
        assert decrypted["M"] == message, f"Decrypted message should match original. Got: {decrypted['M']}"
        assert decrypted["F1"] == f1, "Decrypted F1 should match original F1"

    def test_tc1_2_hmac_deterministic(self, engine):
        """TC-1.2: HMAC-SHA256 produces same output for same inputs"""
        message = "Receiver:Bob|Amt:1000"
        key = "test_hmac_key_12345"

        hash1 = engine.generate_hmac(key, message)
        hash2 = engine.generate_hmac(key, message)
        hash3 = engine.generate_hmac(key + "x", message)

        assert hash1 == hash2, "Same inputs should produce same HMAC"
        assert len(hash1) == 64, "SHA256 HMAC should be 64 hex chars"
        assert hash1 != hash3, "Different keys should produce different HMACs"

    def test_tc1_3_key_derivation_deterministic(self, engine):
        """TC-1.3: AES key derivation (K2+Bp+T) is deterministic"""
        key1 = engine._derive_aes_key(SAMPLE_K2, SAMPLE_BP, SAMPLE_T)
        key2 = engine._derive_aes_key(SAMPLE_K2, SAMPLE_BP, SAMPLE_T)

        assert key1 == key2, "Same K2+Bp+T should derive same key"
        assert len(key1) == 32, "Derived AES key should be 32 bytes (256-bit)"

        key_different_t = engine._derive_aes_key(SAMPLE_K2, SAMPLE_BP, SAMPLE_T + "x")
        assert key1 != key_different_t, "Different T should derive different key"

        key_different_k2 = engine._derive_aes_key(SAMPLE_K2 + "x", SAMPLE_BP, SAMPLE_T)
        assert key1 != key_different_k2, "Different K2 should derive different key"

    def test_tc1_4_altered_ciphertext_fails(self, engine):
        """TC-1.4: Modifying one byte of ciphertext causes decryption to fail"""
        message = "Receiver:Charlie|Amt:200"
        f1 = engine.generate_hmac("key_k1", message)
        result = engine.encrypt_data(message, f1, SAMPLE_K2, SAMPLE_BP, SAMPLE_T)

        ct_bytes = base64.b64decode(result["payload"])
        corrupted = bytearray(ct_bytes)
        corrupted[5] ^= 0xFF
        corrupted_payload = base64.b64encode(bytes(corrupted)).decode("utf-8")

        decrypted = engine.decrypt_data(corrupted_payload, result["iv"], SAMPLE_K2, SAMPLE_BP, SAMPLE_T)
        assert decrypted is None, "Decryption of corrupted ciphertext should return None"

    def test_tc1_5_altered_hmac_detected(self, engine):
        """TC-1.5: After decryption, HMAC mismatch between F1 and recomputed F2 is detectable"""
        message = "Receiver:Dave|Amt:300"
        key_k1 = "hmac_key_for_test"
        original_f1 = engine.generate_hmac(key_k1, message)
        tampered_f1 = engine.generate_hmac(key_k1 + "_tampered", message)

        assert original_f1 != tampered_f1, "Tampered HMAC should differ from original"

        recomputed_f2 = engine.generate_hmac(key_k1, message)
        assert original_f1 == recomputed_f2, "Recomputed HMAC with original key should match"
        assert tampered_f1 != recomputed_f2, "Tampered HMAC should NOT match recomputed"

    def test_tc1_6_different_t_produces_different_ciphertext(self, engine):
        """TC-1.6: Same plaintext with different T produces different ciphertext"""
        message = "Receiver:Eve|Amt:400"
        f1 = engine.generate_hmac("key_k1", message)

        result_t1 = engine.encrypt_data(message, f1, SAMPLE_K2, SAMPLE_BP, "2026-01-01T00:00:00Z")
        result_t2 = engine.encrypt_data(message, f1, SAMPLE_K2, SAMPLE_BP, "2026-06-01T00:00:00Z")

        assert result_t1["payload"] != result_t2["payload"], "Different T should produce different ciphertexts"
        assert result_t1["iv"] != result_t2["iv"], "Each encryption should use a random IV"

    def test_tc1_7_password_stretching(self, engine):
        """TC-1.7: PBKDF2 password stretching produces consistent output"""
        password = "securePass123!"
        nid = "NID12345"

        stretched1 = engine.stretch_password(password, nid)
        stretched2 = engine.stretch_password(password, nid)
        stretched_diff_nid = engine.stretch_password(password, "NID99999")

        assert stretched1 == stretched2, "Same password+NID should produce same stretched key"
        assert stretched1 != stretched_diff_nid, "Different NID should produce different stretched key"
        assert len(stretched1) == 64, "PBKDF2-SHA256 output should be 64 hex chars (32 bytes)"

    def test_tc1_8_multiple_decryption_same_key(self, engine):
        """TC-1.8: Multiple encrypt/decrypt cycles with same key all succeed"""
        test_cases = [
            "Receiver:Frank|Amt:50",
            "Receiver:Grace|Amt:9999.99",
            "Receiver:Henry|Amt:0.01",
        ]
        for msg in test_cases:
            f1 = engine.generate_hmac("key_k1", msg)
            result = engine.encrypt_data(msg, f1, SAMPLE_K2, SAMPLE_BP, SAMPLE_T)
            decrypted = engine.decrypt_data(result["payload"], result["iv"], SAMPLE_K2, SAMPLE_BP, SAMPLE_T)
            assert decrypted is not None, f"Decryption should succeed for: {msg}"
            assert decrypted["M"] == msg, f"Roundtrip failed for: {msg}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
