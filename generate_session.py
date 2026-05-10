import json
import base64
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

SESSION_AES_KEY = "0123456789012345".encode()
SESSION_AES_IV = "5432109876543210".encode()

def get_excel_serial_date(dt):
    excel_start_date = datetime(1899, 12, 30, tzinfo=ZoneInfo("Asia/Hong_Kong"))
    delta = dt - excel_start_date
    return delta.days + (delta.seconds / 86400)

now = datetime.now(ZoneInfo("Asia/Hong_Kong"))
start = now - timedelta(days=1)
end = now + timedelta(days=30)

session_data = {
    "from": int(get_excel_serial_date(start)),
    "to": int(get_excel_serial_date(end)),
    "robot": "all"
}

json_str = json.dumps(session_data)
print(f"Generating session for: {json_str}")

# Pad data
padder = padding.PKCS7(algorithms.AES.block_size).padder()
padded_data = padder.update(json_str.encode()) + padder.finalize()

# Encrypt
cipher = Cipher(
    algorithms.AES(SESSION_AES_KEY),
    modes.CBC(SESSION_AES_IV),
    backend=default_backend(),
)
encryptor = cipher.encryptor()
encrypted_bytes = encryptor.update(padded_data) + encryptor.finalize()

# Base64 encode
session_key = base64.b64encode(encrypted_bytes).decode()
print(f"\n--- SESSION KEY ---\n{session_key}\n-------------------")
