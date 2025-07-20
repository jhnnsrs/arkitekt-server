import tempfile
import os
from pathlib import Path
from typer.testing import CliRunner
from arkitekt_server.main import app
from tests.utils import run_building_command, run_init_command

runner = CliRunner()


def test_generate():
    """Test that runs the script in a temporary folder and returns the temporary folder."""
    # Create a temporary directory
    with runner.isolated_filesystem() as temp_dir:
        # Run the arkitekt init stable command
        result = runner.invoke(app, ["init", "stable", "--defaults"])

        # Check that the command succeeded
        assert result.exit_code == 0, (
            f"Command failed with exit code {result.exit_code}. Output: {result.stdout}"
        )

        # Check that the config file was created
        config_file = Path("arkitekt_server_config.yaml")
        assert config_file.exists(), f"Config file not created at {config_file}"

        # Check that gitignore was created/updated
        gitignore_file = Path(".gitignore")
        assert gitignore_file.exists(), (
            f"Gitignore file not created at {gitignore_file}"
        )

        # Check gitignore contains the config file
        gitignore_content = gitignore_file.read_text()
        assert "arkitekt_server_config.yaml" in gitignore_content, (
            "Config file not added to .gitignore"
        )

        # Return the temporary directory path for potential further inspection
        return temp_dir


def test_building():
    """Test that runs the building command in a temporary folder."""
    # Create a temporary directory
    with runner.isolated_filesystem() as temp_dir:
        run_init_command(app, runner)
        run_building_command(app, runner)

        docker_compose_file = Path("docker-compose.yaml")
        assert docker_compose_file.exists(), (
            f"Docker Compose file not created at {docker_compose_file}"
        )
