import wntr
import numpy as np
from os import listdir
from os.path import dirname, join, isdir
import pickle
from statistics import mean
import yaml


def get_network_examples():
    examples = []
    dir = join(dirname(__file__), '../data',
               'examples/')
    for filename in listdir(dir):
        if isdir(join(dir, filename)):
            examples.append(filename)
    examples.sort()
    return examples


def load_water_network(network):
    # load .inp file
    filename = join(dirname(__file__), '../data',
                    'examples/' + network + '/' + network + '.inp')

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
            # TODO: For some reason this is a list, but in Kentucky 2
            # data there is only ever a single base demand value
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
    # Adjust the coordinates if specified by metadata file
    try:
        metadata_file = join(dirname(__file__), '../data', 'examples/'
                                                + network
                                                + '/metadata.yml')
        with open(metadata_file, 'r') as stream:
            metadata = yaml.safe_load(stream)
            x_offset = metadata['x_offset']
            y_offset = metadata['y_offset']
    except FileNotFoundError:
        x_offset = 0
        y_offset = 0

    locations = {}
    for node, node_data in G.nodes().items():
        xd = node_data['pos'][0] + x_offset
        yd = node_data['pos'][1] + y_offset
        locations[node] = (xd, yd)

    return G, locations, all_base_demands


def load_pollution_dynamics(network):
    # Load pollution dynamics
    # Create pollution as a global var used in some functions
    files = join(dirname(__file__), '../data',
                 'examples/' + network + '/' + network + '')
    # Determine max and min pollution values and all node names
    max_pols = []
    min_pols = []
    injection_nodes = []
    pollution = {}
    for filename in listdir(files):
        if filename.endswith(".pkl"):
            node_name = filename.split(".pkl")[0]
            injection_nodes.append(node_name)
            with open(files + "/" + filename, 'rb') as input_file:
                pollution_df = pickle.load(input_file)
                pollution[node_name] = pollution_df
                v = pollution_df.values.ravel()
                max_pols.append(np.max(v))
                try:  # below will error for a df where all values zero
                    min_pols.append(np.min(v[v > 0]))
                except ValueError:
                    min_pols.append(0)

    max_pol = np.max(max_pols)
    min_pol = np.min(min_pols)
    injection_nodes.sort()

    # Choose a default node for pollution injection
    start_node = injection_nodes[0]

    # Determine the step numbers for the beginning and end of the pollution
    # data. This assumes all injection_nodes are identical in time
    # to the default starting node!
    start = pollution[start_node].index.min()
    end = pollution[start_node].index.max()

    # Get the timstep size for the slider from the pollution df
    step = pollution[start_node].index[1] - pollution[start_node].index[0]

    return (pollution, injection_nodes, start_node, start, end, step,
            max_pol, min_pol)
