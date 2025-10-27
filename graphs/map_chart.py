import plotly.express as px

def create_map_chart(df, selected_year):
    df_year = df[df["year"] == selected_year]
    winners = df_year.loc[df_year.groupby("state")["candidatevotes"].idxmax()]
    fig = px.choropleth(
        winners,
        locations="state_po",
        locationmode="USA-states",
        color="party_simplified",
        scope="usa",
        title=f"Winning Party by State ({selected_year})"
    )
    return fig
