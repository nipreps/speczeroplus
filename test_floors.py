from datetime import date

import pytest
from typer.testing import CliRunner

import floors

AS_OF = date(2026, 11, 8)

# Initial release dates of each minor series, from PyPI
NUMPY = {
    (1, 26): date(2023, 9, 16),
    (2, 0): date(2024, 6, 16),
    (2, 1): date(2024, 8, 18),
    (2, 2): date(2024, 12, 8),
    (2, 3): date(2025, 6, 7),
    (2, 4): date(2025, 12, 20),
    (2, 5): date(2026, 6, 21),
}
NIBABEL = {
    (5, 1): date(2023, 4, 3),
    (5, 2): date(2023, 12, 11),
    (5, 3): date(2024, 10, 8),
    (5, 4): date(2026, 3, 2),
}

# Excerpt of https://pypi.org/pypi/nibabel/json
NIBABEL_JSON = {
    "releases": {
        "4.0.0rc0": [
            {"upload_time": "2022-06-06T14:19:35"},
            {"upload_time": "2022-06-06T14:19:37"},
        ],
        "5.2.0": [
            {"upload_time": "2023-12-11T21:37:41"},
            {"upload_time": "2023-12-11T21:37:43"},
        ],
        "5.2.1": [{"upload_time": "2024-02-27T04:13:17"}],
        "5.3.0": [
            {"upload_time": "2024-10-08T18:24:51"},
            {"upload_time": "2024-10-08T18:24:53"},
        ],
        "5.3.1": [{"upload_time": "2024-10-15T18:57:00"}],
        "5.4.0": [{"upload_time": "2026-03-02T18:12:39"}],
    }
}


class Response:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


@pytest.fixture
def pypi(monkeypatch):
    """Serve captured release dates; tests must not depend on PyPI being reachable."""
    monkeypatch.setattr(
        floors, "release_dates", {"numpy": NUMPY, "nibabel": NIBABEL}.__getitem__
    )


def test_floor_is_oldest_series_in_final_year_of_window():
    assert floors.floor(NUMPY, AS_OF, 2) == (2, 2)
    assert floors.floor(NUMPY, AS_OF, 3) == (2, 0)


def test_floor_keeps_series_until_successor_is_a_year_old():
    # 5.3 is past its window, but 5.4 is only eight months old
    assert floors.floor(NIBABEL, AS_OF, 2) == (5, 3)


def test_floor_drops_series_whose_window_ends_today():
    releases = {(24, 2): date(2024, 11, 8), (25, 0): date(2025, 4, 19)}
    assert floors.floor(releases, AS_OF, 2) == (25, 0)


def test_floor_of_young_package_is_oldest_series():
    releases = {(0, 1): date(2026, 2, 1), (0, 2): date(2026, 9, 1)}
    assert floors.floor(releases, AS_OF, 2) == (0, 1)


def test_python_floor():
    assert floors.floor(floors.PYTHON_RELEASES, AS_OF, 3) == (3, 13)
    assert floors.floor(floors.PYTHON_RELEASES, AS_OF, 5) == (3, 11)


def test_release_dates_keep_initial_final_releases(monkeypatch):
    # Serve a captured response; tests must not depend on PyPI being reachable
    urls = []
    monkeypatch.setattr(
        floors.requests,
        "get",
        lambda url, **kw: urls.append(url) or Response(NIBABEL_JSON),
    )
    assert floors.release_dates("nibabel") == {
        (5, 2): date(2023, 12, 11),
        (5, 3): date(2024, 10, 8),
        (5, 4): date(2026, 3, 2),
    }
    assert urls == ["https://pypi.org/pypi/nibabel/json"]


def test_requirements_skips_direct_references(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """\
[project]
name = "example"
dependencies = [
    "numpy >= 2.0",
    "nibabel",
    "niworkflows @ git+https://github.com/nipreps/niworkflows@master",
    "scipy[test] >= 1.13; python_version >= '3.12'",
]
"""
    )
    assert floors.requirements(pyproject) == ["numpy", "nibabel", "scipy"]


def test_cli_prints_spec0_floors(pypi):
    result = CliRunner().invoke(
        floors.app, ["--date", "2026-11-08", "numpy", "nibabel"]
    )
    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        "python >= 3.13",
        "numpy >= 2.2",
        "nibabel >= 5.3",
    ]


def test_cli_plus_reads_pyproject(pypi, tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "example"\ndependencies = ["numpy >= 1.25", "nibabel"]\n'
    )
    result = CliRunner().invoke(
        floors.app, ["--plus", "--date", "2026-11-08", "--pyproject", str(pyproject)]
    )
    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        "python >= 3.11",
        "numpy >= 2.0",
        "nibabel >= 5.2",
    ]


def test_release_dates_skip_legacy_versions(monkeypatch):
    # Excerpt of https://pypi.org/pypi/pytz/json; 2004d is not a valid version.
    # Serve a captured response; tests must not depend on PyPI being reachable
    data = {
        "releases": {
            "2004d": [{"upload_time": "2013-10-01T15:26:28"}],
            "2024.1": [{"upload_time": "2024-02-02T01:18:37"}],
            "2025.1": [{"upload_time": "2025-01-31T01:54:45"}],
        }
    }
    monkeypatch.setattr(floors.requests, "get", lambda url, **kw: Response(data))
    assert floors.release_dates("pytz") == {
        (2024, 1): date(2024, 2, 2),
        (2025, 1): date(2025, 1, 31),
    }
