import pytest
from water.modules.pollution import pollution_series, pollution_scenario


def test_pollution_series(pollution_data):
    pollution = pollution_data
    scenario = pollution_scenario(pollution, 'J-1')
    assert (pollution_series(scenario, 42330)[0]
            == pytest.approx(6.503378868103027))


def test_pollution_series_timestep_doesnt_exist(pollution_data):
    pollution = pollution_data
    scenario = pollution_scenario(pollution, 'J-100')
    assert pollution_series(scenario, 14)[0] == 0.0


def test_pollution_series_node_doesnt_exist(pollution_data):
    pollution = pollution_data
    with pytest.raises(KeyError):
        pollution_scenario(pollution, 'X')
