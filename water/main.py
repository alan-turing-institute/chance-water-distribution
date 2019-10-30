from bokeh.io import curdoc
from bokeh.layouts import row, column
from bokeh.models.graphs import from_networkx, NodesAndLinkedEdges
from bokeh.models import (Range1d, MultiLine, Circle, HoverTool, Slider, Span,
                          Button, ColorBar, LogTicker, ColumnDataSource)
from bokeh.models.widgets import Dropdown, Div, Select
from bokeh.plotting import figure
from bokeh.tile_providers import get_provider, Vendors
from bokeh.transform import log_cmap
from collections import defaultdict
import colorcet as cc
from modules.html_formatter import (timer_html, pollution_history_html,
                                    pollution_loaction_html)
from modules.load_data import load_water_network, load_pollution_dynamics
from modules.pollution import (pollution_series, pollution_history,
                               pollution_scenario)

# Labels for the play/pause button in paused and playing states respectively
BUTTON_LABEL_PAUSED = '► Start Pollution'
BUTTON_LABEL_PLAYING = '❚❚ Pause'

# Node scaling factor
NODE_SCALING = 15

# Color of injection node (Light blue)
# (color used by injection button, update in CSS too on change)
injection_color = "#34c3eb"

# Color of selected node (bright green)
# (color used by highlight button, update in CSS too on change)
highlight_color = "#07db1c"

# Color of selected node type
type_highlight_color = "purple"


def update_highlights():
    """Set the color and width for each node in the graph."""

    # Widths for edges of highlighted and normal nodes
    highlight_width = 3.0
    normal_width = 2.0

    # Create a default dictionary for node types, any node with a type not in
    # the dictionary gets the default color
    colors = defaultdict(lambda: "magenta")
    colors.update({
        'Junction': 'gray',
        'Reservoir': 'orange',
        'Tank': 'green'
        })

    injection = pollution_location_select.value
    node_to_highlight = pollution_history_select.value
    type_highlight = node_type_dropdown.value

    outline_colors = []
    outline_widths = []
    for node in G.nodes():
        if node == injection:
            # Color injection node the injection color regardless of its type
            outline_colors.append(injection_color)
            outline_widths.append(highlight_width)
        elif node == node_to_highlight:
            # Color selected node bright green
            outline_colors.append(highlight_color)
            outline_widths.append(highlight_width)
        else:
            # Otherwise color based on the node type
            node_type = G.nodes[node]['type']
            if node_type == type_highlight:
                outline_colors.append(type_highlight_color)
            else:
                outline_colors.append(colors[node_type])
            outline_widths.append(normal_width)

    data = graph.node_renderer.data_source.data
    data['line_color'], data['line_width'] = outline_colors, outline_widths


def update_pollution_history():
    history_node = pollution_history_select.value
    history = pollution_history(scenario, history_node)
    pollution_history_source.data['time'] = history.index
    pollution_history_source.data['pollution_value'] = history.values
    if history_node != 'None':
        pollution_history_plot.x_range.update(start=0,
                                              end=max(history.index))
        pollution_history_plot.y_range.update(start=0,
                                              end=max(history.values))
    else:
        pollution_history_plot.x_range.update(start=0, end=0)
        pollution_history_plot.y_range.update(start=0, end=0)


def update():
    """Update the appearance of the pollution dynamics network, including node
    and edge colors"""
    timestep = slider.value
    # Get pollution for each node for the given injection site and timestep
    series = pollution_series(scenario, timestep)

    data = graph.node_renderer.data_source.data

    # Set the timer text
    timer.text = timer_html(timestep)
    # Update node colours
    data['colors'] = list(series)

    # Update edge colours
    edge_values = []
    for node1, node2 in G.edges():
        node1_pollution = series[node1]
        node2_pollution = series[node2]
        edge_values.append((node1_pollution + node2_pollution) / 2.)
    graph.edge_renderer.data_source.data['colors'] = edge_values

    # Update timestep span on pollution history plot
    timestep_span.update(location=timestep)


def update_node_highlight(attrname, old, new):
    """Highlight node drop down callback.
    As node colours depend on many widget values, this callback simply calls
    the update highlights function."""
    update_highlights()
    update_pollution_history()
    history_node = pollution_history_select.value
    pollution_history_node_div.text = pollution_history_html(history_node,
                                                             highlight_color)


def update_node_type_highlight(attrname, old, new):
    """Highlight node type drop down callback.
    As node colours depend on many widget values, this callback simply calls
    the update highlights function."""
    update_highlights()


def update_slider(attrname, old, new):
    """Time slider callback.
    As node colours depend on many widget values, this callback simply calls
    the update function."""
    update()


def update_injection(attrname, old, new):
    """Pollution injection node location drop down callback.
    The global variable scenario, which holds the dataframe of pollution
    dynamics is updated.
    As the injection site affects both the node highlights and pollution data
    this callback calls both the update highlights and the update functions"""
    global scenario
    scenario = pollution_scenario(pollution, new)
    update_highlights()
    update_pollution_history()
    update()
    injection_node = pollution_location_select.value
    pollution_location_div.text = pollution_loaction_html(injection_node,
                                                          injection_color)


def update_node_size(attrname, old, new):
    """Node size slider callback.
    Updates the base size of the nodes in the graph"""
    graph.node_renderer.data_source.data['size'] = (
        new + all_base_demands*NODE_SCALING
        )


def step():
    """Move the slider by one step"""
    timestep = slider.value + step_size
    if timestep > end_step:
        timestep = start_step
    slider.value = timestep


def animate():
    """Move the slider every 30 milliseconds on play button click"""
    global callback_id
    global animation_speed
    if play_button.label == BUTTON_LABEL_PAUSED:
        play_button.label = BUTTON_LABEL_PLAYING
        callback_id = curdoc().add_periodic_callback(step, animation_speed)
    elif play_button.label == BUTTON_LABEL_PLAYING:
        play_button.label = BUTTON_LABEL_PAUSED
        curdoc().remove_periodic_callback(callback_id)


def update_speed(attrname, old, new):
    """Adjust the animation speed"""
    global callback_id
    global animation_speed

    # Update animation speed
    animation_speed = speeds[new]

    # If animation is playing recreate the periodic callback
    if play_button.label == BUTTON_LABEL_PLAYING:
        curdoc().remove_periodic_callback(callback_id)
        callback_id = curdoc().add_periodic_callback(step, animation_speed)


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

(pollution, injection_nodes, start_node, start_step, end_step, step_size,
 max_pol, min_pol) = load_pollution_dynamics()

# Create figure object
x_bounds, y_bounds = plot_bounds(locations)
plot = figure(x_range=x_bounds, y_range=y_bounds, active_scroll='wheel_zoom',
              x_axis_type="mercator", y_axis_type="mercator")

# Add map to plot
tile_provider = get_provider(Vendors.CARTODBPOSITRON)
plot.add_tile(tile_provider)

# Create bokeh graph from the NetworkX object
graph = from_networkx(G, locations)

# Define color map for pollution
color_mapper = log_cmap('colors', cc.CET_L18, min_pol, max_pol)

# Create nodes, set the node colors by pollution level and size by base demand
# Node outline color and thickness is different for the pollution start node

# Create node glyphs
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
plot.add_tools(HoverTool(tooltips=TOOLTIPS))

# Pollution history plot
pollution_history_source = ColumnDataSource(
    data=dict(time=[], pollution_value=[])
    )
pollution_history_plot = figure(
    x_range=Range1d(0, 0),
    y_range=Range1d(0, 0),
    active_scroll='wheel_zoom'
    )
pollution_history_plot.line('time', 'pollution_value',
                            source=pollution_history_source, line_width=2.0)
timestep_span = Span(location=0, dimension='height', line_dash='dashed',
                     line_width=2.0)
pollution_history_plot.add_layout(timestep_span)

# Slider to change the timestep of the pollution data visualised
slider = Slider(start=0, end=end_step, value=0, step=step_size,
                title="Time (s)")
slider.on_change('value', update_slider)

# Play button to move the slider for the pollution timeseries
play_button = Button(label=BUTTON_LABEL_PAUSED, button_type="success")
play_button.on_click(animate)

# Menu to highlight nodes green and display pollution history
pollution_history_select = Select(title="Pollution History",
                                  value="None",
                                  options=['None']+list(G.nodes()))
pollution_history_select.on_change('value', update_node_highlight)

# Create a div to show the name of pollution history node
pollution_history_node_div = Div(text=pollution_history_html())

# Dropdown menu to highlight a node type
node_type_dropdown = Dropdown(label="Highlight Node Type", value='None',
                              css_classes=['purple_button'],
                              menu=['None',
                                    'Reservoir',
                                    'Tank',
                                    'Junction'])
node_type_dropdown.on_change('value', update_node_type_highlight)

# Dropdown menu to choose pollution start location
pollution_location_select = Select(title="Pollution Injection Node",
                                   value=injection_nodes[0],
                                   options=injection_nodes)
pollution_location_select.on_change('value', update_injection)

# Create a div to show the name of pollution start node
injection_node = pollution_location_select.value
pol_location_html = pollution_loaction_html(injection_node, injection_color)
pollution_location_div = Div(text=pol_location_html)

# Dropdown menu to choose node size and demand weighting
initial_node_size = 8
graph.node_renderer.data_source.data['size'] = (
    initial_node_size + all_base_demands*NODE_SCALING
    )
node_size_slider = Slider(start=5, end=20, value=initial_node_size, step=1,
                          title="Base Node Size")
node_size_slider.on_change('value', update_node_size)

# Speed selection dropdown widget
# Animation speeds and speed drop down entries. 'Speeds' are in ms per frame
speed_menu = ['Slow', 'Medium', 'Fast']
speeds = dict(zip(speed_menu, [250, 100, 30]))
speed_dropdown = Dropdown(label="Animation Speed", value='Medium',
                          button_type="primary", menu=speed_menu)
speed_dropdown.on_change('value', update_speed)

# Create a div for the timer
timer = Div(text="")

# Create the layout for the graph and widgets
layout = column(
    row(
        column(
            pollution_history_select,
            pollution_history_node_div,
            node_type_dropdown,
            pollution_location_select,
            pollution_location_div,
            node_size_slider,
            play_button,
            speed_dropdown,
            slider,
            timer,
            width=200, sizing_mode="stretch_height"
        ),
        plot,
        pollution_history_plot,
        sizing_mode="stretch_both"
    ),
    sizing_mode="stretch_both"
)

# Initialise
callback_id = None
animation_speed = speeds[speed_dropdown.value]
scenario = pollution_scenario(pollution, pollution_location_select.value)
history = pollution[start_node]['J-10']
pollution_history_source.data['time'] = history.index
pollution_history_source.data['pollution_value'] = history.values
update_highlights()
update()

curdoc().add_root(layout)
curdoc().title = "Kentucky water distribution Ky2"
