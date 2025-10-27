import pandas as pd
from dash import Dash, html, dcc, Input, Output

# Import graph modules
from graphs.bar_chart import create_bar_chart
from graphs.line_chart import create_line_chart
from graphs.map_chart import create_map_chart
from graphs.pie_chart import create_pie_chart

# --- Load data ---
df = pd.read_csv("dataset/1976-2020-president.csv")
df = df[df["party_simplified"].notna()]
df["party_simplified"] = df["party_simplified"].replace({
    "democrat": "Democrat",
    "republican": "Republican"
})

# --- Initialize Dash app ---
app = Dash(__name__)
app.title = "US Presidential Elections Dashboard"

# --- Layout ---
app.layout = html.Div([
    html.H1("US Presidential Elections Dashboard (1976–2020)", style={"textAlign": "center"}),

    html.Div([
        html.Label("Select Year:"),
        dcc.Dropdown(
            id="year_dropdown",
            options=[{"label": y, "value": y} for y in sorted(df["year"].unique())],
            value=2020,
            clearable=False,
        )
    ], style={"width": "30%", "margin": "auto"}),

    html.Div([
        dcc.Graph(id="bar_chart"),
        dcc.Graph(id="line_chart"),
        dcc.Graph(id="map_chart"),
        dcc.Graph(id="pie_chart"),
    ])
])

# --- Callbacks ---
@app.callback(
    Output("bar_chart", "figure"),
    Input("year_dropdown", "value")
)
def update_bar_chart(selected_year):
    return create_bar_chart(df)

@app.callback(
    Output("line_chart", "figure"),
    Input("year_dropdown", "value")
)
def update_line_chart(selected_year):
    return create_line_chart(df)

@app.callback(
    Output("map_chart", "figure"),
    Input("year_dropdown", "value")
)
def update_map_chart(selected_year):
    return create_map_chart(df, selected_year)

@app.callback(
    Output("pie_chart", "figure"),
    Input("year_dropdown", "value")
)
def update_pie_chart(selected_year):
    return create_pie_chart(df, selected_year)

# --- Run server ---
if __name__ == "__main__":
    app.run(debug=True)
