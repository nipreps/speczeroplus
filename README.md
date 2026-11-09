# SPEC0+

The Scientific Python Ecosystem Coordination (SPEC) mechanism is used to recommend
project policies, coding conventions, and standard tooling.

This project extends [SPEC 0](https://scientific-python.org/specs/spec-0000/) to
consider other support windows.
The neuroimaging community in particular is slower moving than much of the scientific
Python community, and so SPEC0+1yr is a relatively common convention for core libraries.

See https://scientific-python.org/specs/ for a list of SPECs and their statuses.

## Lower bounds for a project

`floors.py` prints the minimum supported version of Python and of each package:

```console
$ uv run floors.py numpy nibabel
python >= 3.13
numpy >= 2.2
nibabel >= 5.3
$ uv run floors.py --plus --pyproject path/to/pyproject.toml
```

`--plus` uses SPEC0+1yr; `--date YYYY-MM-DD` computes the bounds for another day.
A minor series is kept until its successor has been out for a year, so the floor
is the oldest series released in the final year of its support window, or else
the newest series whose window has closed.

Run the tests with:

```console
$ uv run --with pytest --with packaging --with requests --with typer pytest test_floors.py
```
