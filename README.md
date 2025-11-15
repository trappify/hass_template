# Home Assistant Integration Template

This repository bootstraps a persistent Home Assistant instance that runs inside Docker and is managed through a Python CLI. It is designed to be cloned/forked for every new integration so the development container, credentials, and helper scripts are ready immediately.

## Highlights

- **Persistent config** – the Home Assistant configuration under `homeassistant/` is bind mounted, so installations (HACS, custom integrations, etc.) survive restarts.
- **Automatic port selection** – the first free port in the `8123-9123` range is recorded in `.env`, letting multiple template instances run on the same host.
- **One-click devcontainer** – `.devcontainer/devcontainer.json` installs dependencies, configures git hooks, and bootstraps the helper CLI automatically.
- **Turnkey HACS** – `scripts/ha_manager.py` downloads and extracts the requested HACS release before each start if it is not already present.
- **Auto-start hooks** – `.githooks/post-merge`/`post-checkout` call `ha_manager.py autostart` so pulling new changes or switching branches spins up the container without manual intervention.
- **Tests for all tooling** – `pytest` covers the environment helpers, installers, docker wrapper, and the high-level manager class.

## Usage

1. Run `python3 scripts/configure_repo.py --non-interactive` once after cloning to copy `.env.example`, set git hooks, and register the default git identity.
2. Start Home Assistant with `python3 scripts/ha_manager.py start` (or `make start`). The command ensures HACS is installed, assigns a free port, and creates the default credentials if necessary.
3. Visit the UI at `http://localhost:<assigned-port>`; the assigned port is stored in `.env` under `HOST_HA_PORT`.
4. Manage the stack with the remaining commands:

   - `python3 scripts/ha_manager.py stop`
   - `python3 scripts/ha_manager.py restart`
   - `python3 scripts/ha_manager.py rebuild`
   - `python3 scripts/ha_manager.py status`

5. Run `pytest` (or `make test`) before committing to keep coverage for the helper tooling.

For detailed instructions on cloning this repository as the base for a brand-new integration (including Codex CLI-friendly guidance), see [USING_TEMPLATE.md](USING_TEMPLATE.md).

## Codex CLI bootstrap prompt

When you create a brand-new integration repo, paste the prompt below into Codex CLI (replace `<NEW_REPO_PATH>` with the absolute path to your empty project directory). Codex will then mirror the template from `https://github.com/trappify/hass_template`, configure git/hooks, run tests, and spin up Home Assistant automatically.

```
You are Codex working inside <NEW_REPO_PATH>. Bootstrap this project by cloning the Home Assistant template from https://github.com/trappify/hass_template into /tmp/hass_template, copy everything except its .git directory into the current repo, and remove the temporary clone. After that:
1. Run `python3 scripts/configure_repo.py --non-interactive`.
2. Create a Python venv (`python3 -m venv .venv && source .venv/bin/activate`), install `.[dev]`, and run `pytest`.
3. Start the dev container with `python3 scripts/ha_manager.py start` (use `--auto` if it is already up) so I can browse Home Assistant right away; report the host IP/port and default credentials from `.env`.
4. Summarize what you copied or changed and list any follow-up steps I should take.
Never skip restarting the container after changes, and never return work unless the tests succeed.
```

## Default credentials

Values live in `.env` and can be customized as needed. By default the template provisions username/password `devbox` / `devbox` with the display name `Dev Box Owner`.

- `DEFAULT_HA_USERNAME`
- `DEFAULT_HA_PASSWORD`
- `DEFAULT_HA_NAME`

The config also enables the `trusted_networks` auth provider for local subnets so testing remains convenient.

## HACS

`HACSInstaller` downloads the release archive defined by `HACS_VERSION` (default `1.34.0`) and extracts it into `homeassistant/custom_components/hacs`. The `homeassistant/www/community` directory is also created automatically. To bump versions, update `.env.example` and rerun `scripts/configure_repo.py`.

## Devcontainer behavior

Opening the repository in VS Code Dev Containers installs dev dependencies, configures git hooks, and runs `ha_manager.py autostart` so Home Assistant begins running without extra steps. The container includes the Docker CLI via the `docker-outside-of-docker` feature, so the helper scripts can talk to the host Docker daemon.
