# see https://towardsdatascience.com/make-dataframes-interactive-in-streamlit-c3d0c4f84ccb

import streamlit as st
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid
# can also import GridUpdateMode, DataReturnMode


def on_page_load():
    # st.set_page_config(layout="wide")
    st.title("HMRC DALAS Transcript Demo")
    st.write("This is a demo of the HMRC DALAS Transcript project.")
    st.set_option('deprecation.showPyplotGlobalUse', False)


def plot_wordcloud(data_frame: pd.DataFrame):
    """
    Plots a wordcloud of the transcript.
    Args:
        data_frame (pd.DataFrame): the dataframe to process
    """

    st.title("Wordcloud")
    st.write("This is a wordcloud of the transcript.")
    from wordcloud import WordCloud
    import matplotlib.pyplot as plt

    # create a single string of all the tags and topics, minus the HMRC and Supplier tags
    text = ' '.join([tag for tag in data_frame['tags'] for tag in tag])
    text = text + ' '.join([topic for topic in data_frame['topic']])
    text = text.lower()
    text = text.replace('hmrc', '').replace('supplier', '')

    # Create and generate a word cloud image:
    wordcloud = WordCloud(width=1200, height=600, background_color='black').generate(text)

    # Display the generated image:
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.show()
    st.pyplot()


def main():
    """
    Main function to run NLP analysis on a text file.
    """
    file_path = 'data/final/v2output.json'
    data_frame = pd.read_json(file_path, orient='records', lines=True)

    plot_wordcloud(data_frame)

    # create a duplicate table of the data frame with the columns for urgency,
    # sentiment, questioning, and descriptive_normative all as a rolling average
    rolling_df = data_frame.copy()
    rolling_df['urgency'] = rolling_df['urgency'].rolling(10).mean()
    rolling_df['sentiment'] = rolling_df['sentiment'].rolling(10).mean()
    rolling_df['questioning'] = rolling_df['questioning'].rolling(10).mean()
    rolling_df['descriptive_normative'] = rolling_df['descriptive_normative'].rolling(
        10).mean()

    # create a line chart plotting urgency, sentiment, questioning, and
    # descriptive_normative columns from the rolling_df dataframe
    # and add a selector to choose which columns to plot
    selected_columns = st.multiselect(
        'Select columns to plot',
        rolling_df.columns,
        default=['urgency', 'sentiment',
                 'questioning', 'descriptive_normative']
    )
    st.line_chart(rolling_df[selected_columns])

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
    # selected = grid_response['selected_rows']


if __name__ == "__main__":
    on_page_load()
    main()
