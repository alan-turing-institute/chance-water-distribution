from bokeh.io import curdoc
from bokeh.layouts import layout
from bokeh.models.graphs import from_networkx, NodesAndLinkedEdges
from bokeh.models import Range1d, Plot, MultiLine, Circle, HoverTool, Slider, Button
from bokeh.palettes import Spectral4
from bokeh.transform import linear_cmap
import pickle
import wntr
from os.path import dirname, join

# load .inp file
filename = join(dirname(__file__), 'data', 'kentucky_water_distribution_networks/ky2.inp')
wn = wntr.network.WaterNetworkModel(filename)

# Get the NetworkX graph
G = wn.get_graph()

for node in G.nodes():  # add the node name as an attribute, so we can use with tooltips
    G.node[node]['name'] = node

# Load dynamics
filename = join(dirname(__file__), 'data', 'kentucky_water_distribution_networks/Ky2.pkl')
with open(filename, 'rb') as input_file:
    pollution = pickle.load(input_file)

# Use 700th timestep of pollution starting at J-10 as an example
pollution_series = pollution['J-10'].iloc[700]
pollution_values = []

slider = Slider(start=0, end=3, value=0, step=1, title="Time")
button = Button(label='► Play', width=60)

# Create plottable coordinates
x = []
y = []

nodes_dict = dict(G.nodes)
for node_name, node_data in nodes_dict.items():

    x.append(node_data['pos'][0])
    y.append(node_data['pos'][1])

    pollution_values.append(pollution_series[node_name])

x = [(i - min(x)) / (max(x) - min(x)) for i in x]
y = [(i - min(y)) / (max(y) - min(y)) for i in y]

locations = {}
i = 0
for node_name, node_data in nodes_dict.items():
    locations[node_name] = (x[i], y[i])
    i += 1

graph = from_networkx(G, locations)
plot = Plot(x_range=Range1d(-0.1, 1.1), y_range=Range1d(-0.1, 1.1))

# Create nodes and edges
graph.node_renderer.data_source.data['colors'] = pollution_values
# TODO: set a constant value for the max of the color range
graph.node_renderer.glyph = Circle(size=5, fill_color=linear_cmap('colors', 'Spectral8', min(pollution_values), max(pollution_values)))
graph.edge_renderer.glyph = MultiLine(line_alpha=1.6, line_width=0.5)

# green hover for both nodes and edges
graph.node_renderer.hover_glyph = Circle(size=5, fill_color='#abdda4')
graph.edge_renderer.hover_glyph = MultiLine(line_color='#abdda4', line_width=1)

# When we hover over nodes, highlight adjecent edges too
graph.selection_policy = NodesAndLinkedEdges()
graph.inspection_policy = NodesAndLinkedEdges()

TOOLTIPS = [
    ("Type", "@type"),
    ("Name", "@name"),
]

plot.add_tools(HoverTool(tooltips=TOOLTIPS))

plot.renderers.append(graph)

layout = layout([
    [plot],
    [slider, button],
], sizing_mode='scale_width')

curdoc().add_root(layout)
# curdoc().title = "Gapminder"
