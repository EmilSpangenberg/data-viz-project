import logging
import pandas as pd
from dash import Dash, html, dcc, Input, Output

# Import graph modules
from graphs.bar_chart import create_bar_chart
from graphs.line_chart import create_line_chart
from graphs.map_chart import create_map_chart, get_display_states
from graphs.pie_chart import create_pie_chart

# Bootswatch theme (Flatly) via CDN
THEME = "https://cdn.jsdelivr.net/npm/bootswatch@5.2.3/dist/flatly/bootstrap.min.css"


def _load_and_prepare(path):
    # Simpler robust loader:
    # - try common encodings with the fast C engine
    # - if pandas throws a ParserError, retry with the python engine and skip bad lines
    # - normalize column names and string values (strip surrounding quotes/whitespace)
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    df = None
    used_encoding = None
    for enc in encodings:
        try:
            df = pd.read_csv(path, encoding=enc, low_memory=False, sep=",", quotechar='"', skipinitialspace=True)
            used_encoding = enc
            break
        except UnicodeDecodeError:
            continue
        except pd.errors.ParserError:
            # try python engine tolerant of bad lines
            try:
                df = pd.read_csv(path, encoding=enc, engine="python", sep=",", quotechar='"', skipinitialspace=True, on_bad_lines="skip")
                used_encoding = f"{enc} (python engine)"
                break
            except Exception:
                df = None
                continue
        except Exception:
            df = None
            continue

    if df is None:
        # final fallback: read bytes and parse with python engine, replacing invalid bytes
        from io import StringIO
        with open(path, "rb") as f:
            raw = f.read()
        text = raw.decode("utf-8", errors="replace")
        df = pd.read_csv(StringIO(text), engine="python", sep=",", quotechar='"', skipinitialspace=True, on_bad_lines="skip")
        used_encoding = "utf-8 (errors=replace, python engine)"

    # keep rows with defined party
    df = df[df["party_simplified"].notna()].copy()

    # normalize column names (strip whitespace and surrounding quotes)
    df.columns = [str(c).strip().strip('"').strip() for c in df.columns]

    # strip surrounding quotes/whitespace from string columns
    for col in df.select_dtypes(include=[object]).columns:
        df[col] = df[col].astype(str).str.strip().str.strip('"').str.strip()

    # locate party column case-insensitively
    party_col = None
    for c in df.columns:
        if c.lower() == "party_simplified":
            party_col = c
            break
    if party_col is None:
        # try best-effort fallback: any column containing 'party'
        for c in df.columns:
            if "party" in c.lower():
                party_col = c
                break
    if party_col is None:
        raise ValueError(f"party_simplified column not found in {path}; columns: {df.columns.tolist()}")

    # keep rows with defined party
    df = df[df[party_col].notna()].copy()

    # normalize party values to readable form
    def _norm_party(p):
        s = str(p).lower()
        if s == "democrat":
            return "Democrat"
        if s == "republican":
            return "Republican"
        return s.title()

    df["party_simplified"] = df[party_col].apply(_norm_party)

    # debug hint when running locally
    try:
        print(f"Loaded {path} using encoding: {used_encoding}")
    except Exception:
        pass

    return df


# --- Load both datasets ---
df_president = _load_and_prepare("dataset/1976-2020-president.csv")
df_senate = _load_and_prepare("dataset/1976-2020-senate.csv")

# --- Initialize Dash app ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Initialize Dash app with the selected theme
app = Dash(__name__, external_stylesheets=[THEME])
app.title = "US Elections Dashboard (President & Senate)"

# --- Layout (Bootstrap cards/grid) ---
app.layout = html.Div([
    # Navbar
    html.Nav(className="navbar navbar-dark bg-primary", children=
             html.Div(className="container", children=[
                 html.Span("US Elections Dashboard (1976–2020)", className="navbar-brand mb-0 h1"),
             ])
    ),

    html.Div(className="container-fluid my-4", children=[
        html.Div(className="row g-4 gy-4", children=[
            # Controls column
            html.Div(className="col-md-3", children=[
                html.Div(className="card mb-4", children=[
                    html.Div(className="card-body py-3", children=[
                        html.H5("Controls", className="card-title"),
                        html.Div([
                            html.Label("Select Dataset:"),
                            dcc.RadioItems(
                                id="dataset_selector",
                                options=[
                                    {"label": "Presidential (1976–2020)", "value": "president"},
                                    {"label": "Senate (1976–2020)", "value": "senate"},
                                ],
                                value="president",
                                labelStyle={"display": "block", "marginBottom": "0.25rem"}
                            )
                        ], style={"marginBottom": "1rem"}),

                        html.Div([
                            html.Label("Select Year:"),
                            dcc.Dropdown(
                                id="year_dropdown",
                                clearable=False,
                            )
                        ], style={"marginBottom": "0.5rem"}),

                        html.Div(id='coverage_info', style={"marginTop": "0.5rem", "fontWeight": "600"}),
                    ])
                ])
            ]),

            # Graphs column
            html.Div(className="col-md-9", children=[
                html.Div(className="row g-4 gy-4", children=[
                    html.Div(className="col-md-6", children=[
                        html.Div(className="card mb-4", children=[
                            html.Div(className="card-body py-3", children=[
                                html.H6("Votes by Party (Animated)", className="card-title"),
                                dcc.Graph(id="bar_chart", style={"height": "450px"})
                            ])
                        ])
                    ]),

                    html.Div(className="col-md-6", children=[
                        html.Div(className="card mb-4", children=[
                            html.Div(className="card-body py-3", children=[
                                html.H6("Total Voter Turnout", className="card-title"),
                                dcc.Graph(id="line_chart", style={"height": "450px"})
                            ])
                        ])
                    ])
                ]),

                html.Div(className="row g-4 gy-4", children=[
                    html.Div(className="col-md-6", children=[
                        html.Div(className="card mb-4", children=[
                            html.Div(className="card-body py-3", children=[
                                html.H6("Winning Party by State", className="card-title"),
                                dcc.Graph(id="map_chart", style={"height": "520px"}),
                                html.Div(className="mt-2", children=[
                                    html.Span(style={
                                        "display": "inline-block",
                                        "width": "14px",
                                        "height": "14px",
                                        "backgroundColor": "blue",
                                        "marginRight": "6px",
                                        "borderRadius": "2px",
                                        "verticalAlign": "middle"
                                    }), html.Span(" Democrat", style={"marginRight": "12px"}),

                                    html.Span(style={
                                        "display": "inline-block",
                                        "width": "14px",
                                        "height": "14px",
                                        "backgroundColor": "red",
                                        "marginRight": "6px",
                                        "borderRadius": "2px",
                                        "verticalAlign": "middle"
                                    }), html.Span(" Republican", style={"marginRight": "12px"}),

                                    html.Span(style={
                                        "display": "inline-block",
                                        "width": "14px",
                                        "height": "14px",
                                        "backgroundColor": "lightgray",
                                        "marginRight": "6px",
                                        "borderRadius": "2px",
                                        "verticalAlign": "middle",
                                        "border": "1px solid #bbb"
                                    }), html.Span(" No Race", style={"marginRight": "6px"}),
                                    html.Span(id='no_race_count', style={"marginRight": "12px", "fontWeight": "600"}),

                                    html.Span("(States with no contest that year)", style={"color": "#666", "marginLeft": "8px"})
                                ])
                            ])
                        ])
                    ]),

                    html.Div(className="col-md-6", children=[
                        html.Div(className="card mb-4", children=[
                            html.Div(className="card-body py-3", children=[
                                html.H6("Vote Share by Party", className="card-title"),
                                dcc.Graph(id="pie_chart", style={"height": "450px"})
                            ])
                        ])
                    ])
                ])
            ])
        ])
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


@app.callback(
    Output('coverage_info', 'children'),
    Output('no_race_count', 'children'),
    Input('dataset_selector', 'value'),
    Input('year_dropdown', 'value')
)
def update_coverage_text(dataset, selected_year):
    # returns coverage text and optional no-race-count string (empty when none)
    if selected_year is None:
        return "", ""
    df = df_president if dataset == "president" else df_senate
    # find state column (state_po preferred)
    state_col = None
    for c in df.columns:
        if c.lower() == 'state_po':
            state_col = c
            break
    if state_col is None:
        for c in df.columns:
            if c.lower() == 'state':
                state_col = c
                break
    if state_col is None:
        return "", ""

    df_year = df[df['year'] == selected_year]
    present_states = set(df_year[state_col].dropna().unique())

    # determine display states for this dataset (dynamic inclusion like DC)
    display_states = get_display_states(df)
    # count states with data that match the postal codes we use for the map
    present_postal_count = sum(1 for s in display_states if s in present_states)
    total = len(display_states)
    no_race_count = total - present_postal_count

    ds_label = 'Presidential' if dataset == 'president' else 'Senate'
    coverage_text = f"{ds_label} races in {selected_year}: {present_postal_count} states"

    no_race_text = f"No Race: {no_race_count} states" if no_race_count > 0 else ""
    return coverage_text, no_race_text


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
