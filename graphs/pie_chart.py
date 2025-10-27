import plotly.express as px

def create_pie_chart(df, selected_year):
    df_year = df[df["year"] == selected_year]
    pie_data = df_year.groupby("party_simplified", as_index=False)["candidatevotes"].sum()
    fig = px.pie(pie_data, values="candidatevotes", names="party_simplified",
                 title=f"Vote Share by Party in {selected_year}")
    return fig
