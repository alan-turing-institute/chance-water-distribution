import pytest
from water.modules.load_data import (get_network_examples, get_custom_networks,
                                     get_network_files_path, load_water_network,
                                     load_pollution_dynamics)


def test_get_network_examples():
    assert get_network_examples() == ['ky14', 'ky2', 'ky4', 'ky8', 'ky9']


if len(get_custom_networks()) > 0:
    @pytest.mark.parametrize('network', get_custom_networks())
    def test_get_custom_networks(network):
        """By default, there should be no custom networks. If there are, check
        that there is a pollution file present for every node in the network,
        with the exception of tanks and reservoirs"""
        _, injection_nodes, *_ = load_pollution_dynamics(network)
        networkx_graph, *_ = load_water_network(network)
        graph_nodes = []
        for node in networkx_graph.nodes():
            type = networkx_graph.nodes[node]['type']
            if type != 'Tank' and type != 'Reservoir':
                graph_nodes.append(node)
        injection_nodes.sort()
        graph_nodes.sort()
        assert injection_nodes == graph_nodes


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
