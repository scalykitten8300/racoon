"""User account management with salted/hashed password storage.

Passwords are never stored in plain text: each password is hashed with
PBKDF2-HMAC-SHA256 using a random per-user salt.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import default_data_dir

USERS_FILE = "users.json"
PBKDF2_ITERATIONS = 200_000
MIN_PASSWORD_LENGTH = 8


class AuthError(Exception):
    """Raised for registration/login failures."""


@dataclass
class UserRecord:
    username: str
    salt: str
    password_hash: str
    starting_balance: float = 10_000.0


class AccountManager:
    def __init__(self, data_dir: Path | str | None = None):
        self.data_dir = Path(data_dir) if data_dir is not None else default_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.users_path = self.data_dir / USERS_FILE
        self._users: dict[str, UserRecord] = self._load()

    def _load(self) -> dict[str, UserRecord]:
        if not self.users_path.exists():
            return {}
        with open(self.users_path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        return {name: UserRecord(**rec) for name, rec in raw.items()}

    def _save(self) -> None:
        with open(self.users_path, "w", encoding="utf-8") as fh:
            json.dump({name: asdict(rec) for name, rec in self._users.items()}, fh, indent=2)

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS
        ).hex()

    def register(self, username: str, password: str, starting_balance: float = 10_000.0) -> UserRecord:
        username = username.strip()
        if not username:
            raise AuthError("Username cannot be empty.")
        if username in self._users:
            raise AuthError(f"Username '{username}' already exists.")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise AuthError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")

        salt = secrets.token_hex(16)
        password_hash = self._hash_password(password, salt)
        record = UserRecord(
            username=username,
            salt=salt,
            password_hash=password_hash,
            starting_balance=starting_balance,
        )
        self._users[username] = record
        self._save()
        return record

    def authenticate(self, username: str, password: str) -> UserRecord:
        record = self._users.get(username)
        if record is None:
            raise AuthError("Invalid username or password.")
        candidate = self._hash_password(password, record.salt)
        if not hmac.compare_digest(candidate, record.password_hash):
            raise AuthError("Invalid username or password.")
        return record

    def exists(self, username: str) -> bool:
        return username in self._users
