from bokeh.io import curdoc
from bokeh.layouts import row, column
from bokeh.models.graphs import from_networkx, NodesAndLinkedEdges
from bokeh.models import Range1d, MultiLine, Circle, HoverTool, Slider, Button, ColorBar, LogTicker, Title
from bokeh.models.widgets import Dropdown
from bokeh.plotting import figure
from bokeh.tile_providers import get_provider, Vendors
from bokeh.transform import log_cmap
import colorcet as cc
import datetime
import numpy as np
import pickle
import wntr
from os.path import dirname, join


callback_id = None


def get_pollution_values(pollution_series):
    """Get a pollution value for each node, ordered the same as the x,y node coordinates"""
    pollution_values = []
    for node in G.nodes():
        pollution_values.append(pollution_series[node])
    return pollution_values


def update(attrname, old, new):
    """Update pollution data used when the slider or dropdown value changes"""
    start_node = dropdown.value
    timestep = slider.value
    timer.text = "Pollution Spread from " + start_node + ";  Time - " + str(datetime.timedelta(seconds=int(timestep)))
    pollution_values = get_pollution_values(pollution[start_node].loc[timestep])
    graph.node_renderer.data_source.data['colors'] = pollution_values


def animate_update():
    """Move the slider by one step"""
    timestep = slider.value + step
    if timestep > times[-1]:
        timestep = times[0]
    slider.value = timestep


def animate():
    """Move the slider every 30 milliseconds on play button click"""
    global callback_id
    if button.label == '► Play':
        button.label = '❚❚ Pause'
        callback_id = curdoc().add_periodic_callback(animate_update, 30)
    else:
        button.label = '► Play'
        curdoc().remove_periodic_callback(callback_id)


# load .inp file
filename = join(dirname(__file__), 'data', 'kentucky_water_distribution_networks/ky2.inp')

# Create water network
wn = wntr.network.WaterNetworkModel(filename)

# Get the NetworkX graph
G = wn.get_graph().to_undirected()

# Add the node name as an attribute, so we can use with tooltips
# Also add the names of connected nodes and edge names
for node in G.nodes():
    G.node[node]['name'] = node
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
plot = figure(x_range=Range1d(min(x) - x_extra_range, max(x) + x_extra_range),
              y_range=Range1d(min(y) - y_extra_range, max(y) + y_extra_range),
              x_axis_type="mercator", y_axis_type="mercator")

# Add map to plot
tile_provider = get_provider(Vendors.CARTODBPOSITRON)
plot.add_tile(tile_provider)

# Add a timer label under plot
timer_text = "Pollution Spread from [SELECT INJECTION LOCATION]"
timer = Title(text=timer_text, text_font_size='35pt', text_color='grey')
plot.add_layout(timer, 'below')

# Create bokeh graph from the NetworkX object
graph = from_networkx(G, locations)

# Create nodes and set the node colors by pollution level
graph.node_renderer.data_source.data['colors'] = pollution_values
color_mapper = log_cmap('colors', cc.coolwarm, min_pol, max_pol)
node_size = 10
graph.node_renderer.glyph = Circle(size=node_size, fill_color=color_mapper)

# Add color bar as legend
color_bar = ColorBar(color_mapper=color_mapper['transform'], ticker=LogTicker(), label_standoff=12, location=(0, 0))
plot.add_layout(color_bar, 'right')

# Create edges
graph.edge_renderer.glyph = MultiLine(line_alpha=1.6, line_width=0.5)

# Green hover for both nodes and edges
graph.node_renderer.hover_glyph = Circle(size=node_size, fill_color='#abdda4')
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
    ("Connected", "@connected"),
]
plot.add_tools(HoverTool(tooltips=TOOLTIPS))

# Create the layout with time slider, play button and pollution start menu
slider = Slider(start=first_timestep, end=times[-1], value=first_timestep, step=step, title="Time (s)")
slider.on_change('value', update)

button = Button(label='► Play', button_type="success")
button.on_click(animate)

menu = []
for node in pollution.keys():
    if node != 'chemical_start_time':
        menu.append((node, node))
dropdown = Dropdown(label="Pollution Injection Location", button_type="primary", menu=menu)
dropdown.on_change('value', update)

layout = column(
    row(dropdown, height=50, sizing_mode="stretch_width"),
    plot,
    row(button, slider, height=50, sizing_mode="stretch_width"),
    sizing_mode="stretch_both"
)

curdoc().add_root(layout)
curdoc().title = "Kentucky water distribution Ky2"
