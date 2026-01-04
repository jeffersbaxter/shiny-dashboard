import numpy as np
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
import pandas as pd

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


def plot_swing_vs_whiff(df, top_n=40):
    """
    Scatter: swing_rate (x) vs whiff_rate (y)
    color = hardhit_percent, size = barrels_per_pa_percent
    Filter to top_n by plate appearances (pa) to avoid tiny-sample noise.
    """
    df_plot = df.copy()
    if 'pa' in df_plot.columns:
        df_plot = df_plot.sort_values('pa', ascending=False).head(top_n)
    else:
        df_plot = df_plot.head(top_n)

    # convert to percent for labeling if desired
    df_plot['swing_pct'] = round(df_plot['swing_rate'] * 100, 2)
    df_plot['whiff_pct'] = round(df_plot['whiff_rate'] * 100, 2)
    df_plot['hardhit_pct'] = round(df_plot['hardhit_percent'] * 100, 2)
    df_plot['barrels_per_pa_pct'] = round(df_plot['barrels_per_pa_percent'] * 100, 2)
    df_plot['barrels_per_pa_percent'] = round(df_plot['barrels_per_pa_percent'], 2)

    fig = px.scatter(
        df_plot,
        x='swing_rate',
        y='whiff_rate',
        color='hardhit_pct',               # use fraction (0-1) or percent
        size='barrels_per_pa_percent',         # bubble size
        hover_data=['player_name', 'xwoba', 'xslg'],
        labels={
            'swing_rate': 'Swing % (fraction)',
            'whiff_rate': 'Whiff % (fraction)',
            'hardhit_pct': 'Hard-hit %',
            'barrels_per_pa_percent': 'Barrels/PA'
        },
        title=f"Swing% vs Whiff% (Top {len(df_plot)} by PA)"
    )
    fig.update_layout(yaxis_tickformat=".0%", xaxis_tickformat=".0%")
    return fig


def plot_power_vs_expected(df):
    fig = px.scatter(
        df,
        x="slg",
        y="xslg",
        size="barrels_per_pa_percent",
        color="hardhit_percent",
        hover_data=["player_name", "slg", "xslg", "hardhit_percent", "barrels_per_pa_percent"],
        labels={
            "slg": "Actual SLG",
            "xslg": "Expected SLG",
            "hardhit_percent": "HardHit %",
            "barrels_per_pa_percent": "Barrels / PA %"
        },
        title="Power vs Expected Power<br><sup>Bubble size: Barrels/PA • Color: HardHit%</sup>",
        height=600
    )

    fig.update_traces(mode="markers", marker=dict(sizemode="area", opacity=0.8))
    fig.update_layout(xaxis=dict(zeroline=True), yaxis=dict(zeroline=True))
    return fig


def plot_power_gap_lollipop(df, top_n=30):

    # compute gap
    df = df.copy()
    df["power_gap"] = df["xslg"] - df["slg"]

    # pick top players by absolute gap
    df = df.reindex(df["power_gap"].abs().sort_values(ascending=False).index)
    df = df.head(top_n)

    fig = go.Figure()

    # Lollipop "stick"
    fig.add_trace(go.Scatter(
        x=df["xslg"],
        y=df["player_name"],
        mode="lines",
        line=dict(color="lightgray", width=2),
        showlegend=False
    ))

    # Starting point (SLG)
    fig.add_trace(go.Scatter(
        x=df["slg"],
        y=df["player_name"],
        mode="markers",
        marker=dict(color="red", size=12),
        name="SLG"
    ))

    # Ending point (xSLG)
    fig.add_trace(go.Scatter(
        x=df["xslg"],
        y=df["player_name"],
        mode="markers",
        marker=dict(color="green", size=12),
        name="xSLG"
    ))

    fig.update_layout(
        title="SLG vs xSLG Gap",
        xaxis_title="SLG / xSLG",
        height=600,
        margin=dict(l=120, r=40, t=60)
    )

    return fig


def plot_hitter_radial_profile(df, player_name):
    """
    Creates a polar bar chart showing a hitter's overall batted-ball/contact profile.
    """

    metrics = {
        "Launch Speed (EV)": "launch_speed",
        "Launch Angle": "launch_angle",
        "HardHit %": "hardhit_percent",
        "Barrels/Batted Ball %": "barrels_per_bbe_percent",
        "BABIP": "babip",
        "SLG": "slg",
    }

    # subset to player
    row = df[df["player_name"] == player_name].iloc[0]

    chart_df = pd.DataFrame({
        "metric": list(metrics.keys()),
        "value": [row[col] for col in metrics.values()]
    })

    fig = px.bar_polar(
        chart_df,
        r="value",
        theta="metric",
        color="metric",
        template="plotly_dark",
        title=f"{player_name} — Batted-Ball Profile",
    )

    fig.update_traces(opacity=0.85)
    fig.update_layout(
        height=250,
        polar=dict(
            radialaxis=dict(showline=False, showticklabels=False, ticks=""),
            angularaxis=dict(showline=False, direction="clockwise"),
        ),
        showlegend=False
    )

    return fig
