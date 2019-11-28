import pytest
from water.modules.load_data import get_network_examples, get_custom_networks


def test_get_network_examples():
    assert get_network_examples() == ['ky14', 'ky2', 'ky4', 'ky8', 'ky9']


def test_get_custom_networks():
    """By default, there should be no custom networks"""
    assert get_custom_networks() == []
