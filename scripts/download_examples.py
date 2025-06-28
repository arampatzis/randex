"""Download the latest examples from GitHub."""

import io
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from urllib.error import URLError

from randex.cli import get_logger

logger = get_logger(__name__)

GITHUB_ZIP_URL = "https://github.com/arampatzis/randex/archive/refs/heads/main.zip"
DEST_DIR = Path("examples")


def main() -> None:
    """Download the latest examples from GitHub."""
    logger.info("📦 Downloading examples from GitHub...")

    if DEST_DIR.exists():
        logger.error(
            "❌ Destination folder '%s' already exists. Please remove it first."
        )
        sys.exit(1)

    try:
        logger.debug("🌐 Fetching from: %s", GITHUB_ZIP_URL)
        with (
            urllib.request.urlopen(GITHUB_ZIP_URL) as response,  # noqa: S310
            zipfile.ZipFile(io.BytesIO(response.read())) as zip_ref,
        ):
            temp_dir = Path(tempfile.mkdtemp())
            logger.debug("📁 Extracting to temporary directory: %s", temp_dir)
            zip_ref.extractall(temp_dir)

            # Detect the root folder inside the zip (e.g., randex-main)
            root_entry = next((p for p in temp_dir.iterdir() if p.is_dir()), None)

            if not root_entry:
                logger.error("❌ Could not locate the root folder in the archive.")
                sys.exit(1)

            examples_path = root_entry / "examples"
            logger.debug("🔍 Looking for examples in: %s", examples_path)

            if not examples_path.exists():
                logger.error(
                    "❌ examples/ folder not found in the downloaded repository."
                )
                sys.exit(1)

            logger.debug("📂 Copying examples from %s to %s", examples_path, DEST_DIR)
            shutil.copytree(examples_path, DEST_DIR)
            logger.info("✅ Examples downloaded to: %s", DEST_DIR.resolve())

    except (URLError, zipfile.BadZipFile, OSError, shutil.Error):
        logger.exception("❌ Error occurred during the download process.")
        sys.exit(1)
