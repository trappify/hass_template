from types import SimpleNamespace

from ha_template.user_setup import UserSetup


class FakeDocker:
    def __init__(self):
        self.commands = []
        self.responses = {}
        self.users = set()

    def set_response(self, command: tuple[str, ...], stdout: str) -> None:
        self.responses[command] = stdout

    def run_one_off(self, service, command, check=True, capture=False):
        command_tuple = tuple(command)
        self.commands.append((service, command_tuple, capture))
        stdout = ""
        if capture:
            if command_tuple in self.responses:
                stdout = self.responses[command_tuple]
            elif command and command[-1] == "list":
                if self.users:
                    stdout = "\n".join(sorted(self.users)) + "\n\nTotal users: 1\n"
                else:
                    stdout = "\n\nTotal users: 0\n"
            elif "-c" in command:
                stdout = "created"
        return SimpleNamespace(stdout=stdout, returncode=0)


def test_user_setup_detects_existing_user(tmp_path):
    config_dir = tmp_path / "config"
    docker = FakeDocker()
    docker.set_response(
        (
            "python3",
            "-m",
            "homeassistant",
            "--script",
            "auth",
            "-c",
            "/config",
            "list",
        ),
        "devbox\n\nTotal users: 1\n",
    )

    setup = UserSetup(config_dir, docker)
    assert setup.has_user("devbox") is True
    assert setup.has_user("other") is False


def test_user_setup_creates_user_when_missing(tmp_path):
    config_dir = tmp_path / "config"
    (config_dir / ".storage").mkdir(parents=True)
    docker = FakeDocker()
    setup = UserSetup(config_dir, docker)

    created = setup.ensure_user("devadmin", "secret", "Dev Admin")
    assert created is True
    assert docker.commands[0][1][:2] == ("python3", "-c")


def test_onboarding_flag(tmp_path):
    config_dir = tmp_path / "config"
    setup = UserSetup(config_dir, FakeDocker())
    setup.ensure_onboarding_flag()
    onboarding = config_dir / ".storage" / "onboarding"
    assert onboarding.exists()
    original = onboarding.read_text()
    setup.ensure_onboarding_flag()
    assert onboarding.read_text() == original
