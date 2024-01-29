import plotly.graph_objects as go


def plot_scatter(x, y, z, values, legend):
    if values is not None:
        fig = go.Scatter3d(
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
    else:
        fig = go.Scatter3d(
            x=x,
            y=y,
            z=z,
            mode="markers",
            marker={"size": 5, "color": "#66ff33", "opacity": 0.8},
            marker_symbol="cross",
        )

    return fig
