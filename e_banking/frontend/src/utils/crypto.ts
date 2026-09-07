// Frontend crypto utility to match backend crypto.py
import CryptoJS from 'crypto-js';

export interface EncryptedPayload {
  payload: string;
  iv: string;
}

export interface OuterEnvelope {
  payload: string;
  hmac: string;
}

export class FrontendCryptoEngine {
  generateHmac(keyK1: string, message: string): string {
    return CryptoJS.HmacSHA256(message, keyK1).toString();
  }

  stretchPassword(password: string, nid: string): string {
    const salt = CryptoJS.enc.Utf8.parse(nid);
    const key = CryptoJS.PBKDF2(password, salt, {
      keySize: 256 / 32,
      iterations: 100000,
      hasher: CryptoJS.algo.SHA256,
    });
    return key.toString(CryptoJS.enc.Hex);
  }

  private deriveAesKey(k2: string, _bp: string, t: string): CryptoJS.lib.WordArray {
    const fixedBp = CryptoJS.SHA256('123456').toString(CryptoJS.enc.Hex);
    const message = `${fixedBp}${t}`;
    return CryptoJS.HmacSHA256(message, k2);
  }

  encryptData(message: string, f1: string, k2: string, bp: string, t: string): EncryptedPayload {
    try {
      const combinedData = `${message}|${f1}`;
      const key = this.deriveAesKey(k2, bp, t);
      const iv = CryptoJS.lib.WordArray.random(128 / 8);

      const encrypted = CryptoJS.AES.encrypt(combinedData, key, {
        mode: CryptoJS.mode.CBC,
        iv,
        padding: CryptoJS.pad.Pkcs7,
      });

      return {
        payload: CryptoJS.enc.Base64.stringify(encrypted.ciphertext),
        iv: CryptoJS.enc.Base64.stringify(iv),
      };
    } catch (error) {
      console.error('Encryption error details:', {
        message,
        f1Length: f1.length,
        k2Length: k2.length,
        bpLength: bp.length,
        tLength: t.length,
        error,
      });
      throw error;
    }
  }

  decryptData(
    encryptedPayload: string,
    ivBase64: string,
    k2: string,
    bp: string,
    t: string
  ): { M: string; F1: string } | null {
    try {
      const key = this.deriveAesKey(k2, bp, t);
      const ciphertext = CryptoJS.enc.Base64.parse(encryptedPayload);
      const iv = CryptoJS.enc.Base64.parse(ivBase64);
      const cipherParams = CryptoJS.lib.CipherParams.create({ ciphertext });

      const decrypted = CryptoJS.AES.decrypt(cipherParams, key, {
        mode: CryptoJS.mode.CBC,
        iv,
        padding: CryptoJS.pad.Pkcs7,
      });

      const decryptedString = decrypted.toString(CryptoJS.enc.Utf8);
      const parts = decryptedString.split('|');
      if (parts.length < 2) {
        return null;
      }

      const f1 = parts.pop() || '';
      const m = parts.join('|');
      return { M: m, F1: f1 };
    } catch (error) {
      console.error('Decryption error:', error);
      return null;
    }
  }

  decryptOuterEnvelope(envelope: Record<string, unknown>, secretKey: string): Record<string, unknown> | null {
    try {
      const payload = envelope.payload;
      const hmacVal = envelope.hmac;
      const nonce = envelope.nonce;
      const timestamp = envelope.timestamp;

      if (
        typeof payload !== 'string' ||
        typeof hmacVal !== 'string' ||
        typeof nonce !== 'string' ||
        timestamp === undefined ||
        timestamp === null
      ) {
        console.error('Missing envelope parameters');
        return null;
      }

      const integrityStr = `${payload}|${timestamp}|${nonce}`;
      const expectedHmac = CryptoJS.HmacSHA256(integrityStr, secretKey).toString();
      if (expectedHmac !== hmacVal) {
        console.error('Outer envelope HMAC mismatch');
        return null;
      }

      const [ivB64, ctB64] = payload.split(':');
      const key = CryptoJS.enc.Utf8.parse(secretKey.slice(0, 32));
      const iv = CryptoJS.enc.Base64.parse(ivB64);
      const ciphertext = CryptoJS.enc.Base64.parse(ctB64);
      const cipherParams = CryptoJS.lib.CipherParams.create({ ciphertext });

      const decrypted = CryptoJS.AES.decrypt(cipherParams, key, {
        mode: CryptoJS.mode.CBC,
        iv,
        padding: CryptoJS.pad.Pkcs7,
      });

      return JSON.parse(decrypted.toString(CryptoJS.enc.Utf8));
    } catch (error) {
      console.error('Outer envelope decryption failed:', error);
      return null;
    }
  }

  encryptOuterEnvelope(data: Record<string, unknown>, secretKey: string): OuterEnvelope | null {
    try {
      const key = CryptoJS.enc.Utf8.parse(secretKey.slice(0, 32));
      const iv = CryptoJS.lib.WordArray.random(128 / 8);
      const encrypted = CryptoJS.AES.encrypt(JSON.stringify(data), key, {
        mode: CryptoJS.mode.CBC,
        iv,
        padding: CryptoJS.pad.Pkcs7,
      });

      const payload = `${CryptoJS.enc.Base64.stringify(iv)}:${CryptoJS.enc.Base64.stringify(encrypted.ciphertext)}`;
      const generatedHmac = CryptoJS.HmacSHA256(payload, secretKey).toString();

      return {
        payload,
        hmac: generatedHmac,
      };
    } catch (error) {
      console.error('Outer envelope encryption failed:', error);
      return null;
    }
  }
}

export const cryptoEngine = new FrontendCryptoEngine();
