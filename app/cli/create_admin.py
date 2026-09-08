from sqlalchemy import select

from app.core.constants import ROLE_ADMINISTRATOR
from app.core.database import SessionLocal
from app.core.security import (
    generate_temporary_password,
    hash_password,
)
from app.models.user import UserModel


def normalize(value: str) -> str:
    return value.strip().lower()


def main() -> None:
    db = SessionLocal()

    try:
        existing_admin = db.scalar(
            select(UserModel).where(
                UserModel.role == ROLE_ADMINISTRATOR
            )
        )

        if existing_admin is not None:
            print("Administrator account already exists.")
            print(f"Username: {existing_admin.username}")
            return

        print("Create Initial Administrator")
        print("----------------------------")

        username = normalize(
            input("Username: ")
        )

        email = normalize(
            input("Email: ")
        )

        full_name = input(
            "Full Name: "
        ).strip()

        if not username:
            raise ValueError("Username is required.")

        if not email:
            raise ValueError("Email is required.")

        if not full_name:
            raise ValueError("Full name is required.")

        existing_username = db.scalar(
            select(UserModel).where(
                UserModel.username == username
            )
        )

        if existing_username is not None:
            raise ValueError(
                "Username already exists."
            )

        existing_email = db.scalar(
            select(UserModel).where(
                UserModel.email == email
            )
        )

        if existing_email is not None:
            raise ValueError(
                "Email already exists."
            )

        temporary_password = (
            generate_temporary_password()
        )

        user = UserModel(
            username=username,
            email=email,
            password_hash=hash_password(
                temporary_password
            ),
            full_name=full_name,
            role=ROLE_ADMINISTRATOR,
            is_active=True,
            must_change_password=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print()
        print(
            "Administrator account created successfully."
        )
        print()
        print(f"Username           : {user.username}")
        print(f"Email              : {user.email}")
        print(f"Full Name          : {user.full_name}")
        print(f"Role               : {user.role}")
        print(
            f"Temporary Password : {temporary_password}"
        )
        print()
        print(
            "IMPORTANT: Save this temporary password now."
        )
        print(
            "It will not be displayed again."
        )
        print(
            "The administrator must change it "
            "on first login."
        )

    except Exception as exc:
        db.rollback()
        print()
        print(f"Error: {exc}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
