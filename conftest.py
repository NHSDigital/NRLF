# pytest configuration file

import os

import pytest
from hypothesis import settings

if os.getenv("RUNNING_IN_CI"):
    settings.register_profile("ci", deadline=1000)  # max 1 second per test
    settings.load_profile("ci")


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
