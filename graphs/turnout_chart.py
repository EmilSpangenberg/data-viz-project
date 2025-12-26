import pandas as pd
import plotly.express as px
from plotly import graph_objs as go


def create_turnout_explorer(df: pd.DataFrame) -> go.Figure:
    """Interactive turnout explorer with range slider and hover detail."""
    state_col = None
    for c in df.columns:
        if c.lower() == "state_po":
            state_col = c
            break
    if state_col is None:
        for c in df.columns:
            if c.lower() == "state":
                state_col = c
                break
    if state_col is None:
        fig = go.Figure()
        fig.add_annotation(text="No state column found", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font=dict(size=14, color="#444"))
        fig.update_layout(title="Interactive Turnout Explorer")
        return fig

    votes_col = None
    for c in df.columns:
        if c.lower() == "totalvotes":
            votes_col = c
            break
    if votes_col is None:
        for c in df.columns:
            if c.lower() == "candidatevotes":
                votes_col = c
                break
    if votes_col is None:
        fig = go.Figure()
        fig.add_annotation(text="No votes column found", x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font=dict(size=14, color="#444"))
        fig.update_layout(title="Interactive Turnout Explorer")
        return fig

    agg = df.groupby(["year", state_col], as_index=False)[votes_col].sum()
    agg = agg.rename(columns={state_col: "state", votes_col: "votes"})

    fig = px.line(
        agg,
        x="year",
        y="votes",
        color="state",
        hover_data={"state": True, "year": True, "votes": ":,"},
        title="Interactive Turnout Explorer (Zoom, Filter, Hover for Detail)",
    )

    fig.update_layout(
        hovermode="x unified",
        xaxis=dict(rangeslider=dict(visible=True), title="Year"),
        yaxis_title="Total votes",
        legend_title="State",
        template="plotly_white",
        margin=dict(t=60, b=40, l=60, r=20),
        height=520,
    )
    return fig
