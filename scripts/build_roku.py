"""Empaqueta el código Roku; no incluye datos operativos ni credenciales."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import sys

root = Path(__file__).resolve().parents[1] / "roku"
target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else root.parent / "dist" / "techtop-itinerarios-roku.zip"
target.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(target, "w", ZIP_DEFLATED) as package:
    for path in sorted(root.rglob("*")):
        if path.is_file():
            package.write(path, path.relative_to(root).as_posix())
print(target)
