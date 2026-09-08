import hashlib
import secrets
import string

from pwdlib import PasswordHash


password_hasher = PasswordHash.recommended()

PASSWORD_SPECIAL_CHARACTERS = "!@#$%*-_"


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    return password_hasher.verify(
        password,
        password_hash,
    )


def validate_password(password: str) -> None:
    if len(password) < 12:
        raise ValueError(
            "Password must contain at least 12 characters."
        )

    if not any(char.islower() for char in password):
        raise ValueError(
            "Password must contain at least one lowercase letter."
        )

    if not any(char.isupper() for char in password):
        raise ValueError(
            "Password must contain at least one uppercase letter."
        )

    if not any(char.isdigit() for char in password):
        raise ValueError(
            "Password must contain at least one number."
        )

    if not any(
        char in PASSWORD_SPECIAL_CHARACTERS
        for char in password
    ):
        raise ValueError(
            "Password must contain at least one special character."
        )


def generate_temporary_password(length: int = 20) -> str:
    if length < 12:
        raise ValueError(
            "Temporary password length must be at least 12 characters."
        )

    alphabet = (
        string.ascii_letters
        + string.digits
        + PASSWORD_SPECIAL_CHARACTERS
    )

    while True:
        password = "".join(
            secrets.choice(alphabet)
            for _ in range(length)
        )

        try:
            validate_password(password)
            return password
        except ValueError:
            continue


def generate_session_token() -> str:
    return secrets.token_urlsafe(48)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()
