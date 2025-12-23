import pandas as pd
from shiny import App, render, ui, reactive
from shinywidgets import render_plotly, output_widget

from graphs.bar_chart import create_bar_chart
from graphs.line_chart import create_line_chart
from graphs.map_chart import create_map_chart, get_display_states
from graphs.pie_chart import create_pie_chart
from graphs.state_split_chart import create_state_split_chart
from graphs.boxplot_chart import create_boxplot_by_party


def _load_and_prepare(path: str) -> pd.DataFrame:
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
        from io import StringIO
        with open(path, "rb") as f:
            raw = f.read()
        text = raw.decode("utf-8", errors="replace")
        df = pd.read_csv(StringIO(text), engine="python", sep=",", quotechar='"', skipinitialspace=True, on_bad_lines="skip")
        used_encoding = "utf-8 (errors=replace, python engine)"

    df = df[df["party_simplified"].notna()].copy()
    df.columns = [str(c).strip().strip('"').strip() for c in df.columns]
    for col in df.select_dtypes(include=[object]).columns:
        df[col] = df[col].astype(str).str.strip().str.strip('"').str.strip()

    party_col = None
    for c in df.columns:
        if c.lower() == "party_simplified":
            party_col = c
            break
    if party_col is None:
        for c in df.columns:
            if "party" in c.lower():
                party_col = c
                break
    if party_col is None:
        raise ValueError(f"party_simplified column not found in {path}; columns: {df.columns.tolist()}")

    df = df[df[party_col].notna()].copy()

    def _norm_party(p):
        s = str(p).lower()
        if s == "democrat":
            return "Democrat"
        if s == "republican":
            return "Republican"
        return s.title()

    df["party_simplified"] = df[party_col].apply(_norm_party)

    try:
        print(f"Loaded {path} using encoding: {used_encoding}")
    except Exception:
        pass

    return df


# --- Load datasets ---
df_president = _load_and_prepare("dataset/1976-2020-president.csv")
df_senate = _load_and_prepare("dataset/1976-2020-senate.csv")

# --- Years ---
president_years = sorted(df_president["year"].unique())
senate_years = sorted(df_senate["year"].unique())

# --- Helpers ---
def _find_state_col(df: pd.DataFrame) -> str | None:
    for c in df.columns:
        if c.lower() == 'state_po':
            return c
    for c in df.columns:
        if c.lower() == 'state':
            return c
    return None


# --- UI ---
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/bootswatch@5.2.3/dist/flatly/bootstrap.min.css")
    ),

    ui.tags.nav(
        {"class": "navbar navbar-dark bg-primary"},
        ui.div({"class": "container"}, ui.tags.span("US Elections Dashboard (1976–2020)", {"class": "navbar-brand mb-0 h1"}))
    ),

    ui.div(
        {"class": "container-fluid my-4"},
        # Controls section at the top (dataset only)
        ui.row(
            ui.column(
                12,
                ui.div(
                    {"class": "card mb-4"},
                    ui.div(
                        {"class": "card-body py-3"},
                        ui.tags.h5("Select Dataset", {"class": "card-title mb-3"}),
                        ui.div(
                            {"style": "margin-bottom: 0.5rem;"},
                            ui.input_radio_buttons(
                                "dataset_selector",
                                None,
                                {"president": "Presidential (1976–2020)", "senate": "Senate (1976–2020)"},
                                selected="president",
                                inline=True,
                            ),
                        ),
                    ),
                ),
            ),
        ),
        # Graphs section
        ui.row(
            ui.column(
                6,
                ui.div(
                    {"class": "card mb-4"},
                    ui.div(
                        {"class": "card-body py-3"},
                        ui.tags.h6("Votes by Party", {"class": "card-title"}),
                        ui.div(
                            {"style": "margin-bottom: 0.5rem;"},
                            ui.input_select("bar_year", None, {str(max(president_years)): str(max(president_years))}, selected=str(max(president_years)))
                        ),
                        output_widget("bar_chart", height="450px")
                    ),
                ),
            ),
            ui.column(
                6,
                ui.div(
                    {"class": "card mb-4"},
                    ui.div({"class": "card-body py-3"}, ui.tags.h6("Total Voter Turnout", {"class": "card-title"}), output_widget("line_chart", height="450px")),
                ),
            ),
        ),
        ui.row(
            ui.column(
                6,
                ui.div(
                    {"class": "card mb-4"},
                    ui.div(
                        {"class": "card-body py-3"},
                        ui.tags.h6("Vote Distribution by Party", {"class": "card-title"}),
                        ui.div(
                            {"style": "margin-bottom: 0.5rem;"},
                            ui.input_select("boxplot_year", None, {str(max(president_years)): str(max(president_years))}, selected=str(max(president_years)))
                        ),
                        output_widget("boxplot_chart", height="450px")
                    ),
                ),
            ),
            ui.column(
                6,
                ui.div(
                    {"class": "card mb-4"},
                    ui.div(
                        {"class": "card-body py-3"},
                        ui.tags.h6("State Vote Split (Republican vs Democrat)", {"class": "card-title"}),
                        ui.div(
                            {"style": "margin-bottom: 0.5rem;"},
                            ui.input_select("split_year", None, {str(max(president_years)): str(max(president_years))}, selected=str(max(president_years)))
                        ),
                        ui.div(
                            {"style": "max-height: 520px; overflow-y: auto; padding-right: 6px;"},
                            output_widget("state_split_chart", height="1200px")
                        )
                    ),
                ),
            ),
        ),
        ui.row(
            ui.column(
                6,
                ui.div(
                    {"class": "card mb-4"},
                    ui.div(
                        {"class": "card-body py-3"},
                        ui.tags.h6("Winning Party by State", {"class": "card-title"}),
                        ui.row(
                            ui.column(
                                6,
                                ui.div(
                                    {"style": "margin-bottom: 0.5rem;"},
                                    ui.tags.label("Select Year:"),
                                    ui.input_select("map_year", None, {str(max(president_years)): str(max(president_years))}, selected=str(max(president_years)))
                                )
                            ),
                            ui.column(
                                6,
                                ui.div(
                                    {"style": "margin-bottom: 0.5rem;"},
                                    ui.tags.label("Compare Year (optional):"),
                                    ui.input_select("map_compare_year", None, {"": "(None)"}, selected=""),
                                    ui.tags.small(
                                        "Select a second year to highlight states that flipped between the selected year and the compare year. Leave empty to show a single-year map.",
                                        {"style": "display:block; color:#666; margin-top: 4px;"}
                                    )
                                )
                            )
                        ),
                        output_widget("map_chart", height="520px"),
                        ui.div(
                            {"class": "mt-2"},
                            ui.tags.span(style="display: inline-block; width: 14px; height: 14px; background-color: blue; margin-right: 6px; border-radius: 2px; vertical-align: middle;"),
                            ui.tags.span(" Democrat", style="margin-right: 12px;"),
                            ui.tags.span(style="display: inline-block; width: 14px; height: 14px; background-color: red; margin-right: 6px; border-radius: 2px; vertical-align: middle;"),
                            ui.tags.span(" Republican", style="margin-right: 12px;"),
                            ui.output_ui("no_race_legend", inline=True, style="margin-right: 12px;"),
                            ui.output_ui("no_race_count", inline=True, style="font-weight: 600;"),
                        ),
                    ),
                ),
            ),
            ui.column(
                6,
                ui.div(
                    {"class": "card mb-4"},
                    ui.div(
                        {"class": "card-body py-3"},
                        ui.tags.h6("Vote Share by Party", {"class": "card-title"}),
                        ui.div(
                            {"style": "margin-bottom: 0.5rem;"},
                            ui.input_select("pie_year", None, {str(max(president_years)): str(max(president_years))}, selected=str(max(president_years)))
                        ),
                        output_widget("pie_chart", height="450px")
                    ),
                ),
            ),
        ),
        # Flip analysis grouped section (map + ranked bar + slider + description)
        ui.output_ui("flip_card"),
    ),
)


# --- Server ---
def server(input, output, session):
    @reactive.Calc
    def current_df():
        return df_president if input.dataset_selector() == "president" else df_senate

    @reactive.Calc
    def current_years():
        return president_years if input.dataset_selector() == "president" else senate_years

    @reactive.Effect
    def _update_controls():
        years = current_years()
        choices = {str(y): str(y) for y in years}
        # Update per-graph selects
        ui.update_select("bar_year", choices=choices, selected=str(max(years)) if years else None)
        ui.update_select("map_year", choices=choices, selected=str(max(years)) if years else None)
        compare_choices = {"": "(None)"}
        compare_choices.update(choices)
        compare_default = str(years[-2]) if len(years) >= 2 else ""
        ui.update_select("map_compare_year", choices=compare_choices, selected=compare_default)
        ui.update_select("pie_year", choices=choices, selected=str(max(years)) if years else None)
        ui.update_select("boxplot_year", choices=choices, selected=str(max(years)) if years else None)
        ui.update_select("split_year", choices=choices, selected=str(max(years)) if years else None)
        if years and input.dataset_selector() == "president":
            ui.update_slider("flip_range", min=int(min(years)), max=int(max(years)), value=[int(min(years)), int(max(years))], step=1, label="Flip year range")

    @output
    @render.ui
    def coverage_info():
        # Deprecated global coverage info; keep empty or remove if desired
        return ""

    @output
    @render.ui
    def no_race_count():
        if input.dataset_selector() != 'senate':
            return ""
        if not input.map_year():
            return ""
        selected_year = int(input.map_year())
        df = current_df()
        state_col = _find_state_col(df)
        if state_col is None:
            return ""
        df_year = df[df['year'] == selected_year]
        present_states = set(df_year[state_col].dropna().unique())
        display_states = get_display_states(df)
        present_postal_count = sum(1 for s in display_states if s in present_states)
        total = len(display_states)
        no_race_count = total - present_postal_count
        return f"No Race: {no_race_count} states" if no_race_count > 0 else ""

    @output
    @render.ui
    def no_race_legend():
        if input.dataset_selector() != 'senate':
            return ""
        return ui.div(
            ui.tags.span(style="display: inline-block; width: 14px; height: 14px; background-color: lightgray; margin-right: 6px; border-radius: 2px; vertical-align: middle; border: 1px solid #bbb;"),
            ui.tags.span(" No Race")
        )

    @output
    @render_plotly
    def bar_chart():
        df = current_df()
        selected_year = input.bar_year()
        return create_bar_chart(df, int(selected_year) if selected_year else None)

    @output
    @render_plotly
    def line_chart():
        df = current_df()
        return create_line_chart(df)

    @output
    @render_plotly
    def map_chart():
        if not input.map_year():
            from plotly import graph_objs as go
            return go.Figure()
        selected_year = int(input.map_year())
        df = current_df()
        if input.map_compare_year() and input.map_compare_year() != "":
            compare_year = int(input.map_compare_year())
            if compare_year != selected_year:
                from graphs.map_chart import create_flip_map
                return create_flip_map(df, selected_year, compare_year)
        return create_map_chart(df, selected_year)

    @output
    @render_plotly
    def pie_chart():
        if not input.pie_year():
            from plotly import graph_objs as go
            return go.Figure()
        selected_year = int(input.pie_year())
        df = current_df()
        return create_pie_chart(df, selected_year)

    @output
    @render_plotly
    def state_split_chart():
        df = current_df()
        selected_year = input.split_year()
        return create_state_split_chart(df, int(selected_year) if selected_year else None)

    @output
    @render_plotly
    def boxplot_chart():
        df = current_df()
        selected_year = input.boxplot_year()
        return create_boxplot_by_party(df, int(selected_year) if selected_year else None)

    @output
    @render.ui
    def flip_card():
        if input.dataset_selector() != "president":
            return ""
        return ui.div(
            {"class": "card mb-4"},
            ui.div(
                {"class": "card-body py-3"},
                ui.tags.h6("Flip Analysis", {"class": "card-title"}),
                ui.div(
                    {"class": "row g-4 gy-4"},
                    ui.column(7, output_widget("flip_map", height="520px")),
                    ui.column(5, output_widget("flip_bar", height="520px")),
                ),
                ui.div(
                    {"class": "alert alert-secondary py-2", "style": "margin-top: 0.5rem; margin-bottom: 0.5rem;"},
                    "Choose start and end years to inspect specific yearly intervals of party flips."
                ),
                ui.input_slider(
                    "flip_range",
                    "Flip year range",
                    min=min(president_years),
                    max=max(president_years),
                    value=[min(president_years), max(president_years)],
                    step=1,
                    width="100%"
                )
            )
        )

    @output
    @render_plotly
    def flip_map():
        dataset = input.dataset_selector()
        if dataset == 'senate':
            from plotly import graph_objs as go
            fig_note = go.Figure()
            fig_note.add_annotation(text="Flip visualization not applicable for the Senate (staggered 6-year terms).", x=0.5, y=0.5, xref='paper', yref='paper', showarrow=False, font=dict(size=14, color="#444"))
            fig_note.update_layout(title='Cumulative Flip Map', template='plotly_white')
            return fig_note
        if not input.flip_range():
            from plotly import graph_objs as go
            return go.Figure()
        start_year, end_year = map(int, input.flip_range())
        if start_year > end_year:
            start_year, end_year = end_year, start_year
        df = current_df()
        from graphs.flip_chart import create_flip_choropleth
        return create_flip_choropleth(df, start_year, end_year)

    @output
    @render_plotly
    def flip_bar():
        dataset = input.dataset_selector()
        if dataset == 'senate':
            from plotly import graph_objs as go
            fig_bar = go.Figure()
            fig_bar.add_annotation(text="No flip data for Senate — see explanation.", x=0.5, y=0.5, xref='paper', yref='paper', showarrow=False, font=dict(size=12, color="#444"))
            fig_bar.update_layout(title='States Ranked by Flips', template='plotly_white')
            return fig_bar
        if not input.flip_range():
            from plotly import graph_objs as go
            return go.Figure()
        start_year, end_year = map(int, input.flip_range())
        if start_year > end_year:
            start_year, end_year = end_year, start_year
        df = current_df()
        from graphs.flip_chart import create_flip_bar
        return create_flip_bar(df, start_year, end_year)

    @reactive.Effect
    def _disable_flip_controls():
        ds = input.dataset_selector()
        if ds != 'president':
            return
        session.send_input_message("flip_range", {"disabled": False})


app = App(app_ui, server)
