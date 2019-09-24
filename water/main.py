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
# pollution_series = pollution['J-10'].iloc[700]

slider = Slider(start=0, end=3, value=0, step=1, title="Time")
button = Button(label='► Play', width=60)

# Create plottable coordinates
locations = {}
x = []
y = []
for node, node_data in dict(G.nodes).items():
    locations[node] = (node_data['pos'][0], node_data['pos'][1])
    x.append(node_data['pos'][0])
    y.append(node_data['pos'][1])
x_extra_range = (max(x) - min(x)) / 100
y_extra_range = (max(x) - min(x)) / 100

def draw_network(pollution_series):
    pollution_values = []
    for node in G.nodes():
        pollution_values.append(pollution_series[node])

    graph = from_networkx(G, locations)
    plot = Plot(x_range=Range1d(min(x) - x_extra_range, max(x) + x_extra_range), y_range=Range1d(min(y) - y_extra_range, max(y) + y_extra_range))

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

    return plot

plots = []
count = 0  # TODO: save all plots instead of just a few
for index, pollution_series in pollution['J-10'].iterrows():  # < 1 min for all of J-10 pollution start timesteps
    if count % 100 == 0:
        plots.append(draw_network(pollution_series))
    count += 1

layout = layout([
    [plots[3]],
    [slider, button],
], sizing_mode='scale_width')

curdoc().add_root(layout)
# curdoc().title = "Gapminder"
