set windows-powershell := true


# Show this help
@help:
  just --list --list-submodules


# Set up dev environments
install:
  poetry install
  pre-commit install


# Run the pre-commit hooks
hooks:
  pre-commit run --all-files


# Run pluraldo
pdo *ARGS:
  poetry run pluraldo {{ARGS}}


# Run mypy
types:
  poetry run mypy src
