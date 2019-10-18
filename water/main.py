from bokeh.io import curdoc
from bokeh.events import Tap
from bokeh.layouts import row, column
from bokeh.models.graphs import from_networkx, NodesAndLinkedEdges
from bokeh.models import (Range1d, MultiLine, Circle, HoverTool, Slider,
                          Button, ColorBar, LogTicker, Title, TapTool)
from bokeh.models.widgets import Dropdown, MultiSelect
from bokeh.plotting import figure
from bokeh.tile_providers import get_provider, Vendors
from bokeh.transform import log_cmap
from collections import defaultdict
import colorcet as cc
import datetime
import numpy as np
from os.path import dirname, join
import pandas as pd
import pickle
from statistics import mean
import wntr

callback_id = None
base_node_size = 8
node_demand_weighting = 15

# Labels for the play/pause button in paused and playing states respectively
BUTTON_LABEL_PAUSED = '► Start Pollution'
BUTTON_LABEL_PLAYING = '❚❚ Pause'

# Colors below also used by buttons; update in CSS too on change
# Color of injection node
injection_color = "#34c3eb"  # Light blue

# Color of selected node
node_selection_color = "#07db1c"  # Bright green

# Color of highlighted node type
node_type_highlight_color = 'purple'

# List of clicked node indices
nodes_clicked_ints = []

def pollution_series(pollution, injection, timestep):
    """
    Produce a pandas series of the pollution for each node for a given
    injection site and timestep.

    If the timestep has no pollution data a series of zeroes is returned.

    Args:
        pollution (dict): A dictionary of the pollution dynamics as produced by
            wntr. The keys are injection sites and the values are a Pandas
            Dataframe describing the pollution dynamics.  The columns of the
            Dataframe are the node labels and the index is a set of timesteps.
        injection (str): The node label of the injection site.
        timestep (int): The time step.

    Returns:
        Pandas.Series: The pollution value at each node for the given timestep
            and injection location.
    """
    # Get pollution dataframe for the given injection site
    dataframe = pollution[injection]
    # Extract the pollution series at the given timestep
    if timestep in dataframe.index:
        series = dataframe.loc[timestep]
    else:
        # Construct a series of zero pollution
        series = pd.Series(dict(zip(pollution[injection].columns,
                                    [0]*G.number_of_nodes())))

    return series


def get_node_sizes(base_node_size, node_demand_weighting):
    """Get a list of sizes to set all the nodes in the network by"""
    return [(i * node_demand_weighting)
            + base_node_size for i in all_base_demands]


def get_node_outlines(injection, node_highlight=None, type_highlight=None):
    """Get the color and width for each node in the graph.
    These should be the same in every case except for the
    pollution start node and a chosen node to highlight if provided"""
    # Create a default dictionary for node types, any node with a type not in
    # the dictionary gets the default color
    colors = defaultdict(lambda: "magenta")
    colors.update({
        'Junction': ('gray', 1),
        'Reservoir': ('orange', 2),
        'Tank': ('green', 2),
        })

    outline_colors = []
    outline_widths = []
    node_index_counter = 0
    for node in G.nodes():
        if node == injection:
            outline_colors.append(injection_color)
            outline_widths.append(3)
        elif node == node_highlight or node_index_counter in nodes_clicked_ints:
            outline_colors.append(node_selection_color)
            outline_widths.append(3)
        else:
            node_type = G.node[node]['type']
            if node_type == type_highlight:
                outline_colors.append(node_type_highlight_color)
                outline_widths.append(2)
            else:
                outline_colors.append(colors[node_type][0])
                outline_widths.append(colors[node_type][1])
        node_index_counter += 1


    return outline_colors, outline_widths


def update_colors(attrname, old, new):
    """Update the appearance of the pollution dynamics network, including node
    and edge colors"""
    # Get injection node
    start_node = pollution_location_dropdown.value
    node_highlight = node_highlight_dropdown.value
    type_highlight = node_type_dropdown.value
    timestep = slider.value
    # Get pollution for each node for the given injection site and timestep
    series = pollution_series(pollution, start_node, timestep)

    # Set node outlines
    data = graph.node_renderer.data_source.data
    lines = get_node_outlines(start_node, node_highlight, type_highlight)
    source.data['line_color'], source.data['line_width'] = lines

    # Set the status text
    timer.text = ("Pollution Spread from " + start_node + ";  Time - "
                  + str(datetime.timedelta(seconds=int(timestep))))

    # Update node colours
    source.data['colors'] = list(series)

    # Update edge colours
    edge_values = []
    for node1, node2 in G.edges():
        node1_pollution = series[node1]
        node2_pollution = series[node2]
        edge_values.append((node1_pollution + node2_pollution) / 2.)
    graph.edge_renderer.data_source.data['colors'] = edge_values


def update_node_highlight(attrname, old, new):
    """Highlight a chosen node"""
    start_node = pollution_location_dropdown.value
    node_highlight = node_highlight_dropdown.value
    type_highlight = node_type_dropdown.value
    lines = get_node_outlines(start_node, node_highlight, type_highlight)
    source.data['line_color'], source.data['line_width'] = lines


def update_node_sizes(attrname, old, new):
    """Update the sizes of the nodes in the graph"""
    source.data['size'] = get_node_sizes(
        node_size_slider.value, demand_weight_slider.value)


def animate_update_colors():
    """Move the slider by one step"""
    timestep = slider.value + step_pol
    if timestep > end_pol:
        timestep = start_pol
    slider.value = timestep


def animate():
    """Move the slider every 30 milliseconds on play button click"""
    global callback_id
    global animation_speed
    if play_button.label == BUTTON_LABEL_PAUSED:
        play_button.label = BUTTON_LABEL_PLAYING
        callback_id = curdoc().add_periodic_callback(animate_update_colors,
                                                     animation_speed)
    elif play_button.label == BUTTON_LABEL_PLAYING:
        play_button.label = BUTTON_LABEL_PAUSED
        curdoc().remove_periodic_callback(callback_id)


def update_speed(attr, old, new):
    """Adjust the animation speed"""
    global callback_id
    global animation_speed

    # Update animation speed
    animation_speed = speeds[speed_dropdown.value]

    # If animation is playing recreate the periodic callback
    if play_button.label == BUTTON_LABEL_PLAYING:
        curdoc().remove_periodic_callback(callback_id)
        callback_id = curdoc().add_periodic_callback(animate_update_colors,
                                                     animation_speed)


def node_click(event):
    """Highlight the clicked node and set as pollution start if data exists"""
    global nodes_clicked_ints
    nodes_clicked_ints = source.selected.indices
    start_node = pollution_location_dropdown.value
    lines = get_node_outlines(start_node)
    source.data['line_color'], source.data['line_width'] = lines


def load_water_network():
    # load .inp file
    filename = join(dirname(__file__), 'data',
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
        G.node[node]['name'] = node
        try:
            G.node[node]['elevation'] = (
                wn.query_node_attribute('elevation')[node]
                )
        except KeyError:
            G.node[node]['elevation'] = 'N/A'
        try:
            base_demands = []
            # TODO: For some reason this is a list, but in Ky2 data there is
            # only ever a single base demand value
            for timeseries in wn.get_node(node).demand_timeseries_list:
                base_demands.append(timeseries.base_value)
            base_demand = mean(base_demands)
            G.node[node]['demand'] = base_demand
            all_base_demands.append(base_demand)
        except AttributeError:
            # Nodes with no demand will not resize from the base_node_size
            all_base_demands.append(0.0)
            G.node[node]['demand'] = "N/A"
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
        G.node[node]['connected'] = connected_str

    # Normalise base demands
    # This global variable list is used for node resizing and the demand data
    # is also displayed in the tooltip
    all_base_demands = [float(i) / max(all_base_demands)
                        for i in all_base_demands]

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
    filename = join(dirname(__file__), 'data',
                    'kentucky_water_distribution_networks/Ky2.pkl')
    with open(filename, 'rb') as input_file:
        pollution = pickle.load(input_file)

    # Determine max and min pollution values and all scenario names
    max_pols = []
    min_pols = []
    scenarios = []
    for key, df in pollution.items():
        if key != 'chemical_start_time':
            scenarios.append(key)
            v = df.values.ravel()
            max_pols.append(np.max(v))
            min_pols.append(np.min(v[v > 0]))
    max_pol = np.max(max_pols)
    min_pol = np.min(min_pols)

    # Choose a default node for pollution injection
    start_node = scenarios[0]

    # Determine the step numbers for the beginning and end of the pollution
    # data. This assumes all pollution scenarios are identical in time to the
    # default starting node!
    start = pollution[start_node].index.min()
    end = pollution[start_node].index.max()

    # Get the timstep size for the slider from the pollution df
    step = pollution[start_node].index[1] - pollution[start_node].index[0]

    return pollution, scenarios, start_node, start, end, step, max_pol, min_pol


def plot_bounds(locations):
    # Get lists of node locations
    xs = [coord[0] for coord in locations.values()]
    ys = [coord[1] for coord in locations.values()]

    # Find minimum and maximum coordinates
    x_max, x_min = max(xs), min(xs)
    y_max, y_min = max(ys), min(ys)

    # Add padding to boundary
    x_extra_range = (x_max - x_min) / 20
    y_extra_range = (y_max - y_min) / 20

    x_lower = x_min - x_extra_range
    x_upper = x_max + x_extra_range
    y_lower = y_min - y_extra_range
    y_upper = y_max + y_extra_range

    return Range1d(x_lower, x_upper), Range1d(y_lower, y_upper)


G, locations, all_base_demands = load_water_network()

(pollution, scenarios, start_node, start_pol, end_pol, step_pol,
 max_pol, min_pol) = load_pollution_dynamics()

# Get pollution values for time zero
pollution_values = list(pollution_series(pollution, start_node, 0))

# Create figure object
x_bounds, y_bounds = plot_bounds(locations)
plot = figure(x_range=x_bounds, y_range=y_bounds, active_scroll='wheel_zoom',
              x_axis_type="mercator", y_axis_type="mercator")

# Add map to plot
tile_provider = get_provider(Vendors.CARTODBPOSITRON)
plot.add_tile(tile_provider)

# Add a timer label under plot
timer = Title(text_font_size='35pt', text_color='grey')
plot.add_layout(timer, 'below')

# Create bokeh graph from the NetworkX object
graph = from_networkx(G, locations)

# Define color map for pollution
color_mapper = log_cmap('colors', cc.CET_L18, min_pol, max_pol)

# Create nodes, set the node colors by pollution level and size by base demand
# Node outline color and thickness is different for the pollution start node
source = graph.node_renderer.data_source
source.data['colors'] = pollution_values
source.data['size'] = get_node_sizes(base_node_size, node_demand_weighting)
source.data['line_color'], source.data['line_width'] = get_node_outlines(start_node)
graph.node_renderer.glyph = Circle(size="size", fill_color=color_mapper,
                                   line_color="line_color",
                                   line_width="line_width")

# Add color bar as legend
color_bar = ColorBar(color_mapper=color_mapper['transform'],
                     ticker=LogTicker(), label_standoff=12, location=(0, 0))
plot.add_layout(color_bar, 'right')

# Create edges
edge_width = 3.0
graph.edge_renderer.glyph = MultiLine(line_width=edge_width,
                                      line_color=color_mapper)

# Create 'shadow' of the network edges so that they stand out against the map
graph_shadow = from_networkx(G, locations)
shadow_width = edge_width*1.5
graph_shadow.edge_renderer.glyph = MultiLine(line_width=shadow_width,
                                             line_color="gray")

# Green hover for both nodes and edges
hover_color = '#abdda4'
graph.node_renderer.hover_glyph = Circle(size="size", fill_color=hover_color,
                                         line_color="line_color",
                                         line_width="line_width")
graph.edge_renderer.hover_glyph = MultiLine(line_color=hover_color,
                                            line_width=edge_width)

# When we hover over nodes, highlight adjacent edges too
graph.selection_policy = NodesAndLinkedEdges()
graph.inspection_policy = NodesAndLinkedEdges()

# Add the network to plot
plot.renderers.append(graph_shadow)
plot.renderers.append(graph)

# Show node names and type (e.g. junction, tank) on hover
TOOLTIPS = [
    ("Type", "@type"),
    ("Name", "@name"),
    ("Position", "@pos"),
    ("Elevation", "@elevation"),
    ("Connected", "@connected"),
    ("Base Demand", "@demand"),
    ("Pollution Level", "@colors")
]
plot.add_tools(HoverTool(tooltips=TOOLTIPS), TapTool())

# TapTool to select a node
taptool = plot.select(type=TapTool)
plot.on_event(Tap, node_click)

# Slider to change the timestep of the pollution data visualised
slider = Slider(start=0, end=end_pol, value=0, step=step_pol, title="Time (s)")
slider.on_change('value', update_colors)

# Play button to move the slider for the pollution timeseries
play_button = Button(label=BUTTON_LABEL_PAUSED, button_type="success")
play_button.on_click(animate)

# Dropdown menu to highlight a particular node
node_highlight_dropdown = Dropdown(label="Highlight Node",
                                   css_classes=['green_button'],
                                   menu=list(G.nodes()))
node_highlight_dropdown.on_change('value', update_node_highlight)
node_highlight_dropdown.value = None

# Dropdown menu to highlight a node type
node_type_dropdown = Dropdown(label="Highlight Node Type",
                                    css_classes=['purple_button'],
                                    menu=['None',
                                          'Reservoir',
                                          'Tank',
                                          'Junction'])
node_type_dropdown.on_change('value', update_node_highlight)
node_type_dropdown.value = None

# Dropdown menu to choose pollution start location
pollution_location_dropdown = Dropdown(label="Pollution Injection Node",
                                       css_classes=['blue_button'],
                                       menu=scenarios)
pollution_location_dropdown.on_change('value', update_colors)
pollution_location_dropdown.value = scenarios[0]

# Dropdown menu to choose node size and demand weighting
node_size_slider = Slider(start=1, end=20, value=base_node_size, step=1,
                          title="Node Size")
node_size_slider.on_change('value', update_node_sizes)
node_size_slider.value = base_node_size
demand_weight_slider = Slider(start=1, end=40, value=node_demand_weighting,
                              step=1, title="Base Demand Weighting")
demand_weight_slider.on_change('value', update_node_sizes)
demand_weight_slider.value = node_demand_weighting

# Speed selection dropdown widget
# Animation speeds and speed drop down entries. 'Speeds' are in ms per frame
speed_menu = ['Slow', 'Medium', 'Fast']
speeds = dict(zip(speed_menu, [250, 100, 30]))
speed_dropdown = Dropdown(label="Animation Speed", button_type="primary",
                          menu=speed_menu)
speed_dropdown.on_change('value', update_speed)
# Starting animation speed
animation_speed = speeds['Medium']

# Create the layout for the graph and widgets
layout = row(
    column(
        node_highlight_dropdown,
        node_type_dropdown,
        pollution_location_dropdown,
        node_size_slider,
        demand_weight_slider,
        play_button,
        speed_dropdown,
        slider,
        width=200, sizing_mode="stretch_height"
    ),
    plot,
    sizing_mode="stretch_both"
)

curdoc().add_root(layout)
curdoc().title = "Kentucky water distribution Ky2"
