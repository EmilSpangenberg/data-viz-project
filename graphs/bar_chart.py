import plotly.graph_objects as go
import pandas as pd


def create_bar_chart(df, selected_year=None):
    # Aggregate votes by year/party
    df_agg = (
        df.groupby(["year", "party_simplified"], as_index=False)["candidatevotes"]
        .sum()
        .sort_values(["year", "party_simplified"])
    )
    
    # Get all unique years and parties
    years = sorted(df_agg["year"].unique())
    parties = ["Democrat", "Republican", "Other"]
    
    # Define colors
    color_map = {
        "Democrat": "#1f77b4",
        "Republican": "#d62728",
        "Other": "#7f7f7f",
    }
    
    # Determine which year to show
    if selected_year is None:
        selected_year = years[-1]  # Default to most recent year
    
    # Filter data for the selected year
    df_year = df_agg[df_agg["year"] == selected_year]
    
    # Create the figure
    fig = go.Figure()
    
    for party in parties:
        party_data = df_year[df_year["party_simplified"] == party]
        votes = party_data["candidatevotes"].values[0] if len(party_data) > 0 else 0
        
        fig.add_trace(go.Bar(
            name=party,
            x=[party],
            y=[votes],
            marker_color=color_map.get(party, "#7f7f7f"),
            text=[votes],
            texttemplate='%{text:.3s}',
            textposition='outside',
            textfont_size=12,
            hovertemplate='<b>%{x}</b><br>Votes: %{y:,}<extra></extra>'
        ))
    
    # Update layout
    fig.update_layout(
        title=f"Votes by Party - {selected_year}",
        xaxis_title="Party",
        yaxis_title="Total Votes",
        yaxis=dict(
            gridcolor="lightgray",
            tickformat=","
        ),
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        height=450,
        margin=dict(t=50, b=50, l=60, r=20),
        font=dict(size=12)
    )
    
    return fig

