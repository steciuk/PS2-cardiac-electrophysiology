import math

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash import MATCH, Input, Output, State, callback, ctx, dcc, html, no_update

from export_data.pickle_data import pickle_data
from import_data.read_dxl_project import read_DxL_project, read_local_DxL_project
from import_data.read_pkl import read_pkl
from plots.plot_geometry import plot_geometry
from plots.plot_omnipoles import plot_omnipoles
from plots.plot_recordings import plot_recordings
from plots.plot_scatter import plot_scatter
from plots.plot_signals import plot_signals
from utils.filters import bandpass_filter, notch_filter

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

DATA = None

app.layout = html.Div(
    [
        dbc.Nav(
            [
                dbc.DropdownMenu(
                    [
                        dbc.DropdownMenuItem(
                            dcc.Upload(
                                "Import DxL files",
                                id="upload-browse-data",
                                multiple=True,
                            ),
                        ),
                    ],
                    label="Import",
                    nav=True,
                ),
                dbc.DropdownMenu(
                    [
                        dbc.DropdownMenuItem(
                            "Import .pkl file",
                            id="upload-local-pkl",
                            n_clicks=0,
                        ),
                        dbc.DropdownMenuItem(
                            "Import DxL files",
                            id="upload-local-data",
                            n_clicks=0,
                        ),
                    ],
                    label="Local import",
                    nav=True,
                ),
                dbc.DropdownMenu(
                    [
                        dbc.DropdownMenuItem(
                            "Pickle data",
                            id="pickle-data",
                            n_clicks=0,
                        )
                    ],
                    id="export-dropdown",
                    label="Local export",
                    nav=True,
                    disabled=True,
                ),
                dbc.DropdownMenu(
                    [
                        dbc.DropdownMenuItem(
                            "Local activation times",
                            id="draw-lats",
                            n_clicks=0,
                        ),
                        dbc.DropdownMenuItem(
                            "Peak to peak voltage of uEGMs",
                            id="draw-ppvoltage",
                            n_clicks=0,
                        ),
                        dbc.DropdownMenuItem(
                            "Lessions",
                            id="draw-lessions",
                            n_clicks=0,
                            disabled=True,
                        ),
                        dbc.DropdownMenuItem("Clear", id="draw-clear", n_clicks=0),
                    ],
                    id="draw-dropdown",
                    label="Draw maps",
                    nav=True,
                    disabled=True,
                ),
            ]
        ),
        html.Div(
            [
                html.H5("Unipole filters", style={"margin-right": "10px"}),
                dbc.Select(
                    id="filters",
                    options=[
                        {"label": "None", "value": "None"},
                        {"label": "Band Pass 2-100Hz", "value": "bp-2-100"},
                        {"label": "Notch 50Hz", "value": "notch-50"},
                    ],
                    value="None",
                    style={"width": "200px"},
                ),
            ],
            style={"display": "none"},
            id="filters-container",
        ),
        html.Div(id="signals-container"),
        dbc.Row(
            [
                dbc.Col(
                    html.Div(id={"type": "omnipolar-container", "index": "1"}),
                    width=True,
                ),
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.H5("Freeze Group"),
                                dbc.Select(
                                    id="freeze-groups",
                                    options=[],
                                    disabled=True,
                                ),
                            ],
                            id="freeze-group-container",
                            style={"display": "none"},
                        ),
                        html.Div(id={"type": "available-recordings", "index": "1"}),
                    ],
                    width="auto",
                    style={
                        "display": "flex",
                        "flex-direction": "column",
                        "gap": "10px",
                        "align-items": "center",
                    },
                ),
            ]
        ),
        html.Div(id="graph-container"),
        html.Div(id="placeholder", style={"display": "none"}),
    ]
)


@callback(
    Output(
        {"type": "omnipolar-container", "index": MATCH},
        "children",
        allow_duplicate=True,
    ),
    Input({"type": "signals-graph", "index": MATCH}, "selectedData"),
    State("freeze-groups", "value"),
    prevent_initial_call=True,
)
def select_omnipolar(selected_data, group):
    if selected_data is None:
        return no_update

    if group is None or "range" not in selected_data.keys():
        return None

    selected_data_range_keys = [
        k for k in selected_data["range"].keys() if k.startswith("x")
    ]
    if len(selected_data_range_keys) == 0:
        print("WARNING: No x range selected")
        return None

    x_range = [
        math.ceil(x) for x in selected_data["range"][selected_data_range_keys[0]]
    ]

    data_table = DATA["data_table"]
    group_data = data_table[data_table["pt number"] == group]
    group_rovs = DATA["signals"]["rov trace"].loc[group_data.index]

    return plot_omnipoles(group_rovs, x_range)


@callback(
    Output("placeholder", "children"),
    Input("pickle-data", "n_clicks"),
    prevent_initial_call=True,
)
def export_to_pickle(_):
    pickle_data(DATA)

    return no_update


@callback(
    Output("signals-container", "children", allow_duplicate=True),
    Output(
        {"type": "omnipolar-container", "index": "1"}, "children", allow_duplicate=True
    ),
    Output("filters-container", "style", allow_duplicate=True),
    Output("filters", "value", allow_duplicate=True),
    Input("filters", "value"),
    State("freeze-groups", "value"),
    prevent_initial_call=True,
)
def change_filter(filter, group):
    if group is None:
        return None, None, {"display": "none"}, "None"

    data_table = DATA["data_table"]
    group_data = data_table[data_table["pt number"] == group]
    group_rovs = DATA["signals"]["rov trace"].loc[group_data.index]

    fs = data_table["Sample rate"].dropna().unique()[0]

    if filter == "bp-2-100":
        filter_func = lambda x: bandpass_filter(x, 2, 100, fs)
    elif filter == "notch-50":
        filter_func = lambda x: notch_filter(x, 50, fs)
    else:
        filter_func = lambda x: x

    signals_graph = plot_signals(group_rovs, f"Freeze Group {group}", filter_func)

    return signals_graph, None, {"display": "block"}, filter


@callback(
    Output("signals-container", "children", allow_duplicate=True),
    Output(
        {"type": "omnipolar-container", "index": "1"}, "children", allow_duplicate=True
    ),
    Output(
        {"type": "available-recordings", "index": "1"}, "children", allow_duplicate=True
    ),
    Output("filters-container", "style", allow_duplicate=True),
    Output("filters", "value", allow_duplicate=True),
    Input("freeze-groups", "value"),
    State("filters", "value"),
    prevent_initial_call=True,
)
def select_freeze_group(group, filter):
    if group is None:
        return None, None, None, {"display": "none"}, "None"

    data_table = DATA["data_table"]
    group_data = data_table[data_table["pt number"] == group]
    group_rovs = DATA["signals"]["rov trace"].loc[group_data.index]

    fs = data_table["Sample rate"].dropna().unique()[0]

    if filter == "bp-2-100":
        filter_func = lambda x: bandpass_filter(x, 2, 100, fs)
    elif filter == "notch-50":
        filter_func = lambda x: notch_filter(x, 50, fs)
    else:
        filter_func = lambda x: x

    signals_graph = plot_signals(group_rovs, f"Freeze Group {group}", filter_func)

    coords = group_rovs[["x", "y"]].dropna().astype(int)
    available_recordings = np.zeros((4, 4))
    available_recordings[coords["x"], coords["y"]] = 1

    if np.all(available_recordings == 0):
        print(
            "WARNING: Signal headers are either malformed or ambiguous. "
            + "Recordings map won't be shown. Omnipole calculations won't be available. "
            + "Expected format '.*[A-D][1-4].*'"
        )
        return signals_graph, None, None, {"display": "block"}, filter

    recordings_graph = plot_recordings(available_recordings)

    return signals_graph, None, recordings_graph, {"display": "block"}, filter


@callback(
    Output("graph-container", "children", allow_duplicate=True),
    Input("draw-lats", "n_clicks"),
    Input("draw-ppvoltage", "n_clicks"),
    Input("draw-clear", "n_clicks"),
    Input("draw-lessions", "n_clicks"),
    prevent_initial_call=True,
)
def draw_map(*n_clicks):
    trigger = ctx.triggered_id

    data_table = DATA["data_table"]
    values, legend, title = None, "", ""

    geo_plot = plot_geometry(DATA["vertices"], DATA["faces"])
    x, y, z = data_table["roving x"], data_table["roving y"], data_table["roving z"]

    if trigger == "draw-lats":
        print("Drawing LATs")

        values = (
            data_table["rov LAT"] - data_table["ref LAT"]
            if "ref LAT" in data_table.columns
            else data_table["rov LAT"]
        )
        min_lat = abs(values.min())
        values = values + min_lat

        legend = "LATs (s)"
        title = "Map of LATs (s)"
    elif trigger == "draw-ppvoltage":
        print("Drawing PP Voltage")

        values = data_table["peak2peak"]

        legend = "P-P Voltage (mV)"
        title = "Map of Peak to Peak Voltage (mV)"
    elif trigger == "draw-lessions":
        print("Drawing Lessions")

        values = None
        lessions = DATA["lessions"]
        x, y, z = lessions["x"], lessions["y"], lessions["z"]

        legend = ""
        title = "Map of Lessions"
    else:
        print("Clearing")
        geo_plot.update_layout(title="Geometry")
        return dcc.Graph(figure=geo_plot)

    geo_plot.update_layout(title=title)

    scatter = plot_scatter(
        x,
        y,
        z,
        values,
        legend,
    )
    fig = go.Figure(data=[*geo_plot.data, scatter], layout=geo_plot.layout)

    return dcc.Graph(figure=fig)


@callback(
    Output("graph-container", "children", allow_duplicate=True),
    Output("draw-dropdown", "disabled"),
    Output("freeze-groups", "options"),
    Output("freeze-groups", "disabled"),
    Output("export-dropdown", "disabled"),
    Output("freeze-groups", "value"),
    Output("freeze-group-container", "style"),
    Output("draw-lessions", "disabled"),
    Input("upload-browse-data", "contents"),
    State("upload-browse-data", "filename"),
    Input("upload-local-data", "n_clicks"),
    Input("upload-local-pkl", "n_clicks"),
    prevent_initial_call=True,
)
def upload_data(contents, filenames, n_clicks_dxl, n_clicks_pkl):
    trigger = ctx.triggered_id
    global DATA

    try:
        if trigger == "upload-browse-data":
            if contents is None or len(contents) == 0:
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                )

            DATA = read_DxL_project(filenames, contents)

        elif trigger == "upload-local-data":
            DATA = read_local_DxL_project()

        elif trigger == "upload-local-pkl":
            DATA = read_pkl()

    except Exception as e:
        print(f"ERROR: {e}")
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
        )

    print("Import successful")

    data_table = DATA["data_table"]
    groups = data_table["pt number"].unique()
    group_select_options = [{"label": group, "value": group} for group in groups]

    vertices, faces = DATA["vertices"], DATA["faces"]

    fig = None
    map_disabled = True
    lessions_disabled = True

    if vertices is not None and faces is not None:
        print("Plotting geometry")
        fig = dcc.Graph(figure=plot_geometry(vertices, faces))
        map_disabled = False

        if DATA["lessions"] is not None:
            lessions_disabled = False
        else:
            print("WARNING: Lessions mapping disabled")

    return (
        fig,
        map_disabled,
        group_select_options,
        False,
        False,
        None,
        {"display": "block", "max-width": "90px"},
        lessions_disabled,
    )


if __name__ == "__main__":
    app.run_server(debug=True)
