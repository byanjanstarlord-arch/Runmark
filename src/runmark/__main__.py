"""Entrypoint for `python -m runmark`."""

import sys

from runmark.cli.app import main

if __name__ == "__main__":
    sys.exit(main())
