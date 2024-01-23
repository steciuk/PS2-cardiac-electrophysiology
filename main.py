import dash
import dash_bootstrap_components as dbc
import plotly.figure_factory as ff
import plotly.graph_objs as go
from dash import ALL, Input, Output, State, callback, ctx, dcc, html, no_update

from utils.get_vals_for_map import (
    get_lats,
    get_peak,
    get_ppvoltage,
    get_pulsewidth_omnipolar,
)
from utils.read_dxl.read_dxl_project import read_DxL_project, read_local_DxL_project

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

global DATA
DATA = None

global GEO_PLOT
GEO_PLOT = None

app.layout = html.Div(
    [
        dbc.Nav(
            [
                dbc.DropdownMenu(
                    [
                        dbc.DropdownMenuItem("Import .mat file", disabled=True),
                        dbc.DropdownMenuItem(
                            dcc.Upload(
                                "Import DxL files",
                                id="upload-browse-data",
                                multiple=True,
                            ),
                        ),
                        dbc.DropdownMenuItem("From Contact_Mapping", disabled=True),
                    ],
                    label="Import",
                    nav=True,
                ),
                dbc.DropdownMenu(
                    [
                        dbc.DropdownMenuItem("Import .mat file", disabled=True),
                        dbc.DropdownMenuItem(
                            "Import DxL files",
                            id="upload-local-data",
                            n_clicks=0,
                        ),
                        dbc.DropdownMenuItem("From Contact_Mapping", disabled=True),
                    ],
                    label="Local import (FAST)",
                    nav=True,
                ),
                dbc.DropdownMenu(
                    [],
                    label="Export",
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
    ]
)


@callback(
    Output("signals-container", "children"),
    Input("freeze-groups", "value"),
    prevent_initial_call=True,
)
def select_freeze_group(group):
    print(f"Freeze group {group}")

    data_table = DATA["data_table"]
    group_data = data_table[data_table["pt number"] == group]
    group_rovs = DATA["signals"]["rov trace"].loc[group_data.index]

    channels = group_rovs.iloc[:, 0]
    signals = group_rovs.drop(group_rovs.columns[0], axis=1).astype(float)

    fig = go.Figure()
    for i, channel in enumerate(channels):
        fig.add_trace(
            go.Scatter(
                x=list(range(len(signals.columns))),
                y=signals.iloc[i, :],
                name=channel,
            )
        )

    fig.update_layout(
        title=f"Freeze Group {group}",
        showlegend=True,
        xaxis={"visible": False},
    )

    return dcc.Graph(figure=fig)


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
    Input("upload-browse-data", "contents"),
    State("upload-browse-data", "filename"),
    Input("upload-local-data", "n_clicks"),
    prevent_initial_call=True,
)
def upload_data(contents, filenames, n_clicks):
    trigger = ctx.triggered_id
    global DATA

    if trigger == "upload-browse-data":
        if contents is None or len(contents) == 0:
            return no_update, no_update, no_update, no_update

        DATA = read_DxL_project(filenames, contents)

    elif trigger == "upload-local-data":
        if n_clicks == 0:
            return no_update, no_update, no_update, no_update

        DATA = read_local_DxL_project()

    data_table = DATA["data_table"]
    groups = data_table["pt number"].unique()
    group_select_options = [{"label": group, "value": group} for group in groups]

    print("Plotting geometry")
    vertices, faces = DATA["vertices"], DATA["faces"]

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

    return dcc.Graph(figure=fig), False, group_select_options, False


if __name__ == "__main__":
    app.run_server(debug=True)
