import jwt
import os

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjI4OTc1NjIsInN1YiI6IjcxNzAyNWZhLTk0ZWQtNGM0ZS04MDIxLTlmNWExZTE2MmI2ZCIsImVtYWlsIjoidGVzdDJAZXhhbXBsZS5jb20iLCJyb2xlIjoidmlld2VyIn0.jnUVTslDHGN5qr-PMzA2NKV4fa--DiP5EiCb44Vp994"
secret = os.getenv("JWT_SECRET", "your-jwt-secret-key")

try:
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    print(payload)
except Exception as e:
    print(e)
