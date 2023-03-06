# see https://towardsdatascience.com/make-dataframes-interactive-in-streamlit-c3d0c4f84ccb

import streamlit as st
import pandas as pd
import altair as alt
import seaborn as sns
import matplotlib.pyplot as plt
from st_aggrid import GridOptionsBuilder, AgGrid
# can also import GridUpdateMode, DataReturnMode

YOUTUBE_LINK = "https://www.youtube.com/watch?v=Ir3TIRmaSL8"

# currently unused, but could be used to refactor the code to be more DRY and agnostic
# to the number / detail of the metrics
CORE_METRIC_DICT = {
    'sentiment': 'Sentiment',
    'urgency': 'Urgency',
    'descriptive_normative': 'Descriptive Normative',
    'questioning': 'Questioning'
}


def on_page_load():
    st.set_page_config(layout="wide")
    st.title("HMRC DALAS Transcript Analytics using ChatGPT")
    st.write("This is a demo of the HMRC DALAS Transcript project. \
             Below you will find a video which has been transcribed and \
             analysed using NLP techniques. The transcript has been \
             processed using the OpenAI Prompt Engine, and the results \
             are displayed in the full table on the second tab.")
    st.write("For more information please see the [GitHub repo](https://github.com/rorads/Quick-OpenAI-Insights).")
    st.set_option('deprecation.showPyplotGlobalUse', False)


def time_code_from_seconds(seconds: int):
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


def load_youtube_video(url: str, dataframe: pd.DataFrame):
    """
    Loads a youtube video.
    Args:
        url (str): the url of the youtube video
        dataframe (pd.DataFrame): the dataframe containing the transcript
    """
    video_url = url
    timecode = 0

    def stringify_row(row):
        """
        Returns a string representation of a row. The timecode should be converted from seconds to HH:MM:SS.
        using standard arithmetic. Topic should be desplayed as is. Sentiment, urgency, descriptive_normative
        and questioning should be despalyed as numbers between 0 and 1 with up to two decimal places, and they
        should be highlighted on a scale from blue to red.
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

    # add a dropdown to select a timecode from a list of options drawn from
    # the dataframe passed to the function each option should show the
    # timestamp and topic
    time_select = st.selectbox(
        "Select a timecode",
        dataframe[['timestamp',
                   'topic',
                   'sentiment',
                   'urgency',
                   'descriptive_normative',
                   'questioning']].to_dict('records'),
        format_func=stringify_row
    )

    timecode = time_select['timestamp']

    video, details = st.tabs(["Watch Video", "View Segment Details"])
    # show the details of the selected timecode in the details tab
    with details:
        st.write(dataframe[dataframe['timestamp'] == time_select['timestamp']].to_dict('records')[0])
    # show the video in the video tab
    with video:
        st.video(video_url, start_time=timecode)


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
    stoptags = ['hmrc', 'supllier', 's']
    all_tags = [tag.lower() for tag in data_frame['tags'] for tag in tag]
    # remove all stoptags from the list of tags
    all_tags = [tag for tag in all_tags if tag not in stoptags]
    # create a single string of all the tags and topics
    text = ' '.join(all_tags)
    text = text + ' '.join([topic for topic in data_frame['topic']])
    text = text.lower()

    # Create and generate a word cloud image:
    wordcloud = WordCloud(width=1200, height=600, background_color='black').generate(text)

    # Display the generated image:
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.show()
    st.pyplot()


def rolling_average(rolling_df: pd.DataFrame, window_size: int = 10):
    """
    Creates a duplicate table of the data frame with the columns for urgency, sentiment, questioning,
    and descriptive_normative all as a rolling average.
    Args:
        data_frame (pd.DataFrame): the dataframe to process
    Returns:
        pd.DataFrame: the dataframe with the rolling averages
    """
    rolling_df['urgency'] = rolling_df['urgency'].rolling(window_size).mean()
    rolling_df['sentiment'] = rolling_df['sentiment'].rolling(window_size).mean()
    rolling_df['questioning'] = rolling_df['questioning'].rolling(window_size).mean()
    rolling_df['descriptive_normative'] = rolling_df['descriptive_normative'].rolling(
        window_size).mean()
    return rolling_df


def altair_plot_line_chart(data_frame: pd.DataFrame):
    """
    Plots a line chart of the transcript.
    Args:
        data_frame (pd.DataFrame): the dataframe to process
    """

    # create a duplicate table of the data frame with the columns for urgency,
    # sentiment, questioning, and descriptive_normative all as a rolling average
    if st.checkbox('Use Rolling Averages', value=True):
        data_frame = rolling_average(data_frame, window_size=10)

    # create a line chart plotting urgency, sentiment, questioning, and
    # descriptive_normative columns from the rolling_df dataframe
    # and add a selector to choose which columns to plot
    selected_columns = st.multiselect(
        'Select columns to plot',
        data_frame.columns,
        default=['urgency', 'sentiment', 'questioning', 'descriptive_normative']
    )

    # create a base chart
    base_chart = alt.Chart(data_frame).mark_line().encode(
        x=alt.X('timecode_text:O', title='Timecode'),
        y=alt.Y('value:Q', title='Value'),
        color=alt.Color('column:N', scale=alt.Scale(domain=selected_columns), legend=alt.Legend(title="Column Name")),
        tooltip=[alt.Tooltip(c) for c in data_frame.columns]
    )

    # create a chart with separate lines for each selected column
    chart = base_chart.transform_fold(
        selected_columns,
        as_=['column', 'value']
    ).transform_filter(
        alt.FieldOneOfPredicate(field='column', oneOf=selected_columns)
    )

    # add a vertical hover line and display tooltip
    hover_line = alt.Chart(data_frame).mark_rule(color='gray', strokeWidth=0).encode(
        x=alt.X('timecode_text:O', title='Timecode'),
        opacity=alt.condition(
            alt.datum.timecode_text,
            alt.value(0.5),
            alt.value(0)
        ),
        tooltip=[alt.Tooltip(c) for c in data_frame.columns]
    ).add_selection(
        alt.selection_single(on='mouseover', nearest=True, empty='none')
    )

    # combine the chart and hover line
    combined_chart = alt.layer(chart, hover_line).resolve_scale(
        color='independent'
    ).properties(
        height=500,
        width=700
    ).configure_legend(
        orient='top',
        titleFontSize=14,
        labelFontSize=12
    )

    # display the chart
    st.altair_chart(combined_chart, use_container_width=True)


def plot_correlation_heatmap(data_frame: pd.DataFrame):
    """
    Plots a correlation heatmap of the transcript.
    Args:
        data_frame (pd.DataFrame): the dataframe to process
    """

    # create a duplicate table of the data frame with the columns for urgency,
    # sentiment, questioning, and descriptive_normative all as a rolling average
    if st.checkbox('Use Rolling Averages for Heatmap', value=False):
        data_frame = rolling_average(data_frame, window_size=10)

    # create a sample data frame
    df = data_frame.drop(columns=['timestamp'])

    # create the correlation matrix using seaborn
    corr_matrix = df.corr()

    # plot the correlation matrix using matplotlib
    fig, ax = plt.subplots()
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=ax)

    # display the plot using streamlit
    st.pyplot(fig)


def plot_table(data_frame: pd.DataFrame):
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

    return grid_response


def main():
    """
    Main function to run NLP analysis on a text file.
    """
    file_path = 'data/final/v3output.json'
    data_frame = pd.read_json(file_path, orient='records', lines=True)
    data_frame['timecode_text'] = data_frame['timestamp'].apply(
        lambda x: time_code_from_seconds(x))

    tab1, tab2 = st.tabs(["Analytics", "Full Table"])

    with tab1:
        st.write("Below you can view the YouTube video and some analytics it.")
        load_youtube_video(YOUTUBE_LINK, data_frame)
        tab1_1, tab1_2, tab1_3 = st.tabs(["Line Chart", "Wordcloud", "Correlation Matrix"])
        with tab1_1:
            altair_plot_line_chart(data_frame)
        with tab1_2:
            plot_wordcloud(data_frame)
        with tab1_3:
            plot_correlation_heatmap(data_frame)

    with tab2:
        plot_table(data_frame)


if __name__ == "__main__":
    on_page_load()
    main()
