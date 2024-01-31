# src/utils/common.py
import pandas as pd


def rolling_average(rolling_df: pd.DataFrame, analytics_columns: list[str], window_size: int = 10):
    """
    Creates a duplicate table of the data frame with the columns for urgency, sentiment, questioning,
    and descriptive_normative all as a rolling average.
    Args:
        data_frame (pd.DataFrame): the dataframe to process
    Returns:
        pd.DataFrame: the dataframe with the rolling averages
    """

    for column in analytics_columns:
        rolling_df[column] = rolling_df[column].rolling(window_size).mean()

    return rolling_df


def stringify_row(row: dict) -> str:
    """
    Returns a string representation of a row. The timecode is be converted from seconds to HH:MM:SS.
    using standard arithmetic. Topic displayed as is. Sentiment, urgency, descriptive_normative
    and questioning are displayed as numbers between 0 and 1 with up to two decimal places.
    Args:
        row (dict): the row to convert to a string
    Returns:
        str: the string representation of the row
    """
    # convert the timecode from seconds to HH:MM:SS
    timecode = row['timestamp']
    timecode = time_code_from_seconds(timecode)

    # convert sentiment, urgency, descriptive_normative and questioning to a string
    sentiment = f"Sentiment: {row['sentiment']:.2f}"
    urgency = f"Urgency: {row['urgency']:.2f}"
    descriptive_normative = f"Descriptive Normative: {row['descriptive_normative']:.2f}"
    questioning = f"Questioning: {row['questioning']:.2f}"

    # return the string representation of the row
    return f"{timecode} | {row['topic']} \t|| {sentiment} | {urgency} | {descriptive_normative} | {questioning}"


def time_code_from_seconds(seconds: int) -> str:
    """
    Converts seconds to HH:MM:SS.
    Args:
        seconds (int): the number of seconds
    Returns:
        str: the timecode in HH:MM:SS format
    """
    hours = int(seconds / 3600)
    minutes = int((seconds - hours * 3600) / 60)
    seconds = int(seconds - hours * 3600 - minutes * 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

