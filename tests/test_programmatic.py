import tempfile
from pathlib import Path
from arkitekt_server.create import create_server, temp_server, ArkitektServerConfig
from dokker import local


def test_programmatic_generation():
    # create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        config = ArkitektServerConfig()

        create_server(temp_dir, config)

        # Check that the config file was created
        config_file = Path(temp_dir) / "docker-compose.yaml"
        assert config_file.exists(), f"Docker Compose file not created at {config_file}"


def test_programmatic_temp_server():
    with temp_server() as temp_path:
        # Check that the temporary server directory was created
        assert temp_path.exists(), (
            f"Temporary server directory not created at {temp_path}"
        )

        # Check that the config file was created
        config_file = temp_path / "docker-compose.yaml"
        assert config_file.exists(), f"Docker compose file not created at {config_file}"


def test_programmatic_temp_server_with_dokker():
    with temp_server() as temp_path:
        with local(temp_path / "docker-compose.yaml") as setup:
            # Check that the setup can be initialized
            assert setup is not None, "Setup could not be initialized"

            # Check that the services are correctly set up
            assert setup.spec.find_service("gateway") is not None, (
                "Gateway service not found"
            )
            assert setup.spec.find_service("rekuest") is not None, (
                "Rekuest service not found"
            )
            assert setup.spec.find_service("mikro") is not None, (
                "Mikro service not found"
            )
            assert setup.spec.find_service("fluss") is not None, (
                "Fluss service not found"
            )

        # Here you could add more tests related to dokker if needed
