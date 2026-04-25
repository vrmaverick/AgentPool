import os, base64
print(base64.urlsafe_b64encode(os.urandom(32)).decode())


import secrets
print(secrets.token_urlsafe(48))  # ~64+ chars of random secret