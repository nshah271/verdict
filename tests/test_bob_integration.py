"""Tests for Bob integration (Custom Mode and MCP installation)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from verdict.cli import (
    check_mcp_installed,
    get_global_mcp_config_path,
    get_project_mcp_config_path,
    install_bob_mode,
)


class TestMcpConfigPaths:
    """Test MCP configuration path resolution."""

    @patch("pathlib.Path.cwd")
    def test_project_mcp_path(self, mock_cwd: MagicMock) -> None:
        """Test project-level MCP config path."""
        mock_cwd.return_value = Path("/fake/project")
        result = get_project_mcp_config_path()
        assert result == Path("/fake/project/.bob/mcp.json")

    @patch("platform.system")
    @patch.dict("os.environ", {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"})
    def test_global_mcp_path_windows(self, mock_system: MagicMock) -> None:
        """Test global MCP config path on Windows."""
        mock_system.return_value = "Windows"
        result = get_global_mcp_config_path()
        assert result == Path("C:\\Users\\Test\\AppData\\Roaming\\Bob\\settings\\mcp_settings.json")

    @patch("platform.system")
    @patch("pathlib.Path.home")
    def test_global_mcp_path_macos(self, mock_home: MagicMock, mock_system: MagicMock) -> None:
        """Test global MCP config path on macOS."""
        mock_system.return_value = "Darwin"
        mock_home.return_value = Path("/Users/test")
        result = get_global_mcp_config_path()
        assert result == Path("/Users/test/.bob/settings/mcp_settings.json")

    @patch("platform.system")
    @patch("pathlib.Path.home")
    def test_global_mcp_path_linux(self, mock_home: MagicMock, mock_system: MagicMock) -> None:
        """Test global MCP config path on Linux."""
        mock_system.return_value = "Linux"
        mock_home.return_value = Path("/home/test")
        result = get_global_mcp_config_path()
        assert result == Path("/home/test/.bob/settings/mcp_settings.json")


class TestCheckMcpInstalled:
    """Test MCP server installation detection."""

    @patch("verdict.cli.get_project_mcp_config_path")
    @patch("verdict.cli.get_global_mcp_config_path")
    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_mcp_installed_project(
        self,
        mock_file: MagicMock,
        mock_exists: MagicMock,
        mock_global: MagicMock,
        mock_project: MagicMock,
    ) -> None:
        """Test detection when MCP server is installed at project level."""
        mock_project.return_value = Path("/fake/project/.bob/mcp.json")
        mock_global.return_value = Path("/fake/home/.bob/settings/mcp_settings.json")
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(
            {"mcpServers": {"verdict": {"command": "verdict-mcp"}}}
        )

        result = check_mcp_installed()
        assert result is True

    @patch("verdict.cli.get_project_mcp_config_path")
    @patch("verdict.cli.get_global_mcp_config_path")
    @patch("pathlib.Path.exists")
    def test_mcp_not_installed_file_missing(
        self, mock_exists: MagicMock, mock_global: MagicMock, mock_project: MagicMock
    ) -> None:
        """Test detection when MCP config files don't exist."""
        mock_project.return_value = Path("/fake/project/.bob/mcp.json")
        mock_global.return_value = Path("/fake/home/.bob/settings/mcp_settings.json")
        mock_exists.return_value = False

        result = check_mcp_installed()
        assert result is False

    @patch("verdict.cli.get_project_mcp_config_path")
    @patch("verdict.cli.get_global_mcp_config_path")
    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_mcp_not_installed_no_verdict_entry(
        self,
        mock_file: MagicMock,
        mock_exists: MagicMock,
        mock_global: MagicMock,
        mock_project: MagicMock,
    ) -> None:
        """Test detection when MCP config exists but verdict not registered."""
        mock_project.return_value = Path("/fake/project/.bob/mcp.json")
        mock_global.return_value = Path("/fake/home/.bob/settings/mcp_settings.json")
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(
            {"mcpServers": {"other": {"command": "other-mcp"}}}
        )

        result = check_mcp_installed()
        assert result is False

    @patch("verdict.cli.get_project_mcp_config_path")
    def test_mcp_check_handles_exceptions(self, mock_project: MagicMock) -> None:
        """Test that exceptions during MCP check return False."""
        mock_project.side_effect = Exception("Test error")

        result = check_mcp_installed()
        assert result is False


class TestInstallBobMode:
    """Test Bob Custom Mode installation (project-level)."""

    @patch("pathlib.Path.cwd")
    @patch("verdict.cli.check_mcp_installed")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    @patch("shutil.copy2")
    @patch("click.echo")
    def test_install_creates_bob_directory(
        self,
        mock_echo: MagicMock,
        mock_copy: MagicMock,
        mock_exists: MagicMock,
        mock_mkdir: MagicMock,
        mock_mcp: MagicMock,
        mock_cwd: MagicMock,
    ) -> None:
        """Test that install creates .bob directory in project."""
        mock_cwd.return_value = Path("/fake/project")
        mock_mcp.return_value = True
        mock_exists.return_value = False  # File doesn't exist yet

        install_bob_mode()

        # Verify .bob directory was created
        assert mock_mkdir.call_count >= 1

    @patch("pathlib.Path.cwd")
    @patch("verdict.cli.check_mcp_installed")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    @patch("shutil.copy2")
    @patch("click.echo")
    def test_install_copies_custom_mode(
        self,
        mock_echo: MagicMock,
        mock_copy: MagicMock,
        mock_exists: MagicMock,
        mock_mkdir: MagicMock,
        mock_mcp: MagicMock,
        mock_cwd: MagicMock,
    ) -> None:
        """Test that install copies custom_modes.yaml."""
        mock_cwd.return_value = Path("/fake/project")
        mock_mcp.return_value = True
        mock_exists.return_value = False  # File doesn't exist yet

        install_bob_mode()

        # Verify file was copied
        assert mock_copy.call_count == 1

    @patch("pathlib.Path.cwd")
    @patch("verdict.cli.check_mcp_installed")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    @patch("shutil.copy2")
    @patch("click.echo")
    def test_install_preserves_existing_file(
        self,
        mock_echo: MagicMock,
        mock_copy: MagicMock,
        mock_exists: MagicMock,
        mock_mkdir: MagicMock,
        mock_mcp: MagicMock,
        mock_cwd: MagicMock,
    ) -> None:
        """Test that install is non-destructive (preserves existing file)."""
        mock_cwd.return_value = Path("/fake/project")
        mock_mcp.return_value = True
        mock_exists.return_value = True  # File already exists

        install_bob_mode()

        # Verify file was NOT copied (preserved)
        assert mock_copy.call_count == 0

    @patch("pathlib.Path.cwd")
    @patch("verdict.cli.check_mcp_installed")
    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.exists")
    @patch("shutil.copy2")
    @patch("click.echo")
    def test_install_warns_if_mcp_not_installed(
        self,
        mock_echo: MagicMock,
        mock_copy: MagicMock,
        mock_exists: MagicMock,
        mock_mkdir: MagicMock,
        mock_mcp: MagicMock,
        mock_cwd: MagicMock,
    ) -> None:
        """Test that install warns when MCP server is not registered."""
        mock_cwd.return_value = Path("/fake/project")
        mock_mcp.return_value = False  # MCP not installed
        mock_exists.return_value = False

        install_bob_mode()

        # Verify warning was printed
        warning_calls = [call for call in mock_echo.call_args_list if "MCP server" in str(call)]
        assert len(warning_calls) > 0


class TestYamlValidity:
    """Test that YAML configuration file is valid."""

    def test_custom_mode_yaml_exists(self) -> None:
        """Test that custom_mode.yaml exists in the package."""
        yaml_path = (
            Path(__file__).parent.parent / "verdict" / "bob_integration" / "custom_mode.yaml"
        )
        assert yaml_path.exists(), "custom_mode.yaml not found"

    def test_custom_mode_yaml_parses(self) -> None:
        """Test that custom_mode.yaml is valid YAML."""
        yaml_path = (
            Path(__file__).parent.parent / "verdict" / "bob_integration" / "custom_mode.yaml"
        )

        try:
            import yaml
        except ImportError:
            pytest.skip("pyyaml not available")

        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Verify Bob Custom Mode schema
        assert "customModes" in data
        assert isinstance(data["customModes"], list)
        assert len(data["customModes"]) > 0

        mode = data["customModes"][0]
        assert mode["slug"] == "verifier"
        assert mode["name"] == "Verifier"
        assert "roleDefinition" in mode
        assert "whenToUse" in mode
        assert "description" in mode
        assert "customInstructions" in mode
        assert "groups" in mode
        assert mode["source"] == "project"


# Made with Bob
