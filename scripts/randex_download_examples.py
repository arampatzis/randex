"""Download the latest examples from GitHub."""

import io
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from urllib.error import URLError

GITHUB_ZIP_URL = "https://github.com/arampatzis/randex/archive/refs/heads/main.zip"
DEST_DIR = Path("examples")


def main() -> None:
    """Download the latest examples from GitHub."""
    print("📦 Downloading examples from GitHub...")

    if DEST_DIR.exists():
        print(
            f"❌ Destination folder '{DEST_DIR}' already exists. "
            "Please remove it first."
        )
        sys.exit(1)

    try:
        with (
            urllib.request.urlopen(GITHUB_ZIP_URL) as response,  # noqa: S310
            zipfile.ZipFile(io.BytesIO(response.read())) as zip_ref,
        ):
            temp_dir = Path(tempfile.mkdtemp())
            zip_ref.extractall(temp_dir)

            # Detect the root folder inside the zip (e.g., randex-main)
            root_entry = next((p for p in temp_dir.iterdir() if p.is_dir()), None)

            if not root_entry:
                print("❌ Could not locate the root folder in the archive.")
                sys.exit(1)

            examples_path = root_entry / "examples"

            if not examples_path.exists():
                print("❌ examples/ folder not found in the downloaded repository.")
                sys.exit(1)

            shutil.copytree(examples_path, DEST_DIR)
            print(f"✅ Examples downloaded to: {DEST_DIR.resolve()}")

    except (URLError, zipfile.BadZipFile, OSError, shutil.Error) as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
