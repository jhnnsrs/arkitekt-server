from contextlib import contextmanager
from typing import Generator
from arkitekt_server.diff import write_virtual_config_files
from .config import ArkitektServerConfig
from pathlib import Path
import random


def create_server(path: Path | str, config: ArkitektServerConfig | None = None):
    """
    Create a server configuration at the specified path using the provided config.

    Args:
        path (str): The path where the server configuration will be created.
        config (ArkitektServerConfig): The configuration for the server.

    Returns:
        None
    """
    if isinstance(path, str):
        path = Path(path)

    # Ensure the directory exists
    path.mkdir(parents=True, exist_ok=True)

    if config is None:
        config = ArkitektServerConfig()

    # Write the configuration to a file
    write_virtual_config_files(path, config)


@contextmanager
def temp_server(
    config: ArkitektServerConfig | None = None,
) -> Generator[Path, None, None]:
    """
    Create a temporary server configuration using the provided config.

    This is a context manager that yields the path to the temporary server configuration.
    The server directory is created and cleaned up automatically.

    Attention: The docker compose project that was created will not be cleaned up automatically.
                If you want to clean it up, you have to call `down` on the project manually.
                Or use the `local` function from the `dokker` package to create a local deployment.

    Args:
        config (ArkitektServerConfig): The configuration for the server.

    Yield:
        Path: The path to the temporary server configuration.
    """
    import tempfile

    if not config:
        config = ArkitektServerConfig()

        # Make sure we are creating volumes not bind mounts
        config.minio.mount = None
        config.db.mount = None
        config.gateway.exposed_http_port = random.randint(8000, 9000)
        config.gateway.exposed_https_port = random.randint(9000, 10000)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        create_server(temp_path, config)
        yield temp_path
