import datetime
from services.auth_service import AuthService


def test_create_and_decode_access_token():
    payload_data = {"sub": "12345", "role": "tenant"}
    token = AuthService.create_access_token(data=payload_data)

    assert token is not None
    assert isinstance(token, str)

    decoded = AuthService.decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "12345"
    assert decoded["role"] == "tenant"
    assert "exp" in decoded


def test_expired_token():
    payload_data = {"sub": "expired_user", "role": "admin"}
    # Token that expired 1 hour ago
    token = AuthService.create_access_token(
        data=payload_data, expires_delta=datetime.timedelta(hours=-1)
    )

    decoded = AuthService.decode_access_token(token)
    assert decoded is None
