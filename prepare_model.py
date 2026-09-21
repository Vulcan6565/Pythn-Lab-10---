"""Check or download the official small English Vosk model."""

from pathlib import Path
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile


BASE_DIR = Path(__file__).resolve().parent
MODEL_NAME = "vosk-model-small-en-us-0.15"
MODEL_DIR = BASE_DIR / MODEL_NAME
MODEL_URL = "https://alphacephei.com/vosk/models/" + MODEL_NAME + ".zip"
MODEL_FILES = [
    "am/final.mdl", "conf/mfcc.conf", "conf/model.conf",
    "graph/Gr.fst", "graph/HCLr.fst", "graph/disambig_tid.int",
    "graph/phones/word_boundary.int", "ivector/final.dubm",
    "ivector/final.ie", "ivector/final.mat", "ivector/global_cmvn.stats",
    "ivector/online_cmvn.conf", "ivector/splice.conf"
]


def model_is_ready(directory=MODEL_DIR):
    for name in MODEL_FILES:
        path = directory / name
        if not path.is_file() or path.stat().st_size == 0:
            return False
    return True


def main():
    if "--check" in sys.argv:
        return 0 if model_is_ready() else 1

    if model_is_ready():
        print("The speech model is ready:", MODEL_DIR)
        return 0

    print("Downloading the official English speech model (about 40 MB)...")
    try:
        # Extract into a temporary folder first; a failed download is not a model.
        with tempfile.TemporaryDirectory(prefix="model_download_", dir=BASE_DIR) as folder:
            temp_dir = Path(folder)
            zip_path = temp_dir / "model.zip"
            with urllib.request.urlopen(MODEL_URL, timeout=60) as response:
                with zip_path.open("wb") as file:
                    shutil.copyfileobj(response, file)

            with zipfile.ZipFile(zip_path) as archive:
                for entry in archive.infolist():
                    parts = entry.filename.replace("\\", "/").split("/")
                    if parts[0] != MODEL_NAME or ".." in parts or ":" in entry.filename:
                        raise ValueError("Unexpected file in the model archive.")
                archive.extractall(temp_dir)

            downloaded_model = temp_dir / MODEL_NAME
            if not model_is_ready(downloaded_model):
                raise ValueError("The downloaded speech model is incomplete.")
            shutil.copytree(downloaded_model, MODEL_DIR, dirs_exist_ok=True)

        print("The speech model is ready:", MODEL_DIR)
        return 0
    except (OSError, ValueError, urllib.error.URLError, zipfile.BadZipFile) as error:
        print("Could not prepare the speech model:", error)
        print("Check your internet connection, then run START_LAB.bat again.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
