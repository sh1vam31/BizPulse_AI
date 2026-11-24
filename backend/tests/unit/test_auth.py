from datetime import timedelta
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing():
    raw = "MySuperSecretPassword#123"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_access_token_creation_and_decoding():
    user_id = "test-uuid-1234-5678"
    token = create_access_token(subject=user_id)
    payload = decode_token(token)
    assert payload is not None
    assert payload.get("sub") == user_id
    assert payload.get("type") == "access"
    assert "exp" in payload


def test_jwt_refresh_token_creation_and_decoding():
    user_id = "test-uuid-refresh-5678"
    token = create_refresh_token(subject=user_id)
    payload = decode_token(token)
    assert payload is not None
    assert payload.get("sub") == user_id
    assert payload.get("type") == "refresh"
    assert "exp" in payload


def test_expired_token_handling():
    user_id = "test-expired"
    # Create expired token
    expired_token = create_access_token(subject=user_id, expires_delta=timedelta(seconds=-10))
    payload = decode_token(expired_token)
    assert payload is None


def test_invalid_token_string():
    payload = decode_token("invalid.token.string")
    assert payload is None

