import pytest
from water.modules.load_data import (get_network_examples, get_custom_networks,
                                     get_network_files_path)


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
