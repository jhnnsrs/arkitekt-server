from pathlib import Path
from typer.testing import CliRunner
from typer.main import Typer


def run_init_command(
    app: Typer, runner: CliRunner, port: int = 80, ssl_port: int = 443
):
    # Run the arkitekt init stable command
    result = runner.invoke(
        app,
        [
            "init",
            "stable",
            "--defaults",
            "--port",
            str(port),
            "--ssl-port",
            str(ssl_port),
        ],
    )

    # Check that the command succeeded
    assert result.exit_code == 0, (
        f"Command failed with exit code {result.exit_code}. Output: {result.stderr + result.stdout}"
    )


def run_building_command(app: Typer, runner: CliRunner):
    # Run the arkitekt build command
    result = runner.invoke(app, ["build", "docker", "--yes"])

    # Check that the command succeeded
    assert result.exit_code == 0, (
        f"Command failed with exit code {result.exit_code}. Output: {result.stdout}"
    )

    # Check that the config file was created
    config_file = Path("docker-compose.yaml")
    assert config_file.exists(), f"Docker Compose file not created at {config_file}"
