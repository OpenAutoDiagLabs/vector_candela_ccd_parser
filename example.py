"""Quick start: load a CDD file and print the default request of the first few services.

Usage:
    python example.py path/to/file.cdd
"""
import sys

from cdd import load_cdd


def format_hex(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data) if data else "(empty)"


if __name__ == "__main__":
    db = load_cdd(sys.argv[1], strict=False)
    print(db)
    for svc in [s for s in db.services if s.is_used][:10]:
        print(f"{svc.qualifier:50} {format_hex(svc.request.encode_default())}")
