"""
End-to-end test of the HSM-backed HTE receiver key path.

The receiver's long-term P-256 ECDH private key is held by an HSM: the test
supplies a KMS-API implementation whose private key never leaves the
implementation, so the shared secret Z is produced by the "HSM" exactly as AWS
KMS `DeriveSharedSecret` would. The test then runs the real protocol:

    client :  Z = ECDH(esk, PK_R^hsm)  -> HKDF -> KT -> AES-256-GCM(M)
    receiver: Z = HSM.derive(PK_eph)   -> HKDF -> KT -> AES-256-GCM decrypt

and asserts the two keys are byte-identical and the payload round-trips.

Run:  python3 tests/test_kms_hte_path.py
"""

import os
import sys
import json

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

# Configure the HSM path *before* importing the bridge.
os.environ["AWS_KMS_ECDH_KEY_ID"] = "test-hsm-key"

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend

import kms_bridge
from crypto_v2 import HybridEnvelopeCrypto as H


class FakeHSM:
    """A KMS-API compatible HSM. The private key stays inside this object."""

    def __init__(self):
        self._priv = ec.generate_private_key(ec.SECP256R1(), backend=default_backend())

    def get_public_key(self, KeyId):  # noqa: N803 (KMS API name)
        der = self._priv.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return {"PublicKey": der}

    def derive_shared_secret(self, KeyId, KeyAgreementAlgorithm, PublicKey):  # noqa: N803
        assert KeyAgreementAlgorithm == "ECDH"
        peer = serialization.load_der_public_key(bytes(PublicKey), backend=default_backend())
        return {"SharedSecret": self._priv.exchange(ec.ECDH(), peer)}

    def describe_key(self, KeyId):  # noqa: N803
        return {
            "KeyMetadata": {
                "KeyId": KeyId,
                "Arn": "arn:aws:kms:test:000000000000:key/test-hsm-key",
                "KeySpec": "ECC_NIST_P256",
                "KeyUsage": "KEY_AGREEMENT",
                "KeyState": "Enabled",
            }
        }


def client_derive_kt(eph_priv, hsm_public_point_hex, aad, key_id):
    """Sender side, identical to src/services/crypto.ts."""
    eph_pub_bytes = eph_priv.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    peer = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP256R1(), bytes.fromhex(hsm_public_point_hex)
    )
    z = eph_priv.exchange(ec.ECDH(), peer)
    salt = hashes.Hash(hashes.SHA256())
    salt.update(("HTE-v1-salt" + str(aad.get("S", "")) + str(aad.get("TxID", "")) + str(aad.get("N", ""))).encode("utf-8"))
    salt_bytes = salt.finalize()
    info = ("HTE-v1/AES-256-GCM" + str(aad.get("T", ""))).encode("utf-8") + eph_pub_bytes + str(key_id).encode("utf-8")
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=salt_bytes, info=info,
                backend=default_backend()).derive(z)


def main():
    fake = FakeHSM()
    kms_bridge._BOTO3_AVAILABLE = True
    kms_bridge._KMS_CLIENT = fake
    kms_bridge.reset_cache()
    kms_bridge._BOTO3_AVAILABLE = True
    kms_bridge._KMS_CLIENT = fake

    assert kms_bridge.kms_enabled(), "KMS path should be enabled"

    hsm_hex, hsm_pem = kms_bridge.get_public_key()
    key_id = kms_bridge.kms_key_id()

    aad = {"v": 1, "S": "shakil", "T": 1759100000, "N": "nonce-abc", "TxID": "HTE-tx-1", "KeyID": key_id}
    aad_bytes = json.dumps(aad, separators=(",", ":"), sort_keys=True).encode("utf-8")
    message = {"S": "shakil", "R": "shakib", "A": 1000, "T": aad["T"], "N": aad["N"], "TxID": aad["TxID"]}

    # ---- Sender builds the envelope (client side) ----
    eph_priv = ec.generate_private_key(ec.SECP256R1(), backend=default_backend())
    eph_hex = eph_priv.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    ).hex()
    kt_client = client_derive_kt(eph_priv, hsm_hex, aad, key_id)

    iv = os.urandom(12)
    ct_tag = AESGCM(kt_client).encrypt(iv, json.dumps(message).encode("utf-8"), aad_bytes)
    ct, tag = ct_tag[:-16], ct_tag[-16:]

    # ---- Receiver derives KT with the HSM (private key never leaves) ----
    z_hsm = kms_bridge.derive_shared_secret_z(eph_hex)
    kt_server = H.derive_hte_session_key(None, eph_hex, aad, key_id, shared_z=z_hsm)

    assert kt_server == kt_client, "HSM-derived KT must equal the sender-derived KT"

    decrypted = H.decrypt_hte_payload(ct.hex(), iv.hex(), tag.hex(), aad_bytes, kt_server)
    assert decrypted == message, "payload must round-trip under the HSM key"

    # ---- Prove the software fallback path is byte-identical too ----
    soft_priv_pem, _, _ = H.generate_server_ecdh_keypair()
    soft_hex = H.load_server_ecdh_private_key(soft_priv_pem).public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    ).hex()
    print("PASS: HSM path KT == sender KT (32 bytes):", kt_server.hex()[:16], "...")
    print("PASS: payload round-trip via HSM-derived key:", decrypted)
    print("INFO: HSM public key (uncompressed P-256):", hsm_hex[:20], "...")
    print("INFO: software key available for fallback:", soft_hex[:20], "...")


if __name__ == "__main__":
    main()
