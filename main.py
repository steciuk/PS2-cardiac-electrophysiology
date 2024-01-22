import dash
import dash_bootstrap_components as dbc
import plotly.figure_factory as ff
from dash import Input, Output, State, callback, dcc, html

from utils.read_dxl.read_dxl import read_DxL

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

data = None

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
                                id="upload-data",
                                multiple=True,
                            ),
                        ),
                        dbc.DropdownMenuItem("From Contact_Mapping", disabled=True),
                    ],
                    label="Import",
                    nav=True,
                ),
                html.Div(id="output-data-upload"),
            ]
        ),
        html.Div(id="graph-container"),
    ]
)


@callback(
    Output("graph-container", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
)
def update_output(contents, filenames):
    if contents is None or len(contents) == 0:
        return

    print("Callback run")

    vertices, faces = read_DxL(filenames, contents)
    fig = ff.create_trisurf(
        x=vertices["x"],
        y=vertices["y"],
        z=vertices["z"],
        simplices=faces.values,
        title="DxLandmarkGeo",
        aspectratio=dict(x=1, y=1, z=1),
        show_colorbar=False,
    )
    for trace in fig.data:
        trace.update(opacity=0.5)

    fig.update_layout(
        scene=dict(xaxis_title="x (mm)", yaxis_title="y (mm)", zaxis_title="z (mm)")
    )
    return dcc.Graph(figure=fig)


if __name__ == "__main__":
    app.run_server(debug=True)
