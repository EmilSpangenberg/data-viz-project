import pandas as pd
import plotly.graph_objects as go

from graphs.map_chart import get_display_states

COLOR_MAP = {
    "Democrat": "#1f77b4",
    "Republican": "#d62728",
    "Other": "#7f7f7f",
    "No Race": "#bbbbbb",
}


def create_state_split_chart(df: pd.DataFrame, selected_year: int | None = None) -> go.Figure:
    """Show state-level Democrat vs Republican vote share for a given year, sorted by closeness to 50/50."""
    if selected_year is None:
        years = sorted(df["year"].unique())
        if not years:
            return go.Figure()
        selected_year = years[-1]

    df_year = df[df["year"] == selected_year].copy()
    if df_year.empty:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No data for {selected_year}",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=14, color="#444"),
        )
        fig.update_layout(title=f"State Vote Split — {selected_year}")
        return fig

    state_col = "state_po" if "state_po" in df_year.columns else ("state" if "state" in df_year.columns else None)
    if state_col is None:
        fig = go.Figure()
        fig.add_annotation(
            text="No state column found",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=14, color="#444"),
        )
        fig.update_layout(title=f"State Vote Split — {selected_year}")
        return fig

    df_year[state_col] = df_year[state_col].astype(str).str.strip().str.upper()

    agg = df_year.groupby([state_col, "party_simplified"], as_index=False)["candidatevotes"].sum()

    display_states = get_display_states(df)

    states = []
    for state in display_states:
        s = agg[agg[state_col] == state]
        dem = s.loc[s["party_simplified"] == "Democrat", "candidatevotes"].sum()
        rep = s.loc[s["party_simplified"] == "Republican", "candidatevotes"].sum()
        other = s.loc[~s["party_simplified"].isin(["Democrat", "Republican"]), "candidatevotes"].sum()
        total = dem + rep + other
        if total <= 0:
            dem_share = 0.0
            rep_share = 0.0
            margin = 0.0
            winner = "No Race"
        else:
            dem_share = dem / total
            rep_share = rep / total
            margin = dem_share - rep_share  # positive favors Dem, negative favors Rep
            winner = "Democrat" if margin > 0 else ("Republican" if margin < 0 else "Other")
        states.append({
            "state": state,
            "dem_share": dem_share * 100,
            "rep_share": rep_share * 100,
            "margin": margin * 100,  # percentage points
            "total": int(total),
            "winner": winner,
        })

    if not states:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No data for {selected_year}",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=14, color="#444"),
        )
        fig.update_layout(title=f"State Vote Split — {selected_year}")
        return fig

    df_states = pd.DataFrame(states)
    df_states = df_states.reindex(df_states["margin"].abs().sort_values().index)

    chart_height = max(650, 22 * len(df_states))

    text_labels = [f"{abs(m):.1f}%" for m in df_states["margin"]]
    text_positions = ["inside" if abs(m) >= 8 else "outside" for m in df_states["margin"]]

    fig = go.Figure(
        go.Bar(
            x=df_states["margin"],
            y=df_states["state"],
            orientation="h",
            marker_color=[COLOR_MAP.get(w, "#7f7f7f") for w in df_states["winner"]],
            customdata=df_states[["dem_share", "rep_share", "total", "winner"]],
            hovertemplate=(
                "%{y}: %{customdata[0]:.1f}% D / %{customdata[1]:.1f}% R<extra></extra>" +
                "<br>Margin (D-R): %{x:.1f} pp" +
                "<br>Total votes: %{customdata[2]:,}" +
                "<br>Winner: %{customdata[3]}"
            ),
            text=text_labels,
            textposition=text_positions,
            insidetextanchor="middle",
            texttemplate="%{text}",
            insidetextfont=dict(size=10, color="#ffffff"),
            outsidetextfont=dict(size=10, color="#333333"),
            cliponaxis=False,
        )
    )

    fig.update_layout(
        title=f"State Vote Split (Rep - Dem) — {selected_year}",
        xaxis_title="Margin (percentage points; positive = Democrat leads)",
        yaxis_title="State (sorted by closeness to 50/50)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=chart_height,
        margin=dict(t=60, b=40, l=80, r=30),
        yaxis=dict(categoryorder="array", categoryarray=df_states["state"].tolist()),
        shapes=[
            dict(
                type="line",
                x0=0,
                x1=0,
                y0=-0.5,
                y1=len(df_states) - 0.5,
                line=dict(color="#444", width=1, dash="dash"),
            )
        ],
    )

    return fig
