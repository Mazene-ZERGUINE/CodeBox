from pathlib import Path
import shutil
from django.conf import settings


def purge_storage():
    for rel in ("storage/in", "storage/out"):
        p = Path(settings.BASE_DIR) / rel
        if p.exists():
            for child in p.iterdir():
                if child.is_file():
                    child.unlink(missing_ok=True)
                elif child.is_dir():
                    shutil.rmtree(child, ignore_errors=True)
