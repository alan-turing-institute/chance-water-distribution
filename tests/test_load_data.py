import pytest
from water.modules.load_data import (get_network_examples, get_custom_networks,
                                     get_network_files_path, load_water_network,
                                     load_pollution_dynamics)


def test_get_network_examples():
    assert get_network_examples() == ['ky14', 'ky2', 'ky4', 'ky8', 'ky9']


def test_get_custom_networks():
    """By default, there should be no custom networks"""
    assert get_custom_networks() == []


def test_get_network_files_path_bad_network():
    """Check exception raised for bad network name"""
    with pytest.raises(Exception):
        get_network_files_path('bad network name')


def test_get_network_files_path_ky2_example_network():
    """Check path created for known example"""
    assert 'data/examples/ky2' in get_network_files_path('ky2')


def test_load_water_network_bad_network():
    """Check that the error raised by providing a bad network name to
    get_network_files_path() also stops load_water_network()"""
    with pytest.raises(Exception):
        load_water_network('bad network name')


def test_load_pollution_dynamics_bad_network():
    """Check that the error raised by providing a bad network name to
    get_network_files_path() also stops load_pollution_dynamics()"""
    with pytest.raises(Exception):
        load_pollution_dynamics('bad network name')
