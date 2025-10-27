import plotly.express as px

def create_bar_chart(df):
    df_year = df.groupby(["year", "party_simplified"], as_index=False)["candidatevotes"].sum()
    fig = px.bar(
        df_year,
        x="party_simplified",
        y="candidatevotes",
        color="party_simplified",
        animation_frame="year",
        title="Votes by Party Over Time (Animated)"
    )
    fig.update_layout(transition_duration=500)
    return fig
