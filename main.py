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
        html.Div(id={"type": "omnipolar-container", "index": "1"}),
        html.Div(id="signals-container"),
        dbc.Row(
            [
                dbc.Col(id="graph-container", width=True),
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
                            style={"max-width": "90px", "margin-right": "10px"},
                        )
                    ],
                    width="auto",
                ),
            ],
        ),
        html.Div(id="placeholder", style={"display": "none"}),
    ]
)


@callback(
    Output({"type": "omnipolar-container", "index": MATCH}, "children"),
    Input({"type": "signals-graph", "index": MATCH}, "selectedData"),
    prevent_initial_call=True,
)
def select_omnipolar(selectedData):
    print(selectedData)
    return no_update


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
    Input("freeze-groups", "value"),
    prevent_initial_call=True,
)
def select_freeze_group(group):
    if group is None:
        return None

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
        return signals_graph

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
        margin=dict(l=5, r=0, b=0, t=0, pad=0),
        coloraxis=dict(showscale=False),
    )

    recordings_graph = dcc.Graph(
        figure=recordings_fig,
        config={
            "staticPlot": True,
        },
    )

    return dbc.Row(
        [
            dbc.Col(
                html.Div(recordings_graph, style={"width": 150, "margin-left": "30px"}),
                width="auto",
            ),
            dbc.Col(signals_graph, width=True),
        ],
        align="center",
    )


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
