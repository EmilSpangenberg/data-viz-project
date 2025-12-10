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

                        html.Div([
                            html.Label("Compare Year (optional):"),
                            dcc.Dropdown(
                                id="compare_year_dropdown",
                                clearable=True,
                            )
                        ], style={"marginBottom": "0.5rem"}),

                        html.Div([
                            html.Label("Flip Start Year:"),
                            dcc.Dropdown(
                                id="flip_start_year",
                                clearable=False,
                            )
                        ], style={"marginBottom": "0.5rem"}),

                        html.Div([
                            html.Label("Flip End Year:"),
                            dcc.Dropdown(
                                id="flip_end_year",
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
                ]),

                # Flip map + ranked bar
                html.Div(className="row g-4 gy-4 mt-3", children=[
                    html.Div(className="col-md-7", children=[
                        html.Div(className="card mb-4", children=[
                            html.Div(className="card-body py-3", children=[
                                html.H6("Cumulative Flip Map", className="card-title"),
                                dcc.Graph(id="flip_map", style={"height": "520px"})
                            ])
                        ])
                    ]),

                    html.Div(className="col-md-5", children=[
                        html.Div(className="card mb-4", children=[
                            html.Div(className="card-body py-3", children=[
                                html.H6("States Ranked by Flips", className="card-title"),
                                dcc.Graph(id="flip_bar", style={"height": "520px"})
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
    Output("compare_year_dropdown", "options"),
    Output("compare_year_dropdown", "value"),
    Output("flip_start_year", "options"),
    Output("flip_start_year", "value"),
    Output("flip_end_year", "options"),
    Output("flip_end_year", "value"),
    Input("dataset_selector", "value")
)
def update_year_options(dataset):
    df = df_president if dataset == "president" else df_senate
    years = sorted(df["year"].unique())
    default = max(years) if len(years) else None
    # set compare default to the previous available year if possible
    compare_default = years[-2] if len(years) >= 2 else None
    start_default = years[0] if len(years) else None
    end_default = years[-1] if len(years) else None
    options = [{"label": y, "value": y} for y in years]
    return options, default, options, compare_default, options, start_default, options, end_default


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
    Input("year_dropdown", "value"),
    Input("compare_year_dropdown", "value")
)
def update_map_chart(dataset, selected_year, compare_year):
    df = df_president if dataset == "president" else df_senate
    # if compare_year provided and different from selected_year, show flip/swing map
    if compare_year and selected_year and compare_year != selected_year:
        from graphs.map_chart import create_flip_map
        return create_flip_map(df, selected_year, compare_year)
    return create_map_chart(df, selected_year)


@app.callback(
    Output("pie_chart", "figure"),
    Input("dataset_selector", "value"),
    Input("year_dropdown", "value")
)
def update_pie_chart(dataset, selected_year):
    df = df_president if dataset == "president" else df_senate
    return create_pie_chart(df, selected_year)


@app.callback(
    Output('flip_map', 'figure'),
    Output('flip_bar', 'figure'),
    Input('dataset_selector', 'value'),
    Input('flip_start_year', 'value'),
    Input('flip_end_year', 'value')
)
def update_flip_views(dataset, start_year, end_year):
    # For the Senate dataset, flips across consecutive elections are not meaningful
    # because only ~1/3 of seats are contested each cycle (6-year terms). Show
    # an explanatory placeholder and disable flip calculations.
    if dataset == 'senate':
        # create simple placeholder figures without importing heavy modules
        from plotly import graph_objs as go
        fig_note = go.Figure()
        fig_note.add_annotation(text="Flip visualization not applicable for the Senate (staggered 6-year terms).",
                                x=0.5, y=0.5, xref='paper', yref='paper', showarrow=False,
                                font=dict(size=14, color="#444"))
        fig_note.update_layout(title='Cumulative Flip Map', template='plotly_white')

        fig_bar = go.Figure()
        fig_bar.add_annotation(text="No flip data for Senate — see explanation.", x=0.5, y=0.5,
                               xref='paper', yref='paper', showarrow=False,
                               font=dict(size=12, color="#444"))
        fig_bar.update_layout(title='States Ranked by Flips', template='plotly_white')
        return fig_note, fig_bar

    df = df_president if dataset == 'president' else df_senate
    from graphs.flip_chart import create_flip_choropleth, create_flip_bar
    # defensive: if start/end missing, pass None so functions pick defaults
    return create_flip_choropleth(df, start_year, end_year), create_flip_bar(df, start_year, end_year)


@app.callback(
    Output('flip_start_year', 'disabled'),
    Output('flip_end_year', 'disabled'),
    Input('dataset_selector', 'value')
)
def disable_flip_controls(dataset):
    # Disable flip range controls for Senate because flips across consecutive cycles are not meaningful
    disabled = True if dataset == 'senate' else False
    return disabled, disabled


# --- Run server ---
if __name__ == "__main__":
    app.run(debug=True)
