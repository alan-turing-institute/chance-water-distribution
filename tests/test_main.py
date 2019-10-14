from water.main import pollution_series, pollution

def test_pollution_series():
    assert float(pollution_series(pollution, 'J-1', 42330)[0]) == 6.503378868103027


def test_pollution_series_timestep_doesnt_exist():
    assert pollution_series(pollution, 'J-100', 14)[0] == 0.0


def test_pollution_series_node_doesnt_exist():
    assert pollution_series(pollution, 'X', 42330)[0] == 0.0
