from water.main import get_pollution_values
from water.main import get_node_sizes


def test_get_pollution_values():
    assert(get_pollution_values('J-1', 42330)[0], 6.503379)


def test_get_pollution_values_timestep_doesnt_exist():
    assert(get_pollution_values('J-100', 14)[0], 0.0)


# def test_get_node_sizes():
#     assert(get_node_sizes())
