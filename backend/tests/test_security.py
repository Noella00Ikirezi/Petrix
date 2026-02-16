"""Tests for security utilities."""
from datetime import timedelta
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_token,
)


class TestPasswordHashing:
    def test_hash_returns_string(self):
        result = get_password_hash("mypassword")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_differs_from_plain(self):
        result = get_password_hash("mypassword")
        assert result != "mypassword"

    def test_verify_correct_password(self):
        hashed = get_password_hash("testpassword123")
        assert verify_password("testpassword123", hashed) is True

    def test_verify_wrong_password(self):
        hashed = get_password_hash("testpassword123")
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        hash1 = get_password_hash("samepassword")
        hash2 = get_password_hash("samepassword")
        assert hash1 != hash2  # bcrypt uses random salt


class TestJWT:
    def test_create_token_returns_string(self):
        token = create_access_token({"sub": "user@test.com"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        token = create_access_token({"sub": "user@test.com"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user@test.com"
        assert "exp" in payload

    def test_decode_invalid_token(self):
        result = decode_token("invalid.token.string")
        assert result is None

    def test_create_token_with_custom_expiry(self):
        token = create_access_token(
            {"sub": "user@test.com"},
            expires_delta=timedelta(hours=2),
        )
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user@test.com"

    def test_token_contains_exp_claim(self):
        token = create_access_token({"sub": "test"})
        payload = decode_token(token)
        assert "exp" in payload
