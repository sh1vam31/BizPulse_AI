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


def test_name_validation():
    import pytest
    from app.schemas.auth import validate_person_name

    # Valid names
    assert validate_person_name("Jane Doe") == "Jane Doe"
    assert validate_person_name("O'Connor") == "O'Connor"
    assert validate_person_name("Jean-Luc") == "Jean-Luc"
    assert validate_person_name("Dr. Smith") == "Dr. Smith"

    # Invalid names containing numbers
    with pytest.raises(ValueError, match="cannot contain numbers"):
        validate_person_name("123")

    with pytest.raises(ValueError, match="cannot contain numbers"):
        validate_person_name("User123")

    # Invalid characters or too short
    with pytest.raises(ValueError, match="at least 2 letters"):
        validate_person_name("A")


def test_email_typo_domain_suggestion():
    import pytest
    from app.schemas.auth import check_email_domain

    # Valid emails
    assert check_email_domain("user@gmail.com") == "user@gmail.com"
    assert check_email_domain("jane@techcorp.io") == "jane@techcorp.io"

    # Common Gmail typos
    with pytest.raises(ValueError, match="Did you mean @gmail.com"):
        check_email_domain("shiv@gmaill.com")

    with pytest.raises(ValueError, match="Did you mean @gmail.com"):
        check_email_domain("test@gamil.com")

    # Yahoo typo
    with pytest.raises(ValueError, match="Did you mean @yahoo.com"):
        check_email_domain("user@yaho.com")

    # Outlook typo
    with pytest.raises(ValueError, match="Did you mean @outlook.com"):
        check_email_domain("user@outlok.com")

    # Hotmail typo
    with pytest.raises(ValueError, match="Did you mean @hotmail.com"):
        check_email_domain("user@hotmial.com")

    # .con generic typo
    with pytest.raises(ValueError, match="Did you mean @company.com"):
        check_email_domain("user@company.con")


