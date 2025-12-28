import os
from pathlib import Path

from ha_template.env import EnvManager
from ha_template.ha_manager import HomeAssistantManager


class FakePortAllocator:
    def __init__(self, port: int = 9001):
        self.port = port
        self.calls = 0

    def allocate(self):
        self.calls += 1
        return self.port


class FakeDocker:
    def __init__(self):
        self.running = False
        self.up_calls = []
        self.stop_calls = 0
        self.pull_calls = 0
        self.exec_calls = []

    def up(self, rebuild: bool = False):
        self.running = True
        self.up_calls.append(rebuild)

    def stop(self):
        self.running = False
        self.stop_calls += 1

    def pull(self):
        self.pull_calls += 1

    def status(self) -> str:
        return "running" if self.running else "stopped"

    def is_running(self, service: str = "homeassistant") -> bool:
        return self.running


class FakeHacs:
    def __init__(self):
        self.versions = []

    def ensure(self, version: str) -> bool:
        self.versions.append(version)
        return True


class FakeUserSetup:
    def __init__(self, created: bool = True):
        self.onboarding_calls = 0
        self.user_calls = []
        self.created = created

    def ensure_onboarding_flag(self):
        self.onboarding_calls += 1

    def ensure_user(self, username: str, password: str, display_name: str):
        self.user_calls.append((username, password, display_name))
        return self.created


def build_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".env.example").write_text("HOST_HA_PORT=auto\n")
    (repo / "docker-compose.yml").write_text("services: {}")
    (repo / "homeassistant").mkdir()
    return repo


def test_manager_start_prepares_environment(tmp_path):
    repo = build_repo(tmp_path)
    env_manager = EnvManager(repo / ".env")
    port_allocator = FakePortAllocator()
    docker = FakeDocker()
    hacs = FakeHacs()
    user_setup = FakeUserSetup(created=True)

    manager = HomeAssistantManager(
        repo,
        env_manager=env_manager,
        port_allocator=port_allocator,
        docker=docker,
        hacs=hacs,
        user_setup=user_setup,
    )

    started = manager.start()
    assert started is True
    assert docker.up_calls == [False]
    assert user_setup.user_calls
    assert "HOST_HA_PORT=9001" in (repo / ".env").read_text()
    assert f"HOST_UID={os.getuid()}" in (repo / ".env").read_text()
    assert f"HOST_GID={os.getgid()}" in (repo / ".env").read_text()
    assert "COMPOSE_PROJECT_NAME=" in (repo / ".env").read_text()


def test_manager_autostart_skips_if_running(tmp_path):
    repo = build_repo(tmp_path)
    env_manager = EnvManager(repo / ".env")
    port_allocator = FakePortAllocator()
    docker = FakeDocker()
    docker.running = True
    hacs = FakeHacs()
    user_setup = FakeUserSetup(created=False)

    manager = HomeAssistantManager(
        repo,
        env_manager=env_manager,
        port_allocator=port_allocator,
        docker=docker,
        hacs=hacs,
        user_setup=user_setup,
    )

    started = manager.start(auto=True)
    assert started is False
    assert not docker.up_calls
    assert user_setup.user_calls


def test_manager_restarts_when_credentials_added_and_running(tmp_path):
    repo = build_repo(tmp_path)
    env_manager = EnvManager(repo / ".env")
    port_allocator = FakePortAllocator()
    docker = FakeDocker()
    docker.running = True
    hacs = FakeHacs()
    user_setup = FakeUserSetup(created=True)

    manager = HomeAssistantManager(
        repo,
        env_manager=env_manager,
        port_allocator=port_allocator,
        docker=docker,
        hacs=hacs,
        user_setup=user_setup,
    )

    started = manager.start(auto=True)
    assert started is True
    assert docker.stop_calls == 1
    assert docker.up_calls == [False]
