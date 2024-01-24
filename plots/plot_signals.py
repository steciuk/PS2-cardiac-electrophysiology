import plotly.graph_objects as go
from dash import dcc
from plotly.subplots import make_subplots


def plot_signals(group_rovs, title):
    labels = group_rovs["label"]
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
        title=title,
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

    return signals_graph
