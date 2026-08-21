import base64
import os
import secrets
import sys
from pathlib import Path

path = Path(sys.argv[1] if len(sys.argv) > 1 else ".env")
text = path.read_text()
values = {
    "replace-with-a-long-random-value": secrets.token_urlsafe(64),
    "replace-with-a-strong-password": secrets.token_urlsafe(32),
    "replace-with-a-fernet-key": base64.urlsafe_b64encode(os.urandom(32)).decode(),
}
for old, new in values.items():
    text = text.replace(old, new)
path.write_text(text)

