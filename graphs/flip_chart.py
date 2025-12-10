import pandas as pd
import plotly.express as px
from .map_chart import get_display_states


def _winners_by_state_year(df, group_col_preference=('state_po', 'state')):
    """Return a DataFrame indexed by (state_po, year) with party_simplified and candidatevotes."""
    # normalize column names
    cols = df.columns
    group_col = None
    for pref in group_col_preference:
        if pref in cols:
            group_col = pref
            break
    if group_col is None:
        # try case-insensitive
        for c in cols:
            if c.lower() in ('state_po', 'state'):
                group_col = c
                break
    if group_col is None:
        raise ValueError('No state column found')

    # For each year and state, pick row with max candidatevotes
    df = df.copy()
    df = df[df['candidatevotes'].notna()]
    idx = df.groupby([group_col, 'year'])['candidatevotes'].idxmax()
    winners = df.loc[idx, [group_col, 'year', 'party_simplified', 'candidatevotes']].copy()
    winners = winners.rename(columns={group_col: 'state_po'})
    winners['state_po'] = winners['state_po'].astype(str)
    winners = winners.set_index(['state_po', 'year'])
    return winners


def compute_flip_counts(df, start_year=None, end_year=None):
    """Compute number of flips per state between consecutive years within [start_year, end_year].

    Returns DataFrame with index state_po and columns: flip_count, years_covered
    """
    winners = _winners_by_state_year(df)

    # select year range
    years = sorted({y for (_, y) in winners.index})
    if not years:
        return pd.DataFrame(columns=['flip_count'])
    min_y, max_y = years[0], years[-1]
    if start_year is None:
        start_year = min_y
    if end_year is None:
        end_year = max_y
    years_range = [y for y in years if start_year <= y <= end_year]

    # pivot to state x years
    pivot = winners.reset_index().pivot_table(index='state_po', columns='year', values='party_simplified', aggfunc='first')

    # compute flips per state
    def count_flips(row):
        seq = [row.get(y) for y in years_range]
        # treat nan as no-race
        prev = None
        flips = 0
        for val in seq:
            if pd.isna(val):
                # no race, skip but set prev to None to avoid counting when race appears later
                prev = None
                continue
            if prev is None:
                prev = val
                continue
            if val != prev:
                flips += 1
                prev = val
        return flips

    flip_counts = pivot.apply(count_flips, axis=1).rename('flip_count')
    # ensure all display states present
    display_states = get_display_states(df)
    flip_counts = flip_counts.reindex(display_states).fillna(0).astype(int)

    return flip_counts.to_frame()


def create_flip_choropleth(df, start_year=None, end_year=None):
    counts = compute_flip_counts(df, start_year, end_year)
    counts = counts.reset_index().rename(columns={'index': 'state_po'})

    # choropleth by flip_count
    fig = px.choropleth(
        counts,
        locations='state_po',
        locationmode='USA-states',
        color='flip_count',
        color_continuous_scale='OrRd',
        scope='usa',
        title=f'Number of Party Flips ({start_year} → {end_year})' if start_year and end_year else 'Number of Party Flips'
    )
    fig.update_layout(coloraxis_colorbar=dict(title='Flip Count'))
    return fig


def create_flip_bar(df, start_year=None, end_year=None, top_n=15):
    counts = compute_flip_counts(df, start_year, end_year)
    counts = counts.reset_index().rename(columns={'index': 'state_po'})
    counts = counts.sort_values('flip_count', ascending=False).head(top_n)
    fig = px.bar(counts, x='flip_count', y='state_po', orientation='h', title='States Ranked by Flip Count')
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig
