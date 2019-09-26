from bokeh.io import curdoc
from bokeh.layouts import layout
from bokeh.models.graphs import from_networkx, NodesAndLinkedEdges
from bokeh.models import Range1d, Plot, MultiLine, Circle, HoverTool, Slider, Button, ColumnDataSource
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


def get_pollution_values(pollution_series):
    pollution_values = []
    for node in G.nodes():
        pollution_values.append(pollution_series[node])
    return pollution_values

max_pol = max(pollution['J-10'].max())
min_pol = min(pollution['J-10'].min())

# plots = []
step = 30  # minimum step is 30 because each index is a 30s time step
times = []
for index, pollution_series in pollution['J-10'].iterrows():  # < 1 min for all of J-10 pollution start timesteps
    # if index % step == 0:
        # plots.append(draw_network(pollution_series))
    times.append(index)

# source = ColumnDataSource(data={'colors': get_pollution_values(pollution['J-10'].loc[times[0]])})
pollution_values = get_pollution_values(pollution['J-10'].loc[times[0]])

plot = Plot(x_range=Range1d(min(x) - x_extra_range, max(x) + x_extra_range), y_range=Range1d(min(y) - y_extra_range, max(y) + y_extra_range))

graph = from_networkx(G, locations)

# Create nodes and edges
graph.node_renderer.data_source.data['colors'] = pollution_values
# TODO: set a constant value for the max of the color range
graph.node_renderer.glyph = Circle(size=5, fill_color=linear_cmap('colors', 'Spectral8', min_pol, max_pol))
graph.edge_renderer.glyph = MultiLine(line_alpha=1.6, line_width=0.5)

# green hover for both nodes and edges
graph.node_renderer.hover_glyph = Circle(size=5, fill_color='#abdda4')
graph.edge_renderer.hover_glyph = MultiLine(line_color='#abdda4', line_width=1)

# When we hover over nodes, highlight adjecent edges too
graph.selection_policy = NodesAndLinkedEdges()
graph.inspection_policy = NodesAndLinkedEdges()

plot.renderers.append(graph)

TOOLTIPS = [
    ("Type", "@type"),
    ("Name", "@name"),
]

plot.add_tools(HoverTool(tooltips=TOOLTIPS))

def slider_update(attrname, old, new):
    timestep = slider.value
    pollution_values = get_pollution_values(pollution['J-10'].loc[timestep])
    graph.node_renderer.data_source.data['colors'] = pollution_values
    # plot.renderers.append(generate_graph(pollution_values))
    # source.data = {'colors': pollution_values}

slider = Slider(start=times[0], end=times[-1], value=times[0], step=step, title="Time step")
slider.on_change('value', slider_update)

button = Button(label='► Play', width=60)

layout = layout([
    [plot],
    [slider, button],
], sizing_mode='scale_width')

curdoc().add_root(layout)
# curdoc().title = "Gapminder"
