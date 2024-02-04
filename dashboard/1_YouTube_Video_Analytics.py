# see https://towardsdatascience.com/make-dataframes-interactive-in-streamlit-c3d0c4f84ccb
import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from st_aggrid import GridOptionsBuilder, AgGrid

import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now you can import modules from the src directory
import src.utils.common as utils

YOUTUBE_URL = "https://www.youtube.com/watch?v=Ir3TIRmaSL8"
TEXT_FILE_PATH = "data/final/output.json"
ANALYTICS_COLUMNS = ['sentiment', 'urgency', 'descriptive_normative', 'questioning']


class YouTubeDashboard:
    """
    Class to create a dashboard for the HMRC DALAS Transcript project.
    """

    def __init__(self, file_path: str, youtube_url: str, rolling_window: int = 5):
        """
        Args:
            file_path (str): the path to the json file containing the transcript data
            youtube_url (str): the url of the youtube video
            rolling_window (int): the rolling window for the rolling average
        """
        self.analytics_columns = ANALYTICS_COLUMNS
        self.input_file_path = file_path
        self.primary_data_frame = pd.read_json(file_path, orient='records', lines=True)
        self.primary_data_frame['timecode_text'] = self.primary_data_frame['timestamp'].apply(
            lambda x: utils.time_code_from_seconds(x))

        # create a copy of the dataframe to use for the wordcloud which doesn't update when
        # the original dataframe is updated
        self.wordcloud_data_frame = self.primary_data_frame.copy()
        self.rolling_data_frame = self.primary_data_frame.copy()
        self._set_rolling_window(rolling_window)

        self.youtube_url = youtube_url
        self.input_file_path = file_path

    def _set_rolling_window(self, rolling_window: int):
        """
        Sets the rolling window for the rolling average.
        Args:
            rolling_window (int): the rolling window
        """
        self.rolling_data_frame = utils.rolling_average(
            self.rolling_data_frame, self.analytics_columns,
            rolling_window)

    def load_youtube_video(self):
        """
        Loads a youtube video along with a table which can be used to select sections to view.
        """

        # load an initial selected row from the primary dataframe whilst aggrid is loading
        selected_row = self.primary_data_frame.iloc[0]

        grid_options = GridOptionsBuilder.from_dataframe(self.primary_data_frame)
        # grid_options.configure_pagination()  # Add pagination
        grid_options.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum')
        grid_options.configure_grid_options(domLayout='autoHeight')
        grid_options.configure_side_bar()
        grid_options.configure_auto_height(False)

        # hide the id column from the grid, and move the timecode_text column to the front
        grid_options.configure_column('timestamp', hide=True)
        grid_options.configure_column('text', hide=True)
        grid_options.configure_column('timecode_text', pinned='left', width="autoSizeColumn")

        # select the first row in the grid by defualt
        grid_options.configure_selection(selection_mode='single',
                                         pre_selected_rows=[0])

        grid_response = AgGrid(
            self.primary_data_frame,
            gridOptions=grid_options.build(),
            fit_columns_on_grid_load=True,
            height=200,
        )

        if grid_response['selected_rows']:
            selected_row = grid_response['selected_rows'][0]
        else:
            selected_row = self.primary_data_frame.iloc[0]

        video, details = st.tabs(["Watch Video", "View Segment Details"])
        # show the details of the selected timecode in the details tab
        with details:
            st.write(selected_row)
        # show the video in the video tab
        with video:
            st.video(self.youtube_url, start_time=selected_row['timestamp'])

    def plot_wordcloud(self):
        """
        Plots a wordcloud of the transcript.
        """

        st.title("Wordcloud")
        st.write("This is a wordcloud of the transcript.")

        df = self.primary_data_frame.copy()

        # create four rows
        columns = st.columns(len(self.analytics_columns))

        # create sliders to allow the user to filter the data based on the analytics columns
        for analytical_column, column in zip(self.analytics_columns, columns):

            # create a slider for the column
            with column:
                slider_value = st.slider(
                    f"{analytical_column} range",
                    value=(0.0, 1.0),
                    step=0.01)

                # filter the dataframe based on the slider value
                df = df[(df[analytical_column] >= slider_value[0]) & (df[analytical_column] <= slider_value[1])]

        # create a single string of all the tags and topics, minus the HMRC and Supplier tags
        stoptags = ['hmrc', 'supllier', 's']
        all_tags = [tag.lower() for tag in df['tags'] for tag in tag]
        all_tags = [tag for tag in all_tags if tag not in stoptags]
        text = ' '.join(all_tags)
        text = text + ' '.join([topic for topic in df['topic']])
        text = text.lower()

        # Check if text is empty
        if not text.strip():
            st.write("No words to display in wordcloud! Try broadening your filters.")
            return

        # Create and generate a word cloud image:
        try:
            wordcloud = WordCloud(width=1200, height=600, background_color='black').generate(text)
        except ValueError:
            st.write("No words to display in wordcloud! Try broadening your filters.")
            return

        # Display the generated image:
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        st.pyplot(plt)

    def altair_plot_line_chart(self):
        """
        Plots a line chart of the transcript.
        Args:
            data_frame (pd.DataFrame): the dataframe to process
        """

        # allow the user to plot the rolling average or the original data
        if st.checkbox('Use Rolling Averages', value=True):
            data_frame = self.rolling_data_frame
        else:
            data_frame = self.primary_data_frame

        # create a line chart plotting the analytical columns from the rolling_df
        # dataframe and add a selector to choose which columns to plot
        selected_columns = st.multiselect(
            'Select columns to plot',
            self.analytics_columns,
            default=self.analytics_columns
        )

        # create a base chart
        base_chart = alt.Chart(data_frame).mark_line().encode(
            x=alt.X('timecode_text:O', title='Timecode'),
            y=alt.Y('value:Q', title='Value'),
            color=alt.Color('column:N', scale=alt.Scale(
                domain=selected_columns
            ), legend=alt.Legend(title="Column Name")),
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

    def plot_correlation_heatmap(self):
        """
        Plots a correlation heatmap of the transcript.
        """

        # allow the user to plot the rolling average or the original data
        if st.checkbox('Use Rolling Averages for Heatmap', value=False):
            data_frame = self.rolling_data_frame
        else:
            data_frame = self.primary_data_frame

        # create a sample data frame
        df = data_frame.drop(columns=['timestamp'])

        # create the correlation matrix using seaborn

        corr_matrix = df = df.select_dtypes(include=[np.number]).corr()

        # plot the correlation matrix using matplotlib
        fig, ax = plt.subplots()
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', ax=ax)

        # display the plot using streamlit
        st.pyplot(fig)

    def plot_table(self):
        """
        Plots a full table of the transcript.
        """

        data_frame = self.primary_data_frame

        gb = GridOptionsBuilder.from_dataframe(data_frame)
        gb.configure_side_bar()  # Add a sidebar
        gb.configure_auto_height(False)

        # Enable pivot mode on the topic column
        gb.configure_column('topic', enableRowGroup=True, enablePivot=True)

        # configure the metrics columns to be aggregated in pivot mode

        for col in self.analytics_columns:
            gb.configure_column(col, aggFunc='avg', width=150)

        # hide the id column from the grid, and move the timecode_text column to the front
        gb.configure_column('timestamp', hide=True)
        gb.configure_column('text', hide=True)
        gb.configure_column('timecode_text', pinned='left', width="autoSizeColumn")

        grid_response = AgGrid(
            self.primary_data_frame,
            gridOptions=gb.build(),
            fit_columns_on_grid_load=True,
            height=600,
            width='flex'
        )

        return grid_response

    def on_page_load(self):
        """
        Runs when the page is loaded.
        """
        st.set_page_config(layout="wide")

    def run(self):
        """
        Runs the dashboard.
        """
        self.on_page_load()

        # Create a sidebar on the of the dashboard to put some documentation in
        st.sidebar.title("Info")
        st.sidebar.markdown("This project is provisional, and currently works on a specific YouTube video.")
        st.sidebar.markdown("In future, the follwoing improvements will be made:")
        st.sidebar.markdown("- The ability to pull a transcript automatically from any YouTube video")
        st.sidebar.markdown("- The ability request processing of the given transcript (each run costs money!)")
        st.sidebar.markdown("Suggestions are welcome - please see the linked \
                            [Github reposistory](https://github.com/rorads/Quick-OpenAI-Insights) \
                            for more information and to open an issue or contribute.")

        # Create a main title for the dashboard
        st.title("HMRC DALAS Transcript Analytics using ChatGPT")
        st.write("This is a demo of the HMRC DALAS Transcript project. \
                Below you will find a video which has been transcribed and \
                analysed using NLP techniques. The transcript has been \
                processed using the OpenAI Prompt Engine, and the results \
                are displayed in the full table on the second tab.")

        tab1, tab2 = st.tabs(["Analytics", "Full Table"])

        with tab1:
            st.write("Below you can view the YouTube video and some analytics it. \
                     Use the table to search for specific words or phrases, or to \
                     filter based on the metrics. Click on a row to select it which \
                     will load the YouTube video to the timecode.")
            self.load_youtube_video()
            tab1_1, tab1_2, tab1_3 = st.tabs(["Line Chart", "Wordcloud", "Correlation Matrix"])
            with tab1_1:
                self.altair_plot_line_chart()
            with tab1_2:
                self.plot_wordcloud()
            with tab1_3:
                self.plot_correlation_heatmap()

        with tab2:
            self.plot_table()


if __name__ == "__main__":
    dashboard = YouTubeDashboard(file_path=TEXT_FILE_PATH, youtube_url=YOUTUBE_URL)
    dashboard.run()
