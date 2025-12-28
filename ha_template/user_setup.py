"""Ensures default Home Assistant credentials exist."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .docker_control import DockerController


@dataclass
class UserSetup:
    """Create a default owner account if it doesn't exist."""

    config_dir: Path
    docker: DockerController

    def has_user(self, username: str) -> bool:
        return username in self._list_usernames()

    def _list_usernames(self) -> List[str]:
        result = self.docker.run_one_off(
            "homeassistant",
            [
                "python3",
                "-m",
                "homeassistant",
                "--script",
                "auth",
                "-c",
                "/config",
                "list",
            ],
            capture=True,
            check=False,
        )
        usernames: List[str] = []
        for line in (result.stdout or "").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("Total users"):
                continue
            usernames.append(stripped)
        return usernames

    def ensure_user(
        self,
        username: str,
        password: str,
        display_name: str,
        attempts: int = 10,
        delay: float = 2.0,
    ) -> bool:
        script = f"""
import base64
import bcrypt
import json
import uuid
from pathlib import Path

username = {username!r}
password = {password!r}
display_name = {display_name!r}

auth_path = Path("/config/.storage/auth")
provider_path = Path("/config/.storage/auth_provider.homeassistant")

def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text())
    return default

auth_data = load_json(
    auth_path,
    {{
        "version": 1,
        "minor_version": 1,
        "key": "auth",
        "data": {{"users": [], "groups": [], "credentials": [], "refresh_tokens": []}},
    }},
)
provider_data = load_json(
    provider_path,
    {{
        "version": 1,
        "minor_version": 1,
        "key": "auth_provider.homeassistant",
        "data": {{"users": []}},
    }},
)

groups = auth_data["data"].setdefault("groups", [])
def ensure_group(group_id, name):
    if not any(group.get("id") == group_id for group in groups):
        groups.append({{"id": group_id, "name": name}})

ensure_group("system-admin", "Administrators")
ensure_group("system-users", "Users")
ensure_group("system-read-only", "Read Only")

users = auth_data["data"].setdefault("users", [])
credentials = auth_data["data"].setdefault("credentials", [])
auth_users = provider_data["data"].setdefault("users", [])

user_id = None
for cred in credentials:
    if (
        cred.get("auth_provider_type") == "homeassistant"
        and cred.get("data", {{}}).get("username") == username
    ):
        user_id = cred.get("user_id")
        break

if user_id is None:
    for user in users:
        if user.get("name") in (display_name, username):
            user_id = user.get("id")
            break

created = False
if user_id is None:
    user_id = uuid.uuid4().hex
    users.append(
        {{
            "id": user_id,
            "group_ids": ["system-admin"],
            "is_owner": True,
            "is_active": True,
            "name": display_name,
            "system_generated": False,
            "local_only": False,
        }}
    )
    created = True
else:
    for user in users:
        if user.get("id") == user_id:
            user["is_active"] = True
            if "system-admin" not in user.get("group_ids", []):
                user.setdefault("group_ids", []).append("system-admin")
            break

if not any(
    cred.get("auth_provider_type") == "homeassistant"
    and cred.get("data", {{}}).get("username") == username
    for cred in credentials
):
    credentials.append(
        {{
            "id": uuid.uuid4().hex,
            "user_id": user_id,
            "auth_provider_type": "homeassistant",
            "auth_provider_id": None,
            "data": {{"username": username}},
        }}
    )
    created = True

if not any(user.get("username") == username for user in auth_users):
    hashed = bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt(rounds=12))
    auth_users.append(
        {{
            "username": username,
            "password": base64.b64encode(hashed).decode(),
        }}
    )
    created = True

auth_path.write_text(json.dumps(auth_data, indent=2))
provider_path.write_text(json.dumps(provider_data, indent=2))
print("created" if created else "exists")
"""
        for _ in range(max(1, attempts)):
            result = self.docker.run_one_off(
                "homeassistant",
                ["python3", "-c", script],
                check=False,
                capture=True,
            )
            if "created" in (result.stdout or "").lower():
                return True
            if "exists" in (result.stdout or "").lower():
                return False
            time.sleep(delay)
        return False

    def ensure_onboarding_flag(self) -> None:
        storage = self.config_dir / ".storage"
        storage.mkdir(parents=True, exist_ok=True)
        onboarding_file = storage / "onboarding"
        if onboarding_file.exists():
            return
        onboarding_file.write_text(
            json.dumps(
                {
                    "version": 1,
                    "minor_version": 1,
                    "key": "onboarding",
                    "data": {
                        "done": ["user", "core_config", "integration", "analytics"]
                    },
                },
                indent=2,
            )
        )
