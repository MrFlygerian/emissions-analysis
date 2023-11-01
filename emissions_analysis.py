import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

import altair as alt
from plotly.subplots import make_subplots
import plotly.offline as py
import plotly.graph_objs as go
import plotly.express as px

from funcs import custom_groupby, files_to_dataframe, is_within_range
import config

# Constants
input_file_names = config.INPUT_FILES
columns_to_drop = config.COLUMNS_TO_DROP
ship_range_limits = config.SHIP_RANGE_LIMITS



# Script

st.title('Carbon Chain - Emissions Analysis')
st.sidebar.text("""

To prep this data, I did 3 things:
1. Replaced N/A and 'Division by zero!' values with NaN
2. Dropped unused columns (there were lots of them)
3. Imputed the effieciency DWT field with the the transport by mass field, 
as the latter was more populated

 """
)

# Loading Data
data = files_to_dataframe(input_file_names, dropped_indexes=columns_to_drop)

# Filtering data
selected_periods = st.sidebar.multiselect('Select Reporting Period(s)', data['Reporting Period'].unique())

if selected_periods:
    filtered_data = data[data['Reporting Period'].isin(selected_periods)]
else:
    filtered_data = data.copy()


# Calculating custom metrics
filtered_data['Distance Travelled [n miles]'] = (filtered_data['Total fuel consumption [m tonnes]'] * 1000 
                                                  / 
                                                  filtered_data['Annual average Fuel consumption per distance [kg / n mile]']).round(2)

filtered_data['Distance calculated by Co2'] = (filtered_data['Total CO₂ emissions [m tonnes]'] * 1000 
                                               / 
                                               filtered_data['Annual average CO₂ emissions per distance [kg CO₂ / n mile]']).round(2)

filtered_data['Is Distance in Ship Type Range'] = filtered_data.apply(lambda row: is_within_range(ship_range_limits, row['Ship type'], row['Distance Travelled [n miles]'])[0], axis=1)

filtered_data['Percent Diff'] = filtered_data.apply(lambda row: is_within_range(ship_range_limits, row['Ship type'], row['Distance Travelled [n miles]'])[1], axis=1)

filtered_data['Deadweight'] = (filtered_data['Total fuel consumption [m tonnes]']*1000 
                               /
                               filtered_data['Annual average Fuel consumption per transport work']).round(2)

ship_type_agg = custom_groupby(filtered_data,
                               'Ship type',
                               {'IMO Number': 'nunique',
                                'Total CO₂ emissions [m tonnes]':np.mean,
                                'Distance Travelled [n miles]':np.mean,
                                'Annual average CO₂ emissions per distance [kg CO₂ / n mile]':np.mean,
                                'Deadweight':np.mean
                                })



# Question 1

#TODO:  Turn plots into functions
fig = px.bar(
    ship_type_agg.sort_values(by='IMO Number', 
                              ascending=False), 
                              x = 'Ship type',
                              y = 'IMO Number',
                              title='Ship Type vs Number of Ships'
                              )

fig.update_layout(height=600, width=800,
                  xaxis_title="Ship Type",
                  yaxis_title="Number of Ships")

st.plotly_chart(fig)

st.write('''

The bulk carriers are the most common ship type, 
followed by the oil tanker and the container ship. 
The number of ships is unevenly distributed across the different ship types,
 with the bulk carriers accounting for over a third of all ships.

''')

# Question 2

fig1 = px.bar(ship_type_agg.sort_values(by='Total CO₂ emissions [m tonnes]',
                                         ascending=False),
                                         x = 'Ship type',
                                         y = 'Total CO₂ emissions [m tonnes]',
                                         title='Ship Type vs CO2 Emissions'
                                         )

fig1.update_layout(height=600, width=800,
                  xaxis_title="Ship Type",
                  yaxis_title="Avg CO2 Emissions")

st.plotly_chart(fig1)


# Question 3
# Removing outliers to find corrolation between deadweight and emission intensity
data_less_outliers = filtered_data[(filtered_data['Deadweight']<10000000) 
                                   & 
                                   (filtered_data['Annual average CO₂ emissions per distance [kg CO₂ / n mile]'] < 1000)]


# Regression
X = data_less_outliers['Deadweight'].values.reshape(-1,1)
y = data_less_outliers['Annual average CO₂ emissions per distance [kg CO₂ / n mile]'].values

model = LinearRegression()
model.fit(X, y)

r_sq = model.score(X, y)
st.write(f'Coefficient of determination: {r_sq:.3}') 

# Plotting data without outliers and regression of Deadweight vs 
fig2 = px.scatter(data_less_outliers,
              x = 'Deadweight',
              y = 'Annual average CO₂ emissions per distance [kg CO₂ / n mile]',
              title='Deadweight vs Co2 Emission Intensity',
              color="Ship type"
             )

fig2.add_traces(
    go.Scatter(
        x=X.reshape(-1), 
        y=model.predict(X), 
        name='Trendline',
        fill='tonext',
        opacity=0.5
    )
)

fig2.update_layout(height=600, width=800,
                  xaxis_title="Deadweight (Tonnes)",
                  yaxis_title="Co2 Emissions per Distance Travelled (kg/n miles)")

st.plotly_chart(fig2)

st.write(
    f"""
    The graph shows that CO2 intensity tends to increase with deadweight.
    This is backed by by a coefficient of determination of {r_sq:.3}.
    This is likely due to larger ships being less efficient, 
    having more powerful engines, and traveling at higher speeds.
    """
    )

# Question 4
st.write(
    filtered_data[['IMO Number', 
                   'Ship type',
                   'Name',
                   'Distance Travelled [n miles]',
                   'Distance calculated by Co2',
                   'Is Distance in Ship Type Range',
                   'Percent Diff']],
    """
The __Distance Travelled [n miles]__ was calculated using the total fuel consumed and the 
amount of fuel consumed per unit distance (annually). This closely agrees with the __Distance calculated by Co2__,
which was calculated using total CO2 emissions and average CO2 emissions per distance (annually). 
This distance is not always within the typical range for the ship type, which infers it may not be 
an exact representation of the ship's activity. The __Percent Diff__ column quantifies how 
far outside or inside the typical range the calculated distance falls.
"""
)