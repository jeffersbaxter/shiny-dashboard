import numpy as np

# Import helpers for plotting logic
from plots import (
    plot_swing_vs_whiff,
    plot_power_gap_lollipop,
    plot_power_vs_expected,
    plot_hitter_radial_profile
)

# Import some pre-downloaded data on player careers
from shared import (
    app_dir,
    power_vs_expected_df,
    aggression_df,
    radial_profile_df
)
from shiny import App, ui
from shinywidgets import output_widget, render_plotly

PLAYERS = [
    "Arozarena, Randy",
    "Raleigh, Cal",
    "Crawford, J.P.",
    "Rodríguez, Julio",
    "Polanco, Jorge",
    "Williamson, Ben",
    "Garver, Mitch",
    "Canzone, Dominic",
    "Suárez, Eugenio",
    "Young, Cole",
    "Naylor, Josh",
    "Moore, Dylan",
    "Raley, Luke",
    "Tellez, Rowdy",
    "Solano, Donovan",
    "Mastrobuoni, Miles",
    "Rivas, Leo",
    "Robles, Victor",
    "Taveras, Leody"
]

app_ui = ui.page_fillable(
    ui.div(
        ui.h2("2025 Trident Stats", class_="app-title"),
        class_="page-header"
    ),

    ui.navset_card_tab(
        ui.nav_panel(
            "Power Gap",
            ui.layout_columns(
                ui.card(
                    ui.card_header(
                        "Expected Power vs Actual Power"
                    ),
                    output_widget("power_gap"),
                    full_screen=True,
                ),
                col_widths=[12],
            ),
        ),
        ui.nav_panel(
            "Hitter Aggression",
            ui.layout_columns(
                ui.card(
                    ui.card_header(
                        "Hitter Aggression Quality",
                    ),
                    output_widget("aggression_quality"),
                    full_screen=True,
                ),
                col_widths=[12],
            ),
        ),
        ui.nav_panel(
            "Hitter Profile",
            ui.layout_columns(
                ui.card(
                    ui.card_header(
                        "Hitter Radial Profile",
                    ),
                    ui.input_select('player', 'Hitters', PLAYERS),
                    output_widget("radial_profile"),
                    full_screen=True,
                ),
                col_widths=[12],
            ),
        )
    ),

    title="2025 Trident Stats",
)


def server(input, output, session):
    @render_plotly
    def aggression_quality():
        return plot_swing_vs_whiff(aggression_df)
    
    @render_plotly
    def power_v_expected():
        return plot_power_vs_expected(power_vs_expected_df)
    
    @render_plotly
    def power_gap():
        return plot_power_gap_lollipop(power_vs_expected_df)

    @render_plotly
    def radial_profile():
        selected = input.player() or PLAYERS[0]
        return plot_hitter_radial_profile(radial_profile_df, selected)

    # When a player is clicked on the rug plot, add them to the selected players
    def on_rug_click(trace, points, state):
        player_id = trace.customdata[points.point_inds[0]]
        selected = list(input.players()) + [player_id]
        ui.update_selectize("players", selected=selected)


app = App(app_ui, server)
