import nox

# Python versions available on this machine (no 3.6)
PYTHONS = ["3.7", "3.8", "3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]

nox.options.default_venv_backend = "uv"


@nox.session(python=PYTHONS)
def tests(session: nox.Session):
    """Run the test suite against each Python version."""
    session.install("-e", ".[test]")
    session.install("ruamel.yaml")
    session.run("python", "-m", "pytest", "tests/", "-v", *session.posargs)
