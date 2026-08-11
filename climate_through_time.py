import pandas as pd
import plotly.express as px

"""
Climate Through Time

This project visualizes how temperatures have changed across countries
relative to the pre-industrial period (1850–1900).
"""

# ============================
# Project constants
# ============================

BASELINE_START = 1850
BASELINE_END = 1900
START_YEAR = 1900
BACKUP_YEARS = 30
COLOR_LIMIT = 3.15

# ============================
# Load and prepare data
# ============================

# Read the temperature dataset
temperature = pd.read_csv("GlobalLandTemperaturesByCountry.csv")

# Convert the date column to datetime format
temperature["dt"] = pd.to_datetime(temperature["dt"])

# Extract the year
temperature["Year"] = temperature["dt"].dt.year

# Remove missing temperature values
temperature = temperature.dropna(subset=["AverageTemperature"])

# Calculate the average yearly temperature for each country
yearly = (
    temperature
    .groupby(["Country", "Year"])["AverageTemperature"]
    .mean()
    .reset_index()
)

# ============================
# Calculate baseline temperature
# ============================

# Step A: Attempt to get the standard pre-industrial average (1850–1900)
baseline_pre_industrial = (
    yearly[
        yearly["Year"].between(BASELINE_START, BASELINE_END)
    ]
    .groupby("Country")["AverageTemperature"]
    .mean()
    .reset_index(name="BaselineTemperature")
)

# Step B: Backup calculation using the first 30 available yearly records
baseline_backup = (
    yearly
    .groupby("Country")
    .head(BACKUP_YEARS)
    .groupby("Country")["AverageTemperature"]
    .mean()
    .reset_index(name="BackupBaseline")
)

# Step C: Use the pre-industrial baseline whenever available;
# otherwise use the backup baseline.
baseline = pd.merge(
    baseline_backup,
    baseline_pre_industrial,
    on="Country",
    how="left"
)

baseline["BaselineTemperature"] = (
    baseline["BaselineTemperature"]
    .fillna(baseline["BackupBaseline"])
    .round(2)
)

# Keep only the required columns
baseline = baseline[
    [
        "Country",
        "BaselineTemperature"
    ]
]

# ============================
# Merge yearly data with baseline
# ============================

merged = yearly.merge(
    baseline,
    on="Country",
    how="left"
)

# Keep data from 1900 onwards
merged = merged[
    merged["Year"] >= START_YEAR
]

# Convert each year into its decade
merged["Decade"] = merged["Year"] // 10 * 10

# ============================
# Calculate average temperature for each decade
# ============================

decade = (
    merged
    .groupby(
        [
            "Country",
            "Decade",
            "BaselineTemperature"
        ]
    )["AverageTemperature"]
    .mean()
    .round(2)
    .reset_index()
)

# Calculate temperature anomaly
decade["TempChange"] = (
    decade["AverageTemperature"]
    - decade["BaselineTemperature"]
).round(2)

# Keep only the required columns
map_data = decade[
    [
        "Country",
        "Decade",
        "TempChange"
    ]
].copy()

# Remove continents
regions_to_remove = [
    "Africa",
    "Asia",
    "Europe",
    "North America",
    "South America",
    "Oceania"
]

map_data = map_data[
    ~map_data["Country"].isin(regions_to_remove)
]

# ============================
# Create interactive map
# ============================

fig = px.choropleth(
    map_data,
    locations="Country",
    locationmode="country names",
    color="TempChange",
    hover_name="Country",
    hover_data={
        "Decade": False,
        "TempChange": ":.2f"
    },
    animation_frame="Decade",
    color_continuous_scale=[
        [0.0, "#053061"],   # Deepest Blue (at -3.15)
        [0.45, "#4393c3"],  # Light Blue
        [0.5, "#ffffff"],   # Pure White (exactly at 0.0)
        [0.55, "#f4a582"],  # Light Orange/Red
        [1.0, "#67001f"]    # Deepest Red (at +3.15)
    ],
    range_color=(-COLOR_LIMIT, COLOR_LIMIT),
    labels={
        "TempChange": "Temperature Anomaly (°C)"
    },
    title=(
        "<span style='font-size: 32px;'><b>Climate Through Time: Global Temperature Anomalies</b></span>"
        "<br><sup style='font-size: 22px; color: #444444; font-weight: normal;'>"
        "Temperature anomalies relative to the 1850–1900 pre-industrial baseline."
        "</sup>"
    )
)

# Refined layout
fig.update_layout(
    width=1400,
    height=800,
    margin=dict(
        l=40,
        r=40,
        t=110,
        b=60
    ),
    # Global font config: automatically scales up the slider years and labels
    font=dict(
        family="Arial, sans-serif",
        size=16
    ),
    title_font_size=32,
    geo=dict(
        domain=dict(
            x=[0.06, 0.92],
            y=[0.02, 0.98]
        )
    ),
    coloraxis_colorbar=dict(
        title=dict(
            text="Temperature Anomaly (°C)",
            font=dict(size=16)  # Larger colorbar title text
        ),
        tickfont=dict(size=14),  # Larger colorbar scale numbers (-3, -2, -1...)
        thicknessmode="pixels",
        thickness=22,           # Slightly thicker bar for better readability
        lenmode="pixels",
        len=450,                # Taller bar to match the map scale nicely
        yanchor="middle",
        y=0.50,
        x=0.94
    )
)


# Enhanced map appearance
fig.update_geos(
    showcountries=True,
    countrycolor="#444444",
    showcoastlines=True,
    coastlinecolor="#888888",
    showland=True,
    landcolor="#F3F3F3",
    showocean=True,
    oceancolor="#EAF2F8",
    fitbounds="locations"
)

# Slow down the animation
fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 800
fig.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 300

# Save the map
fig.write_html(
    "climate_through_time.html",
    include_plotlyjs="cdn",
    auto_open=True
)

# Display the map
fig.show()