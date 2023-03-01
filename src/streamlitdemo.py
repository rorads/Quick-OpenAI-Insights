# set up a streamlit dashboard to display the data in
# data/intermediate/processed.json
# -------------------------------------------------
#
# Compare this snippet from src/streamlitdemo.py:
# """
# This script uses existing python classes from this project to
# run NLP analysis on a text file. Import TextFile class from
# src/refactor.py to read the text file and return a dataframe with
# timestamp and text.
# """

# see https://towardsdatascience.com/make-dataframes-interactive-in-streamlit-c3d0c4f84ccb

import streamlit as st
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode


def do_stuff_on_page_load():
    st.set_page_config(layout="wide")
    st.title("HMRC DALAS Transcript Demo")
    st.write("This is a demo of the HMRC DALAS Transcript project.")


def main():
    """
    Main function to run NLP analysis on a text file.
    """
    file_path = 'data/final/downsampled_output.json'
    data_frame = pd.read_json(file_path, orient='records', lines=True)

    gb = GridOptionsBuilder.from_dataframe(data_frame)
    gb.configure_pagination(paginationAutoPageSize=20)  # Add pagination
    gb.configure_side_bar()  # Add a sidebar
    # Enable multi-row selection
    gb.configure_selection('multiple', use_checkbox=True,
                           groupSelectsChildren="Group checkbox select children")

    # Enable pivot mode on the topic column
    gb.configure_column('topic', enableRowGroup=True, enablePivot=True)

    # configure the metrics columns to be aggregated in pivot mode
    gb.configure_column('sentiment', aggFunc='avg')
    gb.configure_column('urgency', aggFunc='avg')
    gb.configure_column('questioning', aggFunc='avg')
    gb.configure_column('descriptive_normative', aggFunc='avg')

    gridOptions = gb.build()

    grid_response = AgGrid(
        data_frame,
        gridOptions=gridOptions,
        data_return_mode='AS_INPUT',
        update_mode='MODEL_CHANGED',
        fit_columns_on_grid_load=False,
        theme='streamlit',  # Add theme color to the table
        enable_enterprise_modules=True,
        height=600,
        width='100%',
        reload_data=True
    )

    data_frame = grid_response['data']
    selected = grid_response['selected_rows']

    # Pass the selected rows to a new dataframe df
    intermediate_df = pd.DataFrame(selected)

    # write text to the streamlit dashboard
    st.write(f"Filtered data frame shape: {intermediate_df.shape}")

    # create a line chart plotting the urgency, sentiment, questioning, and
    # descriptive_normative columns against the index and write it to the
    # dashboard. TODO: Make all the lines be destinct colors.
    st.line_chart(data_frame[['urgency', 'sentiment',
                              'questioning', 'descriptive_normative']])


if __name__ == "__main__":
    do_stuff_on_page_load()
    main()
