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

import tomllib
from datetime import date, timedelta
from pathlib import Path
from typing import Annotated

import requests
import typer
from packaging.requirements import Requirement
from packaging.version import InvalidVersion, Version

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
    closes = as_of - timedelta(days=365 * years)
    final_year = [
        s for s, d in releases.items() if closes < d <= closes + timedelta(days=365)
    ]
    if final_year:
        return min(final_year, key=releases.get)
    closed = [s for s, d in releases.items() if d <= closes]
    if closed:
        return max(closed, key=releases.get)
    return min(releases, key=releases.get)


def release_dates(package: str) -> dict[tuple[int, int], date]:
    """Return the date of each ``X.Y.0`` final release of a PyPI package."""
    response = requests.get(f"https://pypi.org/pypi/{package}/json", timeout=30)
    response.raise_for_status()
    dates = {}
    for ver, files in response.json()["releases"].items():
        try:
            version = Version(ver)
        except InvalidVersion:
            continue
        if not files or version.is_prerelease or version.micro != 0:
            continue
        series = (version.major, version.minor)
        released = min(date.fromisoformat(f["upload_time"][:10]) for f in files)
        dates[series] = min(released, dates.get(series, released))
    return dates


def requirements(pyproject: Path) -> list[str]:
    """Return the names in ``project.dependencies``, skipping direct references."""
    deps = tomllib.loads(pyproject.read_text())["project"]["dependencies"]
    return [req.name for req in map(Requirement, deps) if req.url is None]


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
    today = date.fromisoformat(as_of) if as_of else date.today()
    names = [*(packages or []), *(requirements(pyproject) if pyproject else [])]
    python_years, package_years = (5, 3) if plus else (3, 2)
    major, minor = floor(PYTHON_RELEASES, today, python_years)
    typer.echo(f"python >= {major}.{minor}")
    for name in names:
        major, minor = floor(release_dates(name), today, package_years)
        typer.echo(f"{name} >= {major}.{minor}")


if __name__ == "__main__":
    app()
