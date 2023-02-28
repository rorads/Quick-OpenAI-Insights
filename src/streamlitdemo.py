# set up a streamlit dashboard to display the data in data/intermediate/processed.json
# 
# Compare this snippet from src/streamlitdemo.py:
# """
# This script uses existing python classes from this project to run NLP analysis
# on a text file. Import TextFile class from src/refactor.py to read the text
# file and return a dataframe with timestamp and text.
# """
# 
import streamlit as st
import pandas as pd


def main():
    """
    Main function to run NLP analysis on a text file.
    """
    file_path = 'data/intermediate/processed.json'
    data_frame = pd.read_json(file_path, orient='records', lines=True)
    st.write(data_frame.head())


if __name__ == "__main__":
    main()