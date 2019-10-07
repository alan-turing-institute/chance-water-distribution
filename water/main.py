from bokeh.io import curdoc
from bokeh.layouts import row, column
from bokeh.models.graphs import from_networkx, NodesAndLinkedEdges
from bokeh.models import Range1d, MultiLine, Circle, HoverTool, Slider, Button, ColorBar, LogTicker, Title, ColumnDataSource
from bokeh.models.widgets import Dropdown
from bokeh.plotting import figure
from bokeh.tile_providers import get_provider, Vendors
from bokeh.transform import log_cmap
import colorcet as cc
import datetime
import numpy as np
from os.path import dirname, join
import pickle
from statistics import mean
import wntr



callback_id = None
base_node_size = 8
node_demand_weighting = 15


def get_pollution_values(pollution_series):
    """Get a pollution value for each node, ordered the same as the x,y node coordinates"""
    pollution_values = []
    for node in G.nodes():
        pollution_values.append(pollution_series[node])
    return pollution_values


def update_colors(attrname, old, new):
    """Update pollution data used for node colors"""
    start_node = pollution_location_dropdown.value
    timestep = slider.value
    timer.text = "Pollution Spread from " + start_node + ";  Time - " + str(datetime.timedelta(seconds=int(timestep)))
    pollution_values = get_pollution_values(pollution[start_node].loc[timestep])
    graph.node_renderer.data_source.data['colors'] = pollution_values


def update_node_sizes(attrname, old, new):
    """Update the sizes of the nodes in the graph"""
    node_sizes = [(i * demand_weight_slider.value) + node_size_slider.value for i in all_base_demands]
    graph.node_renderer.data_source.data['size'] = node_sizes


def animate_update_colors():
    """Move the slider by one step"""
    timestep = slider.value + step
    if timestep > times[-1]:
        timestep = times[0]
    slider.value = timestep


def animate():
    """Move the slider every 30 milliseconds on play button click"""
    global callback_id
    if button.label == '► Start Pollution':
        button.label = '❚❚ Pause'
        callback_id = curdoc().add_periodic_callback(animate_update_colors, 30)
    else:
        button.label = '► Start Pollution'
        curdoc().remove_periodic_callback(callback_id)


# load .inp file
filename = join(dirname(__file__), 'data', 'kentucky_water_distribution_networks/ky2.inp')

# Create water network
wn = wntr.network.WaterNetworkModel(filename)

# Get the NetworkX graph
G = wn.get_graph().to_undirected()

# Add the node name as an attribute, so we can use with tooltips
# Also add info about the demand and elevation
# Also add the names of connected nodes and edge names
all_base_demands = []
for node in G.nodes():
    G.node[node]['name'] = node
    try:
        G.node[node]['elevation'] = wn.query_node_attribute('elevation')[node]
    except:
        G.node[node]['elevation'] = 'N/A'
    try:
        base_demands = []
        for timeseries in wn.get_node(node).demand_timeseries_list:
            base_demands.append(timeseries.base_value)
        base_demand = mean(base_demands)
        G.node[node]['demand'] = base_demand
        all_base_demands.append(base_demand)
    except:
        all_base_demands.append(0.0)  # Nodes with no demand will not resize from the base_node_size
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

all_base_demands = [float(i)/max(all_base_demands) for i in all_base_demands]

# Load pollution dynamics
filename = join(dirname(__file__), 'data', 'kentucky_water_distribution_networks/Ky2.pkl')
with open(filename, 'rb') as input_file:
    pollution = pickle.load(input_file)

# Choose a default node for pollution injection
for node in pollution.keys():
    if node != 'chemical_start_time':
        start_node = node
        break

# Create plottable coordinates for each network node
locations = {}
x = []
y = []
for node, node_data in G.nodes().items():
    # Adjust the coordinates to roughly lay over Louisville, Kentucky
    xd = node_data['pos'][0] - 13620000
    yd = node_data['pos'][1] + 1170000
    locations[node] = (xd, yd)
    x.append(xd)
    y.append(yd)

# Use the max and min pollution values for the color range
max_pols = []
min_pols = []
for key, df in pollution.items():
    if key != 'chemical_start_time':
        v = df.values.ravel()
        max_pols.append(np.max(v))
        min_pols.append(np.min(v[v > 0]))
max_pol = np.max(max_pols)
min_pol = np.min(min_pols)

# Get the timstep size for the slider from the pollution df
step = pollution[start_node].index[1] - pollution[start_node].index[0]

# Get a list of the timestep indices we have pollution data for
times = []
for index, pollution_series in pollution[start_node].iterrows():
    times.append(index)

# Set first value of timestep
first_timestep = times[0]

# Get pollution values for first timestep
pollution_values = get_pollution_values(pollution[start_node].loc[first_timestep])

# Create the plot with wiggle room:
x_extra_range = (max(x) - min(x)) / 20
y_extra_range = (max(y) - min(y)) / 20
plot = figure(x_range=Range1d(min(x) - x_extra_range, max(x) + x_extra_range), y_range=Range1d(min(y) - y_extra_range, max(y) + y_extra_range))

# Add map to plot
tile_provider = get_provider(Vendors.CARTODBPOSITRON)
plot.add_tile(tile_provider)

# Add a timer label under plot
timer_text = "[SELECT INJECTION LOCATION]"  # This is no longer actually visible, there is now a default pollution start node
timer = Title(text=timer_text, text_font_size='35pt', text_color='grey')
plot.add_layout(timer, 'below')

# Create bokeh graph from the NetworkX object
graph = from_networkx(G, locations)

# Create nodes, set the node colors by pollution level and size by base demand
graph.node_renderer.data_source.data['colors'] = pollution_values
color_mapper = log_cmap('colors', cc.coolwarm, min_pol, max_pol)
node_sizes = [(i * node_demand_weighting) + base_node_size for i in all_base_demands]
graph.node_renderer.data_source.data['size'] = node_sizes
graph.node_renderer.glyph = Circle(size="size", fill_color=color_mapper)

# Add color bar as legend
color_bar = ColorBar(color_mapper=color_mapper['transform'], ticker=LogTicker(), label_standoff=12, location=(0, 0))
plot.add_layout(color_bar, 'right')

# Create edges
graph.edge_renderer.glyph = MultiLine(line_alpha=1.6, line_width=0.5)

# Green hover for both nodes and edges
graph.node_renderer.hover_glyph = Circle(size="size", fill_color='#abdda4')
graph.edge_renderer.hover_glyph = MultiLine(line_color='#abdda4', line_width=1)

# When we hover over nodes, highlight adjacent edges too
graph.selection_policy = NodesAndLinkedEdges()
graph.inspection_policy = NodesAndLinkedEdges()

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
plot.add_tools(HoverTool(tooltips=TOOLTIPS))

# Slider to change the timestep of the pollution data visualised
slider = Slider(start=first_timestep, end=times[-1], value=first_timestep, step=step, title="Time (s)")
slider.on_change('value', update_colors)

# Play button to move the slider for the pollution timeseries
button = Button(label='► Start Pollution', button_type="success")
button.on_click(animate)

# Dropdown menu to choose pollution start location
menu = []
for node in pollution.keys():
    if node != 'chemical_start_time':
        menu.append((node, node))
pollution_location_dropdown = Dropdown(label="Pollution Injection Location", button_type="danger", menu=menu)
pollution_location_dropdown.on_change('value', update_colors)
pollution_location_dropdown.value = menu[0][0]  # Set default pollution start node

# Dropdown menu to choose node size and demand weighting
node_size_slider = Slider(start=1, end=20, value=base_node_size, step=1, title="Node Size")
node_size_slider.on_change('value', update_node_sizes)
node_size_slider.value = base_node_size
demand_weight_slider = Slider(start=1, end=40, value=node_demand_weighting, step=1, title="Base Demand Weighting")
demand_weight_slider.on_change('value', update_node_sizes)
demand_weight_slider.value = node_demand_weighting

# Create the layout for the graph and widgets
layout = column(
    row(row(node_size_slider, demand_weight_slider), pollution_location_dropdown, height=50, sizing_mode="stretch_width"),
    plot,
    row(button, slider, height=50, sizing_mode="stretch_width"),
    sizing_mode="stretch_both"
)

curdoc().add_root(layout)
curdoc().title = "Kentucky water distribution Ky2"
