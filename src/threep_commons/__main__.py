"""Module entry point for ``python -m threep_commons``."""

from __future__ import annotations

from . import __version__


def main() -> int:
    """Print the installed package version and exit successfully."""

    print(__version__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
