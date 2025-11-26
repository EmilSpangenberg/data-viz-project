import plotly.express as px
import pandas as pd

# canonical 50 US states (postal codes)
US_50_STATES = [
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
    'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM',
    'NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA',
    'WV','WI','WY'
]


def get_display_states(df):
    """Return the list of state postal codes to display on the map.

    Includes the 50 US states by default and adds 'DC' if the dataset contains it.
    """
    display = list(US_50_STATES)
    # check for DC presence in state_po or state columns
    cols = [c for c in df.columns if c.lower() in ("state_po", "state")]
    if cols:
        vals = set()
        for c in cols:
            vals.update(x for x in df[c].dropna().astype(str).unique())
        if 'DC' in vals and 'DC' not in display:
            display.append('DC')
    return display

# keep a backwards-compatible name for simple imports
ALL_STATES = get_display_states


def create_map_chart(df, selected_year):
    df_year = df[df["year"] == selected_year]

    # choose a column to group by for winners (prefer `state`, but fallback to `state_po`)
    group_col = 'state' if 'state' in df_year.columns else ('state_po' if 'state_po' in df_year.columns else None)
    if group_col is None:
        raise ValueError('No state column found for map chart')

    # pick the candidate with max votes per state grouping
    winners_idx = df_year.groupby(group_col)["candidatevotes"].idxmax()
    winners = df_year.loc[winners_idx].copy()

    # ensure we have a `state_po` column for mapping; if not, try to map from `state`
    if 'state_po' not in winners.columns and 'state' in winners.columns:
        # assume state contains postal codes in that case
        winners['state_po'] = winners['state']

    # determine which states to show on the map (dynamic)
    display_states = get_display_states(df)
    all_df = pd.DataFrame({'state_po': display_states})

    # keep only state_po and party for winners
    winners_small = winners[['state_po', 'party_simplified']].drop_duplicates(subset=['state_po'])
    merged = all_df.merge(winners_small, on='state_po', how='left')
    merged['party_simplified'] = merged['party_simplified'].fillna('No Race')

    color_map = {
        'No Race': 'lightgray',
        'Democrat': 'blue',
        'Republican': 'red'
    }

    fig = px.choropleth(
        merged,
        locations="state_po",
        locationmode="USA-states",
        color="party_simplified",
        category_orders={"party_simplified": ["Democrat", "Republican", "No Race"]},
        color_discrete_map=color_map,
        scope="usa",
        title=f"Winning Party by State ({selected_year})"
    )
    return fig
