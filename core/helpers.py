from pathlib import Path
from dotenv import load_dotenv

def load_env():
    load_dotenv()

def ensure_outdirs(root="out"):
    Path(root).mkdir(parents=True, exist_ok=True)
    Path(root, "debug").mkdir(parents=True, exist_ok=True)
    Path(root, "merged").mkdir(parents=True, exist_ok=True)
