import numpy as np
import plotly.graph_objects as go
from dash import dcc
from plotly.subplots import make_subplots


def plot_omnipoles(group_rovs, x_range):
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
        print("WARNING: No cliques found")
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
