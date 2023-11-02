import streamlit as st
import pandas as pd
from sklearn.linear_model import LinearRegression
import plotly.graph_objs as go
import plotly.express as px

from funcs import custom_groupby, files_to_dataframe, is_distance_within_range
import config

# Type hints
ship_type_agg: pd.DataFrame
ship_type_period_agg: pd.DataFrame
data_less_outliers: pd.DataFrame


# Constants
input_file_names = config.INPUT_FILES
columns_to_drop = config.COLUMNS_TO_DROP
ship_range_limits = config.SHIP_RANGE_LIMITS


# Script
st.title("Carbon Chain - Emissions Analysis")
st.sidebar.text("""
Short explainer

This data was cleaned. To do this I did the following:
1. Replaced N/A and "Division by zero!" values with NaN
2. Dropped unused columns (there were lots of them)
3. Imputed the effieciency DWT field with the the transport by mass field,
as the latter was more populated

You can and should interact with the data using the
legends and the Reporting Period filter. More analysis can be seen that way

Calculations:
Deadweight:
Total fuel consumption / Annual average Fuel consumption per transport work

Distance Travelled [n miles]:
Total fuel consumption / Annual average Fuel consumption per distance

Distance calculated by CO₂:
Total CO₂ emissions [m tonnes] / Annual average CO₂ emissions per distance

 """
                )

# Loading Data
data = files_to_dataframe(input_file_names, dropped_indexes=columns_to_drop)
data["Reporting Period"] = pd.to_datetime(
    data["Reporting Period"], format="%Y")

# Filtering data
selected_periods = st.sidebar.multiselect("Select Reporting Period(s)",
                                          data["Reporting Period"].unique())

if selected_periods:
    filtered_data = data[data["Reporting Period"].isin(selected_periods)]
else:
    filtered_data = data.copy()


# Calculating custom metrics
filtered_data["Distance Travelled [n miles]"] = (filtered_data["Total fuel consumption [m tonnes]"] * 1000
                                                 /
                                                 filtered_data["Annual average Fuel consumption per distance [kg / n mile]"]).round(2)

filtered_data["Distance calculated by CO₂"] = (filtered_data["Total CO₂ emissions [m tonnes]"] * 1000
                                               /
                                               filtered_data["Annual average CO₂ emissions per distance [kg CO₂ / n mile]"]).round(2)

filtered_data["Is Distance in Ship Type Range"] = filtered_data.apply(lambda row: is_distance_within_range(
    ship_range_limits, row["Ship type"], row["Distance Travelled [n miles]"])[0], axis=1)

filtered_data["Percent Diff"] = filtered_data.apply(lambda row: is_distance_within_range(
    ship_range_limits, row["Ship type"], row["Distance Travelled [n miles]"])[1], axis=1)

filtered_data["Deadweight"] = (filtered_data["Total fuel consumption [m tonnes]"]*1000
                               /
                               filtered_data["Annual average Fuel consumption per transport work"]).round(2)

ship_type_agg = custom_groupby(filtered_data,
                               "Ship type",
                               {"IMO Number": "nunique",
                                "Total CO₂ emissions [m tonnes]": "mean",
                                "Distance Travelled [n miles]": "mean",
                                "Annual average CO₂ emissions per distance [kg CO₂ / n mile]": "mean",
                                "Deadweight": "mean"
                                })

ship_type_period_agg = custom_groupby(filtered_data,
                                      ["Ship type", "Reporting Period"],
                                      {"IMO Number": "nunique",
                                          "Total CO₂ emissions [m tonnes]": "mean",
                                          "Annual average CO₂ emissions per distance [kg CO₂ / n mile]": "mean",
                                       })


# Question 1

# TODO: Turn plots into functions
fig = px.bar(
    ship_type_agg.sort_values(by="IMO Number",
                              ascending=False),
    x="Ship type",
    y="IMO Number",
    title="Ship Type vs Number of Ships"
)

fig.update_layout(height=600, width=800,
                  xaxis_title="Ship Type",
                  yaxis_title="Number of Ships")

st.plotly_chart(fig)

st.write("""
The bulk carriers are the most common ship type,
followed by the oil tanker and the container ship.
The number of ships is unevenly distributed across the different ship types,
with the bulk carriers accounting for over a third of all ships.
"""
         )


# Question 2
fig1 = go.Figure()

fig1.add_traces(
    go.Bar(
        x=ship_type_agg.sort_values(by="Total CO₂ emissions [m tonnes]",
                                    ascending=False)["Ship type"],
        y=ship_type_agg["Annual average CO₂ emissions per distance [kg CO₂ / n mile]"],
        name="CO₂ emissions per distance"
    )
)

fig1.update_layout(height=600, width=800,
                   xaxis_title="Ship Type",
                   yaxis_title="Avg CO₂ Emissions per unit distance",
                   title="Ship Type vs CO₂ Emissions"
                   )

st.plotly_chart(fig1)
st.write("""
Gas Carriers, Oil Tankers and Vehicle Carriers appear to emit the most
CO₂ per unit distance. This could be due to the fact they all carry
highly pollutant goods. These ships are generally large and require a lot
of fuel to power, added to the pollutants these ships can produce.
""")


fig2 = px.line(
    ship_type_period_agg.sort_values(by="Reporting Period"),
    x="Reporting Period",
    y="Total CO₂ emissions [m tonnes]",
    color="Ship type"
)

totals = custom_groupby(ship_type_period_agg,
                        'Reporting Period',
                        {'Total CO₂ emissions [m tonnes]': 'sum'}
                        )

fig2.add_trace(
  go.Scatter(
    x=totals["Reporting Period"], 
    y=totals["Total CO₂ emissions [m tonnes]"],
    name="Overall",
    line=dict(color='white', width=4)
  )
)

fig2.update_layout(height=600, width=800,
                   title="CO₂ emissions over time",
                   xaxis_title="Ship Type",
                   yaxis_title="Average Annual CO₂ Emissions")

st.plotly_chart(fig2)
st.write("""
Shipping industry is a major contributor to climate change,
but CO2 emissions are decreasing. This looks to be mainly driven by
passenger ships and LNG carriers - although the dip in 2020 was mostly
due to covid. The rate of decrease in CO2 emissions has slowed in
recent years, and has even started ticking up.
""")


# Question 3
# Removing outliers to find corrolation between deadweight and emission intensity
data_less_outliers = filtered_data[(filtered_data["Deadweight"] < 10000000)
                                   &
                                   (filtered_data["Annual average CO₂ emissions per distance [kg CO₂ / n mile]"] < 1000)]

# Regression
X = data_less_outliers["Deadweight"].values.reshape(-1, 1)
y = data_less_outliers["Annual average CO₂ emissions per distance [kg CO₂ / n mile]"].values

model = LinearRegression()
model.fit(X, y)

r_sq = model.score(X, y)

# Plotting data without outliers and regression of Deadweight vs
fig3 = px.scatter(data_less_outliers,
                  x="Deadweight",
                  y="Annual average CO₂ emissions per distance [kg CO₂ / n mile]",
                  title="Deadweight vs Co₂ Emission Intensity",
                  color="Ship type",
                  opacity=0.5
                  )
# Add a trendline to the scatter plot
fig3.add_traces(
    go.Scatter(
        x=X.reshape(-1),
        y=model.predict(X),
        name="Trendline",
        line=dict(color='limegreen', width=4)

    )
)

fig3.update_layout(height=600, width=800,
                   xaxis_title="Deadweight (Tonnes)",
                   yaxis_title="CO₂ Emissions per Distance Travelled (kg/n miles)")

st.plotly_chart(fig3)

st.write(
    f"""
    The graph shows that CO₂ intensity tends to increase with deadweight.
    This is backed by a coefficient of determination of {r_sq:.3}.
    This is likely due to larger ships being less efficient,
    having more powerful engines, and traveling at higher speeds.
    """
)

# Question 4
st.write(
    filtered_data[["IMO Number",
                   "Ship type",
                   "Name",
                   "Distance Travelled [n miles]",
                   "Distance calculated by CO₂",
                   "Is Distance in Ship Type Range",
                   "Percent Diff"]],
    """
The __Distance Travelled [n miles]__ was calculated using the
total fuel consumed and the amount of fuel consumed per unit 
distance (annually).
This closely agrees with the __Distance calculated by CO₂__,
which was calculated using total CO₂ emissions and
average CO₂ emissions per distance (annually). This distance is not
always within the typical range for the ship type, which infers it may not be
an exact representation of the ship"s activity.
The __Percent Diff__ column quantifies how
far outside or inside the typical range the calculated distance falls.
"""
)
