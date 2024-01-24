import plotly.graph_objects as go
from dash import dcc


def plot_recordings(recordings):
    recordings_fig = go.Figure(
        data=go.Heatmap(
            z=recordings,
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

    return recordings_graph
