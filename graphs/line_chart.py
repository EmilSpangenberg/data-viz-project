import plotly.express as px

def create_line_chart(df):
    turnout = df.groupby("year", as_index=False)["totalvotes"].sum()
    fig = px.line(turnout, x="year", y="totalvotes", markers=True,
                  title="Total Voter Turnout Over Time")
    return fig
