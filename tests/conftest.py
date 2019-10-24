import pytest
from water.modules.load_data import load_pollution_dynamics


@pytest.fixture(scope='session')
def pollution_data():

    pollution, *_ = load_pollution_dynamics()
    return pollution
