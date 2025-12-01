import streamlit as st
import duckdb
import pandas as pd

# ---------- CONFIG ----------
DB_PATH = "natural_gas.duckdb"  # relative to project root


STATE_ABBREV = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "District of Columbia": "DC",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}


# ---------- HELPER FUNCTIONS ----------
@st.cache_data
def get_states():
    con = duckdb.connect(DB_PATH, read_only=True)
    df = con.execute("SELECT DISTINCT state FROM gas_long ORDER BY state").df()
    con.close()
    return df["state"].tolist()


@st.cache_data
def get_date_bounds():
    con = duckdb.connect(DB_PATH, read_only=True)
    row = con.execute("""
        SELECT MIN(Date) AS min_date, MAX(Date) AS max_date
        FROM gas_long
    """).df().iloc[0]
    con.close()
    return row["min_date"], row["max_date"]


@st.cache_data
def query_data(selected_states, start_date, end_date, agg_level):
    """
    Query gas_long for the selected states and date range.
    agg_level: 'Monthly' or 'Annual'
    """
    con = duckdb.connect(DB_PATH, read_only=True)

    placeholders = ", ".join(["?"] * len(selected_states))

    if agg_level == "Monthly":
        sql = f"""
            SELECT 
                Date,
                state,
                value
            FROM gas_long
            WHERE state IN ({placeholders})
              AND Date BETWEEN ? AND ?
            ORDER BY Date, state
        """
    else:  # Annual
        sql = f"""
            SELECT 
                DATE_TRUNC('year', Date)::DATE AS Date,
                state,
                SUM(value) AS value
            FROM gas_long
            WHERE state IN ({placeholders})
              AND Date BETWEEN ? AND ?
            GROUP BY Date, state
            ORDER BY Date, state
        """

    params = (*selected_states, start_date, end_date)
    df = con.execute(sql, params).df()
    con.close()
    return df

@st.cache_data
def get_map_data(start_date, end_date, agg_level):
    con = duckdb.connect(DB_PATH, read_only=True)

    if agg_level == "Monthly":
        # Sum raw monthly values over the date range
        query = """
            SELECT
                state,
                SUM(value) AS total_mmcf
            FROM gas_long
            WHERE Date BETWEEN ? AND ?
            GROUP BY state
        """
    else:
        # First aggregate to annual by state, then sum across years in range
        query = """
            WITH annual AS (
                SELECT
                    DATE_TRUNC('year', Date)::DATE AS year,
                    state,
                    SUM(value) AS annual_mmcf
                FROM gas_long
                WHERE Date BETWEEN ? AND ?
                GROUP BY year, state
            )
            SELECT
                state,
                SUM(annual_mmcf) AS total_mmcf
            FROM annual
            GROUP BY state
        """

    df = con.execute(query, [start_date, end_date]).df()
    con.close()

    # Map full state name -> 2-letter code
    df["state_code"] = df["state"].map(STATE_ABBREV)
    df = df.dropna(subset=["state_code"])

    return df



# ---------- APP LAYOUT ----------
st.set_page_config(
    page_title="U.S. Natural Gas Demand Dashboard",
    layout="wide"
)

st.title("U.S. Natural Gas Demand Dashboard")
st.caption(
    "Monthly natural gas delivered to consumers by state (MMcf). "
    "Historical data only for now – forecasts will be added later."
)

# Sidebar controls
states = get_states()
min_date, max_date = get_date_bounds()

# Ensure we have Python dates (not pandas Timestamps)
min_date = pd.to_datetime(min_date).date()
max_date = pd.to_datetime(max_date).date()

with st.sidebar:
    st.header("Filters")

    selected_states = st.multiselect(
        "Select states",
        options=states,
        default=["Texas", "US_Total"] if "US_Total" in states else ["Texas"]
    )

    start_date, end_date = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    agg_level = st.radio(
        "Aggregation level",
        ["Monthly", "Annual"],
        index=0,
        help="Monthly shows raw monthly series; Annual aggregates to yearly totals."
    )

    st.markdown("---")
    st.write("Data source: EIA – delivered to consumers (MMcf).")


if not selected_states:
    st.warning("Please select at least one state.")
    st.stop()

# Query data from DuckDB
df = query_data(selected_states, start_date, end_date, agg_level)

if df.empty:
    st.warning("No data for this selection.")
    st.stop()

# ---------- MAIN CHART ----------
st.subheader(f"Natural Gas Demand ({agg_level})")

# Use Plotly for interactive chart
import plotly.express as px

fig = px.line(
    df,
    x="Date",
    y="value",
    color="state",
    markers=True,
    labels={
        "Date": "Date",
        "value": "Demand (MMcf)",
        "state": "State"
    },
    title=f"Natural Gas Delivered to Consumers ({agg_level})"
)
st.plotly_chart(fig, use_container_width=True)


# ---------- SUMMARY TABLE ----------
st.subheader("Summary statistics for selected period")

summary = (
    df.groupby("state")["value"]
    .agg(total_mmcf="sum", avg_mmcf="mean", max_mmcf="max", min_mmcf="min")
    .reset_index()
    .sort_values("total_mmcf", ascending=False)
)

st.dataframe(summary, use_container_width=True)

# ---------- OPTIONAL: TOP STATES BAR CHART ----------
st.subheader("Total demand by state (selected period)")

fig_bar = px.bar(
    summary,
    x="state",
    y="total_mmcf",
    labels={"total_mmcf": "Total demand (MMcf)", "state": "State"},
)
st.plotly_chart(fig_bar, use_container_width=True)

# ---------- US MAP ----------
st.subheader("Total natural gas delivered to consumers by state (map)")
st.caption(f"Aggregated MMcf between {start_date} and {end_date}")

df_map = get_map_data(start_date, end_date, agg_level)

if df_map.empty:
    st.warning("No data available for this date range.")
else:
    fig_map = px.choropleth(
        df_map,
        locations="state_code",
        locationmode="USA-states",
        color="total_mmcf",
        scope="usa",
        hover_name="state",
        hover_data={"state_code": False, "total_mmcf": ":,"},
        labels={"total_mmcf": "Total MMcf"},
    )
    fig_map.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        coloraxis_colorbar=dict(title="MMcf"),
    )
    st.plotly_chart(fig_map, use_container_width=True)
