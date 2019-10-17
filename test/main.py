import networkx as nx
from bokeh.models.graphs import from_networkx
from bokeh.models import Range1d, MultiLine, Circle, TapTool, Plot, HoverTool, BoxSelectTool
from bokeh.plotting import figure
from bokeh.io import curdoc
from bokeh.layouts import row
from bokeh.models.widgets import Dropdown
from bokeh.events import Tap


def choose_node_outline_colors(nodes_clicked):
    outline_colors = []
    for node in G.nodes():
        if str(node) in nodes_clicked:
            outline_colors.append('pink')
        else:
            outline_colors.append('black')
    return outline_colors


def update_node_highlight(attrname, old, new):
    node_clicked = dropdown.value
    source.data['line_color'] = choose_node_outline_colors(node_clicked)


def callback(event):
    nodes_clicked_ints = source.selected.indices
    nodes_clicked = list(map(str, nodes_clicked_ints))
    source.data['line_color'] = choose_node_outline_colors(nodes_clicked)


G = nx.karate_club_graph()

plot = Plot(plot_width=400, plot_height=400,
            x_range=Range1d(-1.1,1.1), y_range=Range1d(-1.1,1.1))
graph = from_networkx(
    G,
    nx.circular_layout,
    scale=1,
    center=(0,0)
)

# Create nodes and edges
source = graph.node_renderer.data_source
# data = graph.node_renderer.data_source.data
source.data['line_color'] = choose_node_outline_colors('1')
graph.node_renderer.glyph = Circle(size=10, line_color="line_color")
graph.edge_renderer.glyph = MultiLine(line_alpha=1.6, line_width=0.5)

# Add tap tool
TOOLTIPS = [
    ("Index", "@index"),
]
plot.add_tools(HoverTool(tooltips=TOOLTIPS), TapTool(), BoxSelectTool())

plot.renderers.append(graph)

# Dropdown menu to highlight a particular node
dropdown = Dropdown(label="Highlight Node", menu=list(map(str, list(G.nodes()))))
dropdown.on_change('value', update_node_highlight)
dropdown.value = '1'

taptool = plot.select(type=TapTool)

plot.on_event(Tap, callback)

curdoc().add_root(row(plot, dropdown))
