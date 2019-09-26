from bokeh.io import curdoc
from bokeh.layouts import layout
from bokeh.models.graphs import from_networkx, NodesAndLinkedEdges
from bokeh.models import Range1d, MultiLine, Circle, HoverTool, Slider, Button
from bokeh.plotting import figure
from bokeh.transform import linear_cmap
import pickle
import wntr
from os.path import dirname, join


callback_id = None
start_node = 'J-10'


def get_pollution_values(pollution_series):
    """Get a pollution value for each node, ordered the same as the x,y node coordinates"""
    pollution_values = []
    for node in G.nodes():
        pollution_values.append(pollution_series[node])
    return pollution_values


def slider_update(attrname, old, new):
    """Update the pollution data used in graph when slider moved"""
    timestep = slider.value
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
G = wn.get_graph()

for node in G.nodes():  # add the node name as an attribute, so we can use with tooltips
    G.node[node]['name'] = node

# Load pollution dynamics
filename = join(dirname(__file__), 'data', 'kentucky_water_distribution_networks/Ky2.pkl')
with open(filename, 'rb') as input_file:
    pollution = pickle.load(input_file)

# Create plottable coordinates for each network node
locations = {}
x = []
y = []
for node, node_data in G.nodes().items():
    locations[node] = (node_data['pos'][0], node_data['pos'][1])
    x.append(node_data['pos'][0])
    y.append(node_data['pos'][1])

# Use the max and min pollution values for the color range
max_pol = max(pollution[start_node].max())
min_pol = min(pollution[start_node].min())

# Get the timstep size for the slider from the pollution df
step = pollution[start_node].index[1] - pollution[start_node].index[0]

# Get a list of the timestep indices we have pollution data for
times = []
for index, pollution_series in pollution[start_node].iterrows():
    times.append(index)

# Get pollution values for first timestep
pollution_values = get_pollution_values(pollution[start_node].loc[times[0]])

# Create the plot with wiggle room:
x_extra_range = (max(x) - min(x)) / 100
y_extra_range = (max(x) - min(x)) / 100
plot = figure(x_range=Range1d(min(x) - x_extra_range, max(x) + x_extra_range), y_range=Range1d(min(y) - y_extra_range, max(y) + y_extra_range))

# Create bokeh graph from the NetworkX object
graph = from_networkx(G, locations)

# Create nodes and set the node colors by pollution level
graph.node_renderer.data_source.data['colors'] = pollution_values
graph.node_renderer.glyph = Circle(size=5, fill_color=linear_cmap('colors', 'Spectral8', min_pol, max_pol))

# Create edges
graph.edge_renderer.glyph = MultiLine(line_alpha=1.6, line_width=0.5)

# Green hover for both nodes and edges
graph.node_renderer.hover_glyph = Circle(size=5, fill_color='#abdda4')
graph.edge_renderer.hover_glyph = MultiLine(line_color='#abdda4', line_width=1)

# When we hover over nodes, highlight adjacent edges too
graph.selection_policy = NodesAndLinkedEdges()
graph.inspection_policy = NodesAndLinkedEdges()

plot.renderers.append(graph)

# Show node names and type (e.g. junction, tank) on hover
TOOLTIPS = [
    ("Type", "@type"),
    ("Name", "@name"),
]
plot.add_tools(HoverTool(tooltips=TOOLTIPS))

# Create the layout with slider and play button
slider = Slider(start=times[0], end=times[-1], value=times[0], step=step, title="Time step")
slider.on_change('value', slider_update)

button = Button(label='► Play')
button.on_click(animate)

layout = layout([
    [plot],
    [slider, button],
])

curdoc().add_root(layout)
curdoc().title = "Kentucky water distribution Ky2"
