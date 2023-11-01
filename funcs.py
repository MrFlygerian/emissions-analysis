
import pandas as pd
import streamlit as st
import numpy as np

def is_within_range(range_dict, ship_type, distance):
    """Checks if a distance is within the typical range for a given ship type.

    Args:
    range_dict: a dictionary containing ship types and their distance ranges
    ship_type: The type of ship.
    distance: The distance traveled in nautical miles.

    Returns:
        A tuple containing the following:
            * A boolean value indicating whether the distance is within the typical range.
            * The quantile the calculated distance sits in between the ranges, or how far below it falls outside the ranges (% wise).
    """

    range_min, range_max = range_dict[ship_type]
    if distance < range_min:
        return False, round((distance - range_min) * 100 / range_min , 2)
    elif distance > range_max:
        return False, round((distance - range_max) * 100 / range_max , 2)
    else:
        return True, round((distance - range_min) * 100 / (range_max - range_min),2)


# Functions

def custom_groupby(df, groupby_cols, agg_dict):
    """
    Function to group a DataFrame by multiple dimensions and aggregate by specified columns using various methods.
    
    Args:
        df: The DataFrame to be grouped and aggregated.
        groupby_cols: A list of column names to group by.
        agg_dict: A dictionary specifying the columns to aggregate and their respective aggregation methods.
    
    Returns:
        grouped_df: The resulting grouped and aggregated DataFrame.
    """
    # Grouping and aggregation
    grouped_df = df.groupby(groupby_cols).agg(agg_dict).reset_index()
    
    return grouped_df


@st.cache_data
def files_to_dataframe(file_list, dropped_indexes=None):

    """ Turns a list of files into a dataframe and cleans it by dropping some indexes

    Returns:
        pandas.DataFrame: dataframe containing
    """

    df_list = [pd.read_excel(file, header=2) for file in file_list]
    df = pd.concat(df_list, ignore_index=True)

    # Light cleaning
    df = df.replace(['Division by zero!','Not Applicable'],  np.nan)
    df = df.drop(columns=df.columns[dropped_indexes], axis = 1)
    df['Annual average Fuel consumption per transport work'] = df['Annual average Fuel consumption per transport work (dwt) [g / dwt carried · n miles]'].fillna(df['Annual average Fuel consumption per transport work (mass) [g / m tonnes · n miles]'])
    df = df.drop(columns=['Annual average Fuel consumption per transport work (dwt) [g / dwt carried · n miles]',
                      'Annual average Fuel consumption per transport work (mass) [g / m tonnes · n miles]'], axis = 1)
    return df