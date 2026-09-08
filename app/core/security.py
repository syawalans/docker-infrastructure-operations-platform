import hashlib
import secrets
import string

from pwdlib import PasswordHash


password_hasher = PasswordHash.recommended()


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


def generate_temporary_password(length: int = 20) -> str:
    if length < 12:
        raise ValueError(
            "Temporary password length must be at least 12 characters."
        )

    alphabet = (
        string.ascii_letters
        + string.digits
        + "!@#$%*-_"
    )

    while True:
        password = "".join(
            secrets.choice(alphabet)
            for _ in range(length)
        )

        if (
            any(char.islower() for char in password)
            and any(char.isupper() for char in password)
            and any(char.isdigit() for char in password)
            and any(char in "!@#$%*-_" for char in password)
        ):
            return password


def generate_session_token() -> str:
    return secrets.token_urlsafe(48)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()
