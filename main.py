import math

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.figure_factory as ff
import plotly.graph_objs as go
from dash import ALL, MATCH, Input, Output, State, callback, ctx, dcc, html, no_update
from plotly.subplots import make_subplots

from utils.export_data.pickle_data import pickle_data
from utils.get_vals_for_map import (
    get_lats,
    get_peak,
    get_ppvoltage,
    get_pulsewidth_omnipolar,
)
from utils.import_data.read_dxl_project import read_DxL_project, read_local_DxL_project
from utils.import_data.read_pkl import read_pkl

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# TODO: move to dcc.Store, to allow multiuser sessions
DATA = None

# TODO: move to dcc.Store, to allow multiuser sessions
GEO_PLOT = None

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
                    label="Local import (FAST)",
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
                    label="Local export (FAST)",
                    nav=True,
                    disabled=True,
                ),
                dbc.DropdownMenu(
                    [
                        dbc.DropdownMenuItem(
                            "Local Activation Times",
                            id="draw-lats",
                            n_clicks=0,
                        ),
                        dbc.DropdownMenuItem(
                            "Peak to Peak voltage of uEGMs",
                            id="draw-ppvoltage",
                            n_clicks=0,
                        ),
                        dbc.DropdownMenuItem(
                            "Peak Voltage of omnipolar Signal",
                            id="draw-peak",
                            n_clicks=0,
                            disabled=True,
                        ),
                        dbc.DropdownMenuItem(
                            "Pulse Width of omnipolar Signal",
                            id="draw-pulsewidth_omnipolar",
                            n_clicks=0,
                            disabled=True,
                        ),
                        dbc.DropdownMenuItem("Clear", id="draw-clear", n_clicks=0),
                    ],
                    id="draw-dropdown",
                    label="Draw Maps",
                    nav=True,
                    disabled=True,
                ),
            ]
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
                            style={"max-width": "90px"},
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

    if group is None:
        return None

    if "range" not in selected_data.keys():
        return None

    selected_data_range_keys = [
        k for k in selected_data["range"].keys() if k.startswith("x")
    ]
    if len(selected_data_range_keys) == 0:
        print("ERROR: No x range selected")
        return None

    x_range = [
        math.ceil(x) for x in selected_data["range"][selected_data_range_keys[0]]
    ]

    data_table = DATA["data_table"]
    group_data = data_table[data_table["pt number"] == group]
    group_rovs = DATA["signals"]["rov trace"].loc[group_data.index]

    coords = group_rovs[["x", "y"]].dropna().astype(int)

    signals_cords = group_rovs.drop(["label"], axis=1)
    signals = signals_cords.drop(["x", "y"], axis=1).astype(float)
    signals_ranged = signals.loc[
        :, (signals.columns >= x_range[0]) & (signals.columns <= x_range[1])
    ]

    available_recordings = np.zeros((4, 4))
    available_recordings[coords["x"], coords["y"]] = 1

    L_coords = []

    for i in range(3):
        for j in range(3):
            if available_recordings[i, j] == 1:
                if (
                    available_recordings[i + 1, j] == 1
                    and available_recordings[i, j + 1] == 1
                ):
                    L_coords.append((i, j))

    if len(L_coords) == 0:
        print("No cliques found")
        return None

    omni_fig = make_subplots(
        rows=3,
        cols=3,
        vertical_spacing=0.05,
        horizontal_spacing=0.05,
    )

    for x in range(3):
        for y in range(3):
            row = 3 - x
            col = y + 1
            if (x, y) in L_coords:
                recording_idx = signals_cords.loc[
                    (signals_cords["x"] == x) & (signals_cords["y"] == y)
                ].index
                upper_idx = signals_cords.loc[
                    (signals_cords["x"] == x + 1) & (signals_cords["y"] == y)
                ].index
                right_idx = signals_cords.loc[
                    (signals_cords["x"] == x) & (signals_cords["y"] == y + 1)
                ].index
                recording = signals_ranged.loc[recording_idx].squeeze()
                upper = signals_ranged.loc[upper_idx].squeeze()
                right = signals_ranged.loc[right_idx].squeeze()

                dif_y = upper - recording
                dif_x = right - recording

                omni_fig.add_trace(
                    go.Scatter(
                        x=dif_x.values.flatten(),
                        y=dif_y.values.flatten(),
                        mode="lines",
                    ),
                    col=col,
                    row=row,
                )
            else:
                omni_fig.add_trace(
                    go.Scatter(
                        x=[],
                        y=[],
                        mode="lines",
                        name=f"({x}, {y})",
                    ),
                    row=row,
                    col=col,
                )

                omni_fig.add_annotation(
                    x=0.5,
                    y=0.5,
                    text="No clique",
                    showarrow=False,
                    font=dict(size=16),
                    row=row,
                    col=col,
                )

    omni_fig.update_layout(
        height=800,
        width=800,
        margin=dict(l=5, r=5, b=5, t=5, pad=0),
        showlegend=False,
    )

    return dcc.Graph(figure=omni_fig)


@callback(
    Output("placeholder", "children"),
    Input("pickle-data", "n_clicks"),
    prevent_initial_call=True,
)
def export_to_pickle(n_clicks):
    pickle_data(DATA)

    return no_update


@callback(
    Output("signals-container", "children"),
    Output(
        {"type": "omnipolar-container", "index": "1"}, "children", allow_duplicate=True
    ),
    Output(
        {"type": "available-recordings", "index": "1"},
        "children",
    ),
    Input("freeze-groups", "value"),
    prevent_initial_call=True,
)
def select_freeze_group(group):
    if group is None:
        return None, None, None

    print(f"Freeze group {group}")

    data_table = DATA["data_table"]
    group_data = data_table[data_table["pt number"] == group]
    group_rovs = DATA["signals"]["rov trace"].loc[group_data.index]

    labels = group_rovs["label"]
    coords = group_rovs[["x", "y"]].dropna().astype(int)
    signals = group_rovs.drop(["label", "x", "y"], axis=1).astype(float)

    signals_fig = make_subplots(
        rows=len(labels),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0,
    )

    for i, (idx, label) in enumerate(labels.items()):
        signals_fig.add_trace(
            go.Scatter(
                x=list(range(len(signals.columns))),
                y=signals.loc[idx],
                name=label,
            ),
            row=i + 1,
            col=1,
        )

        signals_fig.update_xaxes(showticklabels=False, showgrid=False, row=i + 1, col=1)
        signals_fig.update_yaxes(showticklabels=False, showgrid=False, row=i + 1, col=1)

    signals_fig.update_layout(
        title=f"Freeze Group {group}",
        showlegend=True,
        xaxis={"fixedrange": True},
        yaxis={"fixedrange": True},
        dragmode="select",
        margin=dict(l=5),
    )

    signals_graph = dcc.Graph(
        figure=signals_fig,
        config={
            "modeBarButtons": False,
            "scrollZoom": False,
            "showAxisDragHandles": False,
            "showAxisRangeEntryBoxes": False,
        },
        id={"type": "signals-graph", "index": "1"},
    )

    available_recordings = np.zeros((4, 4))
    available_recordings[coords["x"], coords["y"]] = 1

    if np.all(available_recordings == 0):
        print(
            "'rov trace' headers misformed. Cannot show available recordings. Expected format: 'Channel + [A-D][1-4]'"
        )
        return signals_graph, None, None

    recordings_fig = go.Figure(
        data=go.Heatmap(
            z=available_recordings,
            text=[[f"{chr(ord('A') + i)}{j + 1}" for j in range(4)] for i in range(4)],
            x=[1, 2, 3, 4],
            y=["A", "B", "C", "D"],
            texttemplate="%{text}",
            colorscale=[[0, "white"], [1, "green"]],
            showscale=False,
        ),
    )

    recordings_fig.update_layout(
        showlegend=False,
        width=120,
        height=120,
        autosize=False,
        yaxis={"scaleanchor": "x", "fixedrange": True},
        margin=dict(l=10, r=10, b=10, t=10, pad=0),
        coloraxis=dict(showscale=False),
    )

    recordings_graph = dcc.Graph(
        figure=recordings_fig,
        config={
            "staticPlot": True,
        },
    )

    return signals_graph, None, recordings_graph


@callback(
    Output("graph-container", "children", allow_duplicate=True),
    Input("draw-lats", "n_clicks"),
    Input("draw-ppvoltage", "n_clicks"),
    Input("draw-peak", "n_clicks"),
    Input("draw-pulsewidth_omnipolar", "n_clicks"),
    Input("draw-clear", "n_clicks"),
    prevent_initial_call=True,
)
def draw_map(*n_clicks):
    if all([n_click == 0 for n_click in n_clicks]) or GEO_PLOT is None:
        return no_update, no_update

    trigger = ctx.triggered_id

    data_table = DATA["data_table"]

    x, y, z = data_table["roving x"], data_table["roving y"], data_table["roving z"]
    values, legend, title = None, "", ""

    if trigger == "draw-lats":
        print("Drawing LATs")
        values = get_lats(data_table)
        legend = "LATs (s)"
        title = "Map of LATs (s)"
    elif trigger == "draw-ppvoltage":
        print("Drawing PP Voltage")
        values = get_ppvoltage(data_table)
        legend = "P-P Voltage (mV)"
        title = "Map of Peak to Peak Voltage (mV)"
    elif trigger == "draw-peak":
        print("Drawing Peak Voltage")
        values = get_peak(data_table)
        legend = "Peak Voltage (mV)"
        title = "Map of Peak Amplitude of Omnipole"
    elif trigger == "draw-pulsewidth_omnipolar":
        print("Drawing Pulse Width")
        values = get_pulsewidth_omnipolar(data_table)
        legend = "Pulse Width (ms)"
        title = "Map of Pulse Width of Omnipolar Signals"
    else:
        print("Clearing")
        GEO_PLOT.update_layout(title="Geometry")
        return dcc.Graph(figure=GEO_PLOT)

    scatter = go.Scatter3d(
        x=x,
        y=y,
        z=z,
        mode="markers",
        marker={
            "size": 5,
            "color": values,
            "opacity": 0.8,
            "colorbar": {"title": legend},
            "cmin": values.min(),
            "cmax": values.max(),
        },
    )

    GEO_PLOT.update_layout(title=title)
    fig = go.Figure(data=[*GEO_PLOT.data, scatter], layout=GEO_PLOT.layout)

    return dcc.Graph(figure=fig)


@callback(
    Output("graph-container", "children", allow_duplicate=True),
    Output("draw-dropdown", "disabled"),
    Output("freeze-groups", "options"),
    Output("freeze-groups", "disabled"),
    Output("export-dropdown", "disabled"),
    Output("freeze-groups", "value"),
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
                return no_update, no_update, no_update, no_update, no_update, no_update

            DATA = read_DxL_project(filenames, contents)

        elif trigger == "upload-local-data":
            if n_clicks_dxl == 0:
                return no_update, no_update, no_update, no_update, no_update, no_update

            DATA = read_local_DxL_project()

        elif trigger == "upload-local-pkl":
            if n_clicks_pkl == 0:
                return no_update, no_update, no_update, no_update, no_update, no_update

            DATA = read_pkl()
    except Exception as e:
        print(f"ERROR: {e}")
        return no_update, no_update, no_update, no_update, no_update, no_update

    data_table = DATA["data_table"]
    groups = data_table["pt number"].unique()
    group_select_options = [{"label": group, "value": group} for group in groups]

    vertices, faces = DATA["vertices"], DATA["faces"]

    print("Import successful")

    if vertices is None or faces is None:
        return None, True, group_select_options, False, False, None

    print("Plotting geometry")

    fig = ff.create_trisurf(
        x=vertices["x"],
        y=vertices["y"],
        z=vertices["z"],
        simplices=faces.values,
        title="Geometry",
        aspectratio=dict(x=1, y=1, z=1),
        show_colorbar=False,
    )
    for trace in fig.data:
        trace.update(opacity=0.5)

    fig.update_layout(
        scene={
            "xaxis_title": "x (mm)",
            "yaxis_title": "y (mm)",
            "zaxis_title": "z (mm)",
        },
        showlegend=False,
    )

    global GEO_PLOT
    GEO_PLOT = fig

    return dcc.Graph(figure=fig), False, group_select_options, False, False, None


if __name__ == "__main__":
    app.run_server(debug=True)
