import datetime


def timer_html(timestep):
    timer_html = "<h1 style='color:grey'>Time: "
    timer_html += str(datetime.timedelta(seconds=int(timestep)))
    timer_html += "</h1>"
    return timer_html


def pollution_history_html(history_node="None", highlight_color="black"):
    pollution_history_html = "<p>Selection: <b style='color:"
    pollution_history_html += highlight_color + "'>"
    pollution_history_html += history_node
    pollution_history_html += "</b></p>"
    return pollution_history_html


def pollution_loaction_html(injection_node, injection_color):
    pollution_location_html = "<p>Selection: <b style='color:"
    pollution_location_html += injection_color + "'>"
    pollution_location_html += injection_node
    pollution_location_html += "</b></p>"
    return pollution_location_html
