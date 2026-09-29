"""
AWS KMS bridge for the Hybrid Transaction Envelope (HTE) receiver key.

Paper §2: "the private key is intended to reside in an HSM or equivalent
isolated service."  When AWS KMS is configured, the receiver's long-term P-256
ECDH private key never leaves the HSM: the paper's step (2)

    Z = ECDH(SK_R^dh, ePK)

is computed inside KMS via `DeriveSharedSecret`, and this process only ever sees
the resulting shared secret Z.  `get_public_key` supplies the public half for the
`/server-public-key` endpoint.

This is Mode B (HSM-bound ECDH).  The device signing key stays on the phone in
Android StrongBox — it can never live in a server-side HSM.

Configuration (all optional; when absent the caller falls back to the existing
Vault/DB software key, so nothing breaks):

    AWS_KMS_ECDH_KEY_ID     KMS key ARN/ID, spec ECC_NIST_P256, usage KEY_AGREEMENT
    AWS_KMS_REGION          e.g. ap-south-1   (or AWS_DEFAULT_REGION)
    AWS_ACCESS_KEY_ID       credentials (or an instance/task role — boto3 auto-discovers)
    AWS_SECRET_ACCESS_KEY
    AWS_SESSION_TOKEN       optional (temporary creds)

Required IAM permissions: kms:DeriveSharedSecret, kms:GetPublicKey, kms:DescribeKey
"""

import os
import threading

try:
    import boto3
    from botocore.config import Config as _BotoConfig
    _BOTO3_AVAILABLE = True
except Exception:  # boto3 not installed -> KMS simply disabled
    boto3 = None
    _BotoConfig = None
    _BOTO3_AVAILABLE = False

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend


_KMS_LOCK = threading.Lock()
_KMS_CLIENT = None
_PUBLIC_KEY_CACHE = {"hex": None, "pem": None}


def kms_key_id():
    """The configured KMS ECDH key id/ARN, or '' when KMS is not configured."""
    return (
        os.environ.get("AWS_KMS_ECDH_KEY_ID")
        or os.environ.get("AWS_KMS_KEY_ID")
        or ""
    ).strip()


def kms_enabled():
    """True only when boto3 is importable AND a KMS key id is configured."""
    return bool(_BOTO3_AVAILABLE and kms_key_id())


def _region():
    return (
        os.environ.get("AWS_KMS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or os.environ.get("AWS_REGION")
        or "us-east-1"
    )


def _get_client():
    """Lazily create (and memoize) a boto3 KMS client."""
    global _KMS_CLIENT
    if _KMS_CLIENT is not None:
        return _KMS_CLIENT
    with _KMS_LOCK:
        if _KMS_CLIENT is None:
            if not _BOTO3_AVAILABLE:
                raise RuntimeError("boto3 is not installed; cannot use AWS KMS")
            cfg = _BotoConfig(retries={"max_attempts": 4, "mode": "standard"})
            _KMS_CLIENT = boto3.client("kms", region_name=_region(), config=cfg)
        return _KMS_CLIENT


def _to_spki_der(public_key_hex: str) -> bytes:
    """Uncompressed P-256 point hex (04||X||Y) -> DER SubjectPublicKeyInfo."""
    point = bytes.fromhex(public_key_hex.strip())
    pub = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), point)
    return pub.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def derive_shared_secret_z(ephemeral_pub_hex: str) -> bytes:
    """Mode B: compute Z = ECDH(SK_R^dh, ePK) entirely inside AWS KMS.

    The receiver private key never leaves the HSM. Returns the raw 32-byte
    shared secret (the P-256 x-coordinate), matching
    `private_key.exchange(ec.ECDH(), eph_pub_key)` byte-for-byte.
    """
    client = _get_client()
    resp = client.derive_shared_secret(
        KeyId=kms_key_id(),
        KeyAgreementAlgorithm="ECDH",
        PublicKey=_to_spki_der(ephemeral_pub_hex),
    )
    secret = resp.get("SharedSecret")
    if not secret:
        raise RuntimeError("AWS KMS returned an empty shared secret")
    return bytes(secret)


def get_public_key():
    """Fetch the KMS key's public half as (uncompressed_point_hex, pem).

    Cached after the first successful call so the `/server-public-key` endpoint
    does not hit KMS on every request.
    """
    if _PUBLIC_KEY_CACHE["hex"] and _PUBLIC_KEY_CACHE["pem"]:
        return _PUBLIC_KEY_CACHE["hex"], _PUBLIC_KEY_CACHE["pem"]

    client = _get_client()
    resp = client.get_public_key(KeyId=kms_key_id())
    der = resp.get("PublicKey")
    if not der:
        raise RuntimeError("AWS KMS returned no public key")

    pub = serialization.load_der_public_key(bytes(der), backend=default_backend())
    point_hex = pub.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    ).hex()
    pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    _PUBLIC_KEY_CACHE["hex"] = point_hex
    _PUBLIC_KEY_CACHE["pem"] = pem
    return point_hex, pem


def describe_key():
    """Return basic KMS key metadata (for a startup log line)."""
    client = _get_client()
    meta = client.describe_key(KeyId=kms_key_id())["KeyMetadata"]
    return {
        "key_id": meta.get("KeyId"),
        "arn": meta.get("Arn"),
        "spec": meta.get("KeySpec"),
        "usage": meta.get("KeyUsage"),
        "state": meta.get("KeyState"),
    }


def reset_cache():
    """Clear the memoized client + public key (useful for tests / key rotation)."""
    global _KMS_CLIENT
    with _KMS_LOCK:
        _KMS_CLIENT = None
        _PUBLIC_KEY_CACHE["hex"] = None
        _PUBLIC_KEY_CACHE["pem"] = None
