"""Allow ``python -m ooos`` as well as ``python -m ooos.boot``."""

from .boot import main

if __name__ == "__main__":
    raise SystemExit(main())
