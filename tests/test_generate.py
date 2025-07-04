from typer.testing import CliRunner
from arkitekt_server.main import app

runner = CliRunner()


def test_generate():
    with runner.isolated_filesystem():
        result = runner.invoke(app, ["init", "default"])
        assert result.exit_code == 0, (
            f"Failed to initialize default config: {result.output}"
        )
