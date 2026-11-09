# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "packaging",
#     "requests",
#     "typer",
# ]
# ///
"""Print minimum supported versions under SPEC 0 or SPEC 0 + 1 year.

A minor series is supported for a window after its initial release: 2 years
for packages and 3 for Python under SPEC 0, or 3 and 5 under SPEC 0 + 1 year.
The floor is the oldest series released in the final year of its window, so a
series is kept until its successor has been out for a year. If no series was
released in that year, the floor is the newest series whose window has closed;
if every window is still open, it is the oldest series.

    uv run floors.py numpy scipy
    uv run floors.py --plus --pyproject path/to/pyproject.toml
"""

from datetime import date
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(add_completion=False)

PYTHON_RELEASES = {
    (3, 10): date(2021, 10, 4),
    (3, 11): date(2022, 10, 24),
    (3, 12): date(2023, 10, 2),
    (3, 13): date(2024, 10, 7),
    (3, 14): date(2025, 10, 7),
    (3, 15): date(2026, 10, 9),
}


def floor(
    releases: dict[tuple[int, int], date], as_of: date, years: int
) -> tuple[int, int]:
    """Return the minimum supported series, given each series' initial release date.

    ``years`` is the support window. A series whose window ends on ``as_of`` is
    no longer supported.
    """
    raise NotImplementedError


def release_dates(package: str) -> dict[tuple[int, int], date]:
    """Return the date of each ``X.Y.0`` final release of a PyPI package."""
    raise NotImplementedError


def requirements(pyproject: Path) -> list[str]:
    """Return the names in ``project.dependencies``, skipping direct references."""
    raise NotImplementedError


@app.command()
def main(
    packages: Annotated[
        list[str] | None, typer.Argument(help="PyPI package names")
    ] = None,
    plus: Annotated[bool, typer.Option(help="Use SPEC 0 + 1 year")] = False,
    as_of: Annotated[
        str | None, typer.Option("--date", help="YYYY-MM-DD; default today")
    ] = None,
    pyproject: Annotated[
        Path | None, typer.Option(help="Read packages from project.dependencies")
    ] = None,
) -> None:
    """Print ``name >= X.Y`` for Python and each package."""
    raise NotImplementedError


if __name__ == "__main__":
    app()
