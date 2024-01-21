import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html, dcc, callback

from utils.read_dxl.read_dxl import read_DxL

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

data = None

app.layout = html.Div(
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
    )
)


@callback(
    Output("output-data-upload", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
)
def update_output(contents, filenames):
    if contents is None:
        return

    vertices, faces = read_DxL(filenames, contents)


if __name__ == "__main__":
    app.run_server(debug=True)
