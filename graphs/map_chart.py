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


def create_flip_map(df, year_a, year_b):
    """Create a map showing states that flipped between year_a and year_b.

    Categories:
    - Stayed Democrat
    - Stayed Republican
    - Flipped to Democrat
    - Flipped to Republican
    - No Race
    """
    # winners for each year
    def winners_for_year(dframe, year):
        dfy = dframe[dframe['year'] == year]
        group_col = 'state' if 'state' in dfy.columns else ('state_po' if 'state_po' in dfy.columns else None)
        if group_col is None:
            raise ValueError('No state column found for flip map')
        idx = dfy.groupby(group_col)['candidatevotes'].idxmax()
        w = dfy.loc[idx].copy()
        if 'state_po' not in w.columns and 'state' in w.columns:
            w['state_po'] = w['state']
        return w[['state_po', 'party_simplified']].drop_duplicates(subset=['state_po']).set_index('state_po')

    w_a = winners_for_year(df, year_a)
    w_b = winners_for_year(df, year_b)

    # display states = union of display list and any states present in winners
    display_states = get_display_states(df)
    # ensure we include any postal codes present in data even if not in canonical list
    extra = set(w_a.index.tolist()) | set(w_b.index.tolist())
    for s in extra:
        if s and s not in display_states:
            display_states.append(s)

    all_df = pd.DataFrame({'state_po': display_states}).set_index('state_po')

    merged = all_df.join(w_a.rename(columns={'party_simplified': 'party_a'}))
    merged = merged.join(w_b.rename(columns={'party_simplified': 'party_b'}))

    def classify(row):
        a = row.get('party_a')
        b = row.get('party_b')
        if pd.isna(a) and pd.isna(b):
            return 'No Race'
        if pd.isna(a) and not pd.isna(b):
            return f'Flipped to {b}' if False else 'No Race'
        if not pd.isna(a) and pd.isna(b):
            return 'No Race'
        if a == b:
            return f'Stayed {a}'
        # both present and different -> flipped to b
        return f'Flipped to {b}'

    merged['status'] = merged.apply(classify, axis=1)

    # map statuses to colors
    color_map = {
        'Stayed Democrat': 'blue',
        'Stayed Republican': 'red',
        'Flipped to Democrat': 'purple',
        'Flipped to Republican': 'orange',
        'No Race': 'lightgray'
    }

    category_order = [
        'Stayed Democrat', 'Stayed Republican', 'Flipped to Democrat', 'Flipped to Republican', 'No Race'
    ]

    fig = px.choropleth(
        merged.reset_index(),
        locations='state_po',
        locationmode='USA-states',
        color='status',
        category_orders={'status': category_order},
        color_discrete_map=color_map,
        scope='usa',
        title=f'State Changes: {year_a} → {year_b}'
    )
    return fig
