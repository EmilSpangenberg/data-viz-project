import pandas as pd
import plotly.graph_objects as go


def create_boxplot_by_party(df, selected_year=None):
    """
    Create a box plot showing the distribution of votes by party across states
    for a selected year. Reveals voting concentration and patterns.
    """
    if selected_year is None:
        years = sorted(df["year"].unique())
        selected_year = years[-1]
    
    # Filter data for the selected year
    df_year = df[df["year"] == selected_year].copy()
    
    if df_year.empty:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No data available for {selected_year}",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=14, color="#444"),
        )
        fig.update_layout(title=f"Vote Distribution by Party — {selected_year}")
        return fig
    
    # Group by state and party to get total votes per state-party combination
    state_party_votes = df_year.groupby(["state_po", "party_simplified"])["candidatevotes"].sum().reset_index()
    
    color_map = {
        "Democrat": "#1f77b4",
        "Republican": "#d62728",
        "Other": "#7f7f7f",
    }
    
    fig = go.Figure()
    
    # Create box plot for each party
    for party in ["Democrat", "Republican", "Other"]:
        party_data = state_party_votes[state_party_votes["party_simplified"] == party]
        
        if not party_data.empty:
            fig.add_trace(go.Box(
                y=party_data["candidatevotes"],
                name=party,
                marker_color=color_map.get(party, "#7f7f7f"),
                boxmean='sd',  # Show mean and standard deviation
                hovertemplate='<b>%{fullData.name}</b><br>Votes: %{y:,.0f}<extra></extra>',
            ))
    
    fig.update_layout(
        title=f"Vote Distribution by Party Across States — {selected_year}",
        yaxis_title="Total Votes",
        xaxis_title="Party",
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(
            gridcolor="lightgray",
            tickformat=","
        ),
        height=450,
        margin=dict(t=50, b=50, l=60, r=20),
        font=dict(size=12),
        hovermode="closest"
    )
    
    return fig
