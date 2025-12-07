import numpy as np
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go

color_palette = px.colors.qualitative.D3


def radar_chart(percs_df, stats_df, stats):
    fig = go.Figure()

    for _, row in percs_df.iterrows():
        id = row["person_id"]
        r = [row[x] for x in stats]
        vals = stats_df[stats_df["person_id"] == id][stats].values[0]
        text = np.round(vals, 2).astype(str).tolist()
        fig.add_trace(
            go.Scatterpolar(
                r=r + r[:1],
                theta=stats + stats[:1],
                text=text + text[:1],
                name=row["player_name"],
                hoverinfo="text+name",
                line=dict(width=1, color=row["color"]),
            )
        )

    fig.update_layout(
        margin=dict(l=30, r=30, t=30, b=30),
        polar=dict(radialaxis=dict(range=[0, 1])),
        showlegend=True,
        legend=dict(orientation="h", y=-0.1, yanchor="top", x=0.5, xanchor="center"),
    )

    return fig


def calculate_kde(data, num_points=500, bandwidth=None):
    """
    Calculate Kernel Density Estimation using NumPy only.

    Args:
        data: 1D array of values
        num_points: Number of points to evaluate KDE
        bandwidth: KDE bandwidth (uses Silverman's rule if None)

    Returns:
        x_range, y_values for the KDE curve
    """
    data = np.array(data)

    # Use Silverman's rule of thumb for bandwidth if not provided
    if bandwidth is None:
        bandwidth = 1.06 * np.std(data) * len(data) ** (-1/5)

    # Create range for evaluation
    data_min, data_max = data.min(), data.max()
    data_range = data_max - data_min
    x_range = np.linspace(data_min - 0.5 * data_range, 
                          data_max + 0.5 * data_range, 
                          num_points)

    # Calculate KDE using Gaussian kernel
    kde_values = np.zeros(num_points)
    for point in data:
        # Gaussian kernel: (1/sqrt(2π)) * exp(-0.5 * ((x - point) / bandwidth)^2)
        kde_values += np.exp(-0.5 * ((x_range - point) / bandwidth) ** 2)

    # Normalize
    kde_values = kde_values / (len(data) * bandwidth * np.sqrt(2 * np.pi))

    return x_range, kde_values


def density_plot(careers_df, stats_df, stat, players_dict, on_rug_click):
    vals = careers_df[stat]
    vals = vals[~vals.isnull()]

    # Calculate KDE manually
    x_range, kde_values = calculate_kde(vals.values)
    ymax = kde_values.max()

    # Create figure
    fig = go.Figure()

    # Add KDE curve (density plot)
    fig.add_trace(go.Scatter(
        x=x_range,
        y=kde_values,
        mode='lines',
        name='Overall',
        line=dict(color='black', width=2),
        hoverinfo='none',
        showlegend=False,
        fill='tozeroy',
        fillcolor='rgba(0,0,0,0.1)'
    ))

    # Add rug plot (tick marks at bottom)
    fig.add_trace(go.Scatter(
        x=vals,
        y=np.zeros(len(vals)),
        mode='markers',
        marker=dict(
            symbol='line-ns-open',
            size=10,
            color='black',
            line=dict(width=1)
        ),
        text=careers_df["player_name"],
        customdata=careers_df["person_id"],
        hoverinfo='text+x',
        showlegend=False,
        name='Players'
    ))

    # Arrange rows from highest to lowest value so that legend order is correct
    stats_df = stats_df.sort_values(stat, ascending=False)

    # Add vertical lines for each player
    for _, row in stats_df.iterrows():
        x = row[stat]
        fig.add_trace(go.Scatter(
            x=[x, x],
            y=[0, ymax],
            mode="lines",
            name=players_dict[row["person_id"]],
            line=dict(color=row["color"], width=1),
            hoverinfo="x+name",
        ))

    fig.update_layout(
        hovermode="x",
        xaxis=dict(title=stat + " per game (career average)", hoverformat=".1f"),
        yaxis=dict(title="Density"),
        legend=dict(orientation="h", y=1.03, yanchor="bottom", x=0.5, xanchor="center"),
        showlegend=True
    )

    # Convert Figure to FigureWidget so we can add click events
    fig = go.FigureWidget(fig.data, fig.layout)
    fig.data[1].on_click(on_rug_click)  # Rug plot is now index 1

    return fig
