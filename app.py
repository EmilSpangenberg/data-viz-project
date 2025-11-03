import pandas as pd
from dash import Dash, html, dcc, Input, Output

# Import graph modules
from graphs.bar_chart import create_bar_chart
from graphs.line_chart import create_line_chart
from graphs.map_chart import create_map_chart
from graphs.pie_chart import create_pie_chart


def _load_and_prepare(path):
    # Try a small set of common encodings, fall back to a permissive decode if needed
    encodings = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]
    df = None
    used_encoding = None
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc)
            used_encoding = enc
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        # Last resort: read bytes and decode with replacement for invalid bytes
        from io import StringIO
        with open(path, "rb") as f:
            raw = f.read()
        text = raw.decode("utf-8", errors="replace")
        df = pd.read_csv(StringIO(text))
        used_encoding = "utf-8 (errors=replace)"

    # keep rows with defined party
    df = df[df["party_simplified"].notna()].copy()

    # normalize party names to a consistent display form
    def _norm_party(p):
        s = str(p).lower()
        if s == "democrat":
            return "Democrat"
        if s == "republican":
            return "Republican"
        return s.title()

    df["party_simplified"] = df["party_simplified"].apply(_norm_party)
    # small debug hint when running locally
    try:
        print(f"Loaded {path} using encoding: {used_encoding}")
    except Exception:
        pass
    return df


# --- Load both datasets ---
df_president = _load_and_prepare("dataset/1976-2020-president.csv")
df_senate = _load_and_prepare("dataset/1976-2020-senate.csv")

# --- Initialize Dash app ---
app = Dash(__name__)
app.title = "US Elections Dashboard (President & Senate)"

# --- Layout ---
app.layout = html.Div([
    html.H1("US Elections Dashboard (1976–2020)", style={"textAlign": "center"}),

    html.Div([
        html.Label("Select Dataset:"),
        dcc.RadioItems(
            id="dataset_selector",
            options=[
                {"label": "Presidential (1976–2020)", "value": "president"},
                {"label": "Senate (1976–2020)", "value": "senate"},
            ],
            value="president",
            labelStyle={"display": "inline-block", "marginRight": "1rem"}
        )
    ], style={"width": "60%", "margin": "auto", "textAlign": "center"}),

    html.Div([
        html.Label("Select Year:"),
        dcc.Dropdown(
            id="year_dropdown",
            # options set by callback when dataset changes
            clearable=False,
        )
    ], style={"width": "30%", "margin": "1rem auto"}),

    html.Div([
        dcc.Graph(id="bar_chart"),
        dcc.Graph(id="line_chart"),
        dcc.Graph(id="map_chart"),
        dcc.Graph(id="pie_chart"),
    ])
])


# Update year dropdown options/value when dataset changes
@app.callback(
    Output("year_dropdown", "options"),
    Output("year_dropdown", "value"),
    Input("dataset_selector", "value")
)
def update_year_options(dataset):
    df = df_president if dataset == "president" else df_senate
    years = sorted(df["year"].unique())
    default = max(years) if len(years) else None
    options = [{"label": y, "value": y} for y in years]
    return options, default


# Chart callbacks now depend on both dataset and year
@app.callback(
    Output("bar_chart", "figure"),
    Input("dataset_selector", "value"),
    Input("year_dropdown", "value")
)
def update_bar_chart(dataset, selected_year):
    df = df_president if dataset == "president" else df_senate
    return create_bar_chart(df)


@app.callback(
    Output("line_chart", "figure"),
    Input("dataset_selector", "value"),
    Input("year_dropdown", "value")
)
def update_line_chart(dataset, selected_year):
    df = df_president if dataset == "president" else df_senate
    return create_line_chart(df)


@app.callback(
    Output("map_chart", "figure"),
    Input("dataset_selector", "value"),
    Input("year_dropdown", "value")
)
def update_map_chart(dataset, selected_year):
    df = df_president if dataset == "president" else df_senate
    return create_map_chart(df, selected_year)


@app.callback(
    Output("pie_chart", "figure"),
    Input("dataset_selector", "value"),
    Input("year_dropdown", "value")
)
def update_pie_chart(dataset, selected_year):
    df = df_president if dataset == "president" else df_senate
    return create_pie_chart(df, selected_year)


# --- Run server ---
if __name__ == "__main__":
    app.run(debug=True)
