import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'e_banking', 'backend')))

import base64, json, urllib3
import requests
from crypto import CryptoEngine

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BACKEND_URL = "https://localhost:5001"


class BackendClient:
    def __init__(self):
        self.crypto = CryptoEngine()
        self.session = requests.Session()
        self.session.verify = False

    def health(self):
        return self.session.get(f"{BACKEND_URL}/health")

    def register(self, username, password, nid="NID12345", activation_code="ACT123", bp="123456"):
        return self.session.post(f"{BACKEND_URL}/register", json={
            "username": username, "password": password, "nid": nid,
            "activationCode": activation_code, "bp": bp
        })

    def login(self, username, password):
        return self.session.post(f"{BACKEND_URL}/login", json={
            "username": username, "password": password
        })

    def transfer(self, username, payload, iv, token):
        return self.session.post(f"{BACKEND_URL}/transfer", json={
            "username": username, "payload": payload, "iv": iv
        }, headers={"Authorization": f"Bearer {token}"})

    def get_user(self, username, token):
        return self.session.get(f"{BACKEND_URL}/user/{username}", headers={"Authorization": f"Bearer {token}"})

    def get_transactions(self, username, token):
        return self.session.get(f"{BACKEND_URL}/transactions/{username}", headers={"Authorization": f"Bearer {token}"})

    def get_notifications(self, username, token):
        return self.session.get(f"{BACKEND_URL}/notifications/{username}", headers={"Authorization": f"Bearer {token}"})

    def check_receiver(self, username, token):
        return self.session.get(f"{BACKEND_URL}/check-receiver/{username}", headers={"Authorization": f"Bearer {token}"})


def encrypt_transfer_payload(crypto, k2, bp, t, receiver, amount, k1=None):
    message = f"Receiver:{receiver}|Amt:{amount}"
    f1 = crypto.generate_hmac(k1 or "test_k1_override", message)
    encrypted = crypto.encrypt_data(message, f1, k2, bp, t)
    return encrypted["payload"], encrypted["iv"], message, f1
