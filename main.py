import dash
import dash_bootstrap_components as dbc
import plotly.figure_factory as ff
from dash import Input, Output, State, callback, ctx, dcc, html

from utils.read_dxl.read_dxl_project import read_DxL_project, read_local_DxL_project

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

global DATA
DATA = None

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
                            id="draw-lat",
                            n_clicks=0,
                            disabled=True,
                        ),
                        dbc.DropdownMenuItem(
                            "Peak to Peak voltage of uEGMs", disabled=True
                        ),
                        dbc.DropdownMenuItem(
                            "Peak Voltage of omnipolar Signal", disabled=True
                        ),
                        dbc.DropdownMenuItem(
                            "Pulse Width of omnipolar Signal", disabled=True
                        ),
                        dbc.DropdownMenuItem("Clear", disabled=True),
                    ],
                    id="draw-dropdown",
                    label="Draw Maps",
                    nav=True,
                    disabled=True,
                ),
            ]
        ),
        html.Div(id="graph-container"),
    ]
)


@callback(
    Output("graph-container", "children", allow_duplicate=True),
    Input("draw-lat", "n_clicks"),
    prevent_initial_call=True,
)
def draw_lat(n_clicks):
    if n_clicks == 0:
        return dash.no_update

    print(DATA["data"])
    return None


@callback(
    Output("graph-container", "children", allow_duplicate=True),
    Output("draw-dropdown", "disabled"),
    Output("draw-lat", "disabled"),
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
            return dash.no_update, dash.no_update, dash.no_update

        DATA = read_DxL_project(filenames, contents)

    elif trigger == "upload-local-data":
        if n_clicks == 0:
            return dash.no_update, dash.no_update, dash.no_update

        DATA = read_local_DxL_project()

    print("Plotting geometry")
    fig = ff.create_trisurf(
        x=DATA["vertices"]["x"],
        y=DATA["vertices"]["y"],
        z=DATA["vertices"]["z"],
        simplices=DATA["faces"].values,
        title="DxLandmarkGeo",
        aspectratio=dict(x=1, y=1, z=1),
        show_colorbar=False,
    )
    for trace in fig.data:
        trace.update(opacity=0.5)

    fig.update_layout(
        scene=dict(xaxis_title="x (mm)", yaxis_title="y (mm)", zaxis_title="z (mm)")
    )
    return dcc.Graph(figure=fig), False, False


if __name__ == "__main__":
    app.run_server(debug=True)
