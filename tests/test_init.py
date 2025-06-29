"""Tests for the randex package initialization."""

import sys
from unittest.mock import patch

import randex


class TestPackageVersion:
    """Test package version handling."""

    def test_version_available(self) -> None:
        """Test that version is available when package is installed."""
        # Version should be available
        assert hasattr(randex, "__version__")
        assert isinstance(randex.__version__, str)
        assert len(randex.__version__) > 0

    def test_version_import_error(self) -> None:
        """Test fallback version when importlib.metadata fails."""
        # Remove randex from sys.modules if it exists, so we can reimport it
        if "randex" in sys.modules:
            del sys.modules["randex"]

        # Mock importlib.metadata.version to raise ImportError
        with patch(
            "importlib.metadata.version", side_effect=ImportError("Package not found")
        ):
            # Now import randex, which should trigger the except block
            import randex  # noqa: PLC0415

            # Should fall back to "0.0.0"
            assert randex.__version__ == "0.0.0"
