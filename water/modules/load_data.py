import wntr
import numpy as np
from os.path import dirname, join
import pickle
from statistics import mean


def load_water_network():
    # load .inp file
    filename = join(dirname(__file__), '../data',
                    'kentucky_water_distribution_networks/ky2.inp')

    # Create water network
    wn = wntr.network.WaterNetworkModel(filename)

    # Get the NetworkX graph
    G = wn.get_graph().to_undirected()

    # Add the node name as an attribute, so we can use with tooltips
    # Also add info about the demand and elevation
    # Also add the names of connected nodes and edge names
    # Also get a list of the base demand for each node
    all_base_demands = []
    for node in G.nodes():
        G.nodes[node]['name'] = node
        try:
            G.nodes[node]['elevation'] = (
                wn.query_node_attribute('elevation')[node]
                )
        except KeyError:
            G.nodes[node]['elevation'] = 'N/A'
        try:
            base_demands = []
            # TODO: For some reason this is a list, but in Ky2 data there is
            # only ever a single base demand value
            for timeseries in wn.get_node(node).demand_timeseries_list:
                base_demands.append(timeseries.base_value)
            base_demand = mean(base_demands)
            G.nodes[node]['demand'] = base_demand
            all_base_demands.append(base_demand)
        except AttributeError:
            # Nodes with no demand will not resize from the base_node_size
            all_base_demands.append(0.0)
            G.nodes[node]['demand'] = "N/A"
        pipes = dict(G.adj[node])
        connected_str = ""
        i = 0
        for connected_node, pipe_info in pipes.items():
            if i > 0:
                connected_str = connected_str + "| "
            connected_str = connected_str + connected_node + ": "
            for pipe, info in pipe_info.items():
                connected_str = connected_str + pipe + " "
            i += 1
        G.nodes[node]['connected'] = connected_str

    # Normalise base demands
    # This global variable list is used for node resizing and the demand data
    # is also displayed in the tooltip
    all_base_demands = np.array([float(i) / max(all_base_demands)
                                 for i in all_base_demands])

    # Create plottable coordinates for each network node
    locations = {}
    for node, node_data in G.nodes().items():
        # Adjust the coordinates to roughly lay over Louisville, Kentucky
        xd = node_data['pos'][0] - 13620000
        yd = node_data['pos'][1] + 1170000
        locations[node] = (xd, yd)

    return G, locations, all_base_demands


def load_pollution_dynamics():
    # Load pollution dynamics
    # Create pollution as a global var used in some functions
    filename = join(dirname(__file__), '../data',
                    'kentucky_water_distribution_networks/Ky2.pkl')
    with open(filename, 'rb') as input_file:
        pollution = pickle.load(input_file)

    # Determine max and min pollution values and all scenario names
    max_pols = []
    min_pols = []
    pollution_nodes = []
    for key, df in pollution.items():
        if key != 'chemical_start_time':
            pollution_nodes.append(key)
            v = df.values.ravel()
            max_pols.append(np.max(v))
            min_pols.append(np.min(v[v > 0]))
    max_pol = np.max(max_pols)
    min_pol = np.min(min_pols)

    # Choose a default node for pollution injection
    start_node = pollution_nodes[0]

    # Determine the step numbers for the beginning and end of the pollution
    # data. This assumes all pollution pollution_nodes are identical in time to the
    # default starting node!
    start = pollution[start_node].index.min()
    end = pollution[start_node].index.max()

    # Get the timstep size for the slider from the pollution df
    step = pollution[start_node].index[1] - pollution[start_node].index[0]

    return pollution, pollution_nodes, start_node, start, end, step, max_pol, min_pol
