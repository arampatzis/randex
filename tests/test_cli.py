"""Tests for the CLI utilities module."""

import logging
import sys
from unittest.mock import MagicMock, patch

import click

from randex.cli import CustomCommand, get_logger, setup_logging


class TestSetupLogging:
    """Test the setup_logging function."""

    def test_setup_logging_default(self) -> None:
        """Test default logging setup (INFO level)."""
        setup_logging()

        logger = logging.getLogger()
        assert logger.level == logging.INFO

        # Should have one handler
        assert len(logger.handlers) == 1
        handler = logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert handler.stream == sys.stdout

    def test_setup_logging_verbose(self) -> None:
        """Test logging setup with verbose=1 (DEBUG level)."""
        setup_logging(verbose=1)

        logger = logging.getLogger()
        assert logger.level == logging.DEBUG

    def test_setup_logging_very_verbose(self) -> None:
        """Test logging setup with verbose=2 (DEBUG with detailed format)."""
        setup_logging(verbose=2)

        logger = logging.getLogger()
        assert logger.level == logging.DEBUG

        # Should have detailed formatter
        handler = logger.handlers[0]
        formatter = handler.formatter
        assert "[%(levelname)s] %(name)s:" in formatter._fmt

    def test_setup_logging_quiet(self) -> None:
        """Test logging setup with quiet=True (WARNING level)."""
        setup_logging(quiet=True)

        logger = logging.getLogger()
        assert logger.level == logging.WARNING

    def test_setup_logging_removes_existing_handlers(self) -> None:
        """Test that setup_logging removes existing handlers."""
        logger = logging.getLogger()

        # Add a dummy handler
        dummy_handler = logging.StreamHandler()
        logger.addHandler(dummy_handler)
        len(logger.handlers)

        # Setup logging should remove all existing handlers and add one new
        setup_logging()

        assert len(logger.handlers) == 1
        assert dummy_handler not in logger.handlers


class TestGetLogger:
    """Test the get_logger function."""

    def test_get_logger_with_name(self) -> None:
        """Test getting logger with explicit name."""
        logger = get_logger("test_logger")

        assert logger.name == "test_logger"
        assert isinstance(logger, logging.Logger)

    def test_get_logger_without_name(self) -> None:
        """Test getting logger without explicit name (should use calling module)."""
        logger = get_logger()

        # Should get logger with module name
        assert isinstance(logger, logging.Logger)
        # The name should be either the current module name or 'randex' as fallback
        assert logger.name in ("tests.test_cli", "randex")

    @patch("inspect.currentframe")
    def test_get_logger_no_frame(self, mock_currentframe: MagicMock) -> None:
        """Test get_logger when no frame is available."""
        mock_currentframe.return_value = None

        logger = get_logger()

        assert logger.name == "randex"

    @patch("inspect.currentframe")
    def test_get_logger_no_back_frame(self, mock_currentframe: MagicMock) -> None:
        """Test get_logger when back frame is not available."""
        mock_frame = MagicMock()
        mock_frame.f_back = None
        mock_currentframe.return_value = mock_frame

        logger = get_logger()

        assert logger.name == "randex"

    @patch("inspect.currentframe")
    def test_get_logger_no_module_name(self, mock_currentframe: MagicMock) -> None:
        """Test get_logger when module name is not available."""
        mock_back_frame = MagicMock()
        mock_back_frame.f_globals = {}  # No __name__ key
        mock_frame = MagicMock()
        mock_frame.f_back = mock_back_frame
        mock_currentframe.return_value = mock_frame

        logger = get_logger()

        assert logger.name == "randex"


class TestCustomCommand:
    """Test the CustomCommand class."""

    def test_custom_command_normal_parsing(self) -> None:
        """Test CustomCommand with normal argument parsing."""

        @click.command(cls=CustomCommand)
        @click.argument("folder")
        def test_cmd(folder: str) -> None:
            click.echo(f"Folder: {folder}")

        runner = click.testing.CliRunner()
        result = runner.invoke(test_cmd, ["test_folder"])

        assert result.exit_code == 0
        assert "Folder: test_folder" in result.output

    def test_custom_command_multiple_arguments_error(self) -> None:
        """Test CustomCommand with multiple unexpected arguments."""

        @click.command(cls=CustomCommand)
        @click.argument("folder")
        def test_cmd(folder: str) -> None:
            click.echo(f"Folder: {folder}")

        runner = click.testing.CliRunner()
        result = runner.invoke(test_cmd, ["folder1", "folder2", "folder3"])

        assert result.exit_code != 0
        assert "Multiple folder arguments detected" in result.output
        assert "folder2 folder3" in result.output  # Only extra arguments are shown
        assert "Put quotes around your glob pattern" in result.output

    def test_custom_command_other_usage_error(self) -> None:
        """Test CustomCommand with other types of usage errors."""

        @click.command(cls=CustomCommand)
        @click.option("--required", required=True)
        def test_cmd(required: str) -> None:
            click.echo(f"Required: {required}")

        runner = click.testing.CliRunner()
        result = runner.invoke(test_cmd, [])

        assert result.exit_code != 0
        # Should re-raise the original error for non-multiple-argument cases
        assert "Missing option" in result.output or "required" in result.output.lower()
