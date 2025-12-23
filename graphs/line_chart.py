import plotly.graph_objects as go
import pandas as pd


def create_line_chart(df):
    """
    Create a line chart showing voter turnout over time.
    Shows total votes and breakdown by party (Democrat, Republican, Other).
    """
    # Aggregate votes by party and year
    party_by_year = df.groupby(["year", "party_simplified"], as_index=False)["candidatevotes"].sum()
    party_by_year = party_by_year.rename(columns={"candidatevotes": "votes", "party_simplified": "category"})
    
    # Calculate total as sum of all candidate votes per year
    total_by_year = df.groupby("year", as_index=False)["candidatevotes"].sum()
    total_by_year = total_by_year.rename(columns={"candidatevotes": "votes"})
    total_by_year["category"] = "Total"
    
    # Combine the data
    combined = pd.concat([total_by_year, party_by_year], ignore_index=True)
    
    # Create figure
    fig = go.Figure()
    
    # Color mapping
    colors = {
        "Total": "#2ca02c",  # Green
        "Democrat": "#1f77b4",  # Blue
        "Republican": "#d62728",  # Red
        "Other": "#7f7f7f"  # Gray
    }
    
    # Add traces for each category
    for category in ["Total", "Democrat", "Republican", "Other"]:
        data = combined[combined["category"] == category].sort_values("year")
        if len(data) > 0:
            fig.add_trace(go.Scatter(
                x=data["year"],
                y=data["votes"],
                mode="lines+markers",
                name=category,
                line=dict(color=colors.get(category, "#666"), width=2),
                marker=dict(size=6),
                hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Votes: %{y:,}<extra></extra>"
            ))
    
    # Update layout with range slider
    fig.update_layout(
        title="Voter Turnout Over Time by Party",
        xaxis_title="Year",
        yaxis_title="Total Votes",
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            gridcolor="lightgray",
            type="linear"
        ),
        yaxis=dict(
            gridcolor="lightgray",
            tickformat=","
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=450,
        margin=dict(t=80, b=60, l=60, r=20)
    )
    
    return fig
