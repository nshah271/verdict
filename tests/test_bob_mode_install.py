"""Test bob-mode installation functionality."""

import json
import shutil
from pathlib import Path

import pytest

from verdict.cli import install_bob_mode


@pytest.fixture
def temp_project_dir(tmp_path, monkeypatch):
    """Create a temporary project directory and change to it."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_install_bob_mode_creates_directories(temp_project_dir):
    """Test that install_bob_mode creates .bob and .bob/commands directories."""
    install_bob_mode()

    bob_dir = temp_project_dir / ".bob"
    commands_dir = bob_dir / "commands"

    assert bob_dir.exists()
    assert commands_dir.exists()


def test_install_bob_mode_installs_custom_mode(temp_project_dir):
    """Test that install_bob_mode copies custom_modes.yaml."""
    install_bob_mode()

    custom_modes_file = temp_project_dir / ".bob" / "custom_modes.yaml"
    assert custom_modes_file.exists()

    # Verify it contains the Verifier mode
    content = custom_modes_file.read_text()
    assert "verifier" in content.lower()
    assert "Verifier" in content


def test_install_bob_mode_installs_slash_commands(temp_project_dir):
    """Test that install_bob_mode copies slash command files."""
    install_bob_mode()

    verify_command = temp_project_dir / ".bob" / "commands" / "verify.md"
    assert verify_command.exists()

    # Verify it contains the verify command definition
    content = verify_command.read_text()
    assert "description:" in content
    assert "verdict" in content.lower()


def test_install_bob_mode_preserves_existing_custom_mode(temp_project_dir):
    """Test that install_bob_mode doesn't overwrite existing custom_modes.yaml."""
    bob_dir = temp_project_dir / ".bob"
    bob_dir.mkdir()

    custom_modes_file = bob_dir / "custom_modes.yaml"
    original_content = "# My custom modes\ncustomModes: []"
    custom_modes_file.write_text(original_content)

    install_bob_mode()

    # Should preserve original content
    assert custom_modes_file.read_text() == original_content


def test_install_bob_mode_preserves_existing_slash_command(temp_project_dir):
    """Test that install_bob_mode doesn't overwrite existing slash commands."""
    bob_dir = temp_project_dir / ".bob"
    commands_dir = bob_dir / "commands"
    commands_dir.mkdir(parents=True)

    verify_command = commands_dir / "verify.md"
    original_content = "---\ndescription: My custom verify\n---\nCustom verify command"
    verify_command.write_text(original_content)

    install_bob_mode()

    # Should preserve original content
    assert verify_command.read_text() == original_content


def test_install_bob_mode_idempotent(temp_project_dir):
    """Test that running install_bob_mode multiple times is safe."""
    # First install
    install_bob_mode()

    custom_modes_file = temp_project_dir / ".bob" / "custom_modes.yaml"
    verify_command = temp_project_dir / ".bob" / "commands" / "verify.md"

    first_custom_mode_content = custom_modes_file.read_text()
    first_verify_content = verify_command.read_text()

    # Second install
    install_bob_mode()

    # Content should be unchanged (preserved)
    assert custom_modes_file.read_text() == first_custom_mode_content
    assert verify_command.read_text() == first_verify_content


# Made with Bob