# Developer Notes

These are notes to help me (and other contributors) remember how to set up the project and do common tasks.

## Build Tool

This project uses [Flit](https://flit.readthedocs.io/en/latest/).  It is a simple build tool that uses `pyproject.toml` to define the project.

## Installing

- Create a virtual environment and activate it
- `pip install flit`
- `flit install`

## Testing

Testing uses pytest. Use --doctest-glob to include the README.md file.

- `pytest --doctest-glob="*.md"`

## Building

- `rm -rf dist && rm -rf build`
- `flit build`

## Publishing

- `flit publish`

## Documentation

Docs are built and deployed with mkdocs:

- `mkdocs build`
- `mkdocs gh-deploy`

Use `mkdocs serve` to test locally.
