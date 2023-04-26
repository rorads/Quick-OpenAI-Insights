"""set up a python class to ingest a text file from the data folder and
return a dataframe with timestamp and text
"""

import pandas as pd
import textract as tx
import regex as re


class VideoTranscript():
    """
    Class to ingest a text file and return a dataframe with timestamp and
    text. Raw data is provided in various formats depending on the tool
    used to transcribe it (YouTube, Teams, etc.)
    """

    def __init__(self, file_path, chunksize=10, source="YT"):
        """
        Args:
            file_path (str): path to the text file
            chunksize (int): number of rows to roll up into one row
        """

        self.file_path = file_path
        if source == "YT":
            self.data_frame = self._read_file_yt()
        elif source == "TEAMS":
            self.data_frame = self._read_file_teams()
        else:
            raise ValueError("Source type not recognised")
        self._remove_thinking_words()
        self.roll_up_df(chunksize=chunksize)

    def _read_file_yt(self):
        """
        Read the text file and return a dataframe with timestamp and text.

        The raw data contains timestamps alternating with text line by line.
        
        Text file has the following format:
            ```
            0:00
            so I think we are fine to get started and the first thing on the agenda
            0:05
            is oh
            0:13
            the first thing on our agenda is a message from Dr Philip ormondsey
            0:19
            oh I should have used this slide I'm just realizing that sorry ...
            0:25
            all right thanks yeah thank you very much and thank you for ...
            ```
        """
        with open(self.file_path, 'r', encoding='UTF-8') as f:
            lines = f.readlines()
        # remove the last line if it is empty
        if lines[-1] == '':
            lines = lines[:-1]
        # create a list of tuples with timestamp and text
        data = []
        for i in range(0, len(lines), 2):
            data.append((lines[i].strip(), lines[i+1].strip()))
        # create a dataframe
        data_frame = pd.DataFrame(data, columns=['timestamp', 'text'])
        return data_frame

    def _read_file_teams(self):
        """
        Read the text file and return a dataframe with timestamp and text.

        The raw data contains timestamps alternating with text line by line.
        
        Text file has the following format (the first line is a header and 
        should be ignored.):
            ```
            WEBVTT

            2a71ec0d-6267-4af9-b1fe-bd3e8eb5ab90/29-0
            00:00:03.518 --> 00:00:06.110
            Sort of things you talked about
            before. Then maybe just to so

            2a71ec0d-6267-4af9-b1fe-bd3e8eb5ab90/29-1
            00:00:06.110 --> 00:00:07.448
            that set the scene a little bit.

            ...
            ```
        """
        with open(self.file_path, 'r', encoding='UTF-8') as f:
            lines = f.readlines()

        # Remove the header
        lines = lines[1:]

        # Create a list of tuples with timestamp and text
        data = []
        text_block = []
        for line in lines:
            # Timestamp line
            if re.match(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', line):
                timestamp = line.split(' ')[0].split('.')[0]
                
                # If there's a previous text block, add it to the data list
                if text_block:
                    data.append((prev_timestamp, ' '.join(text_block)))
                    text_block = []
                
                prev_timestamp = timestamp
            # Text line
            elif line.strip() and not re.match(r'\S+/\S+', line.strip()):
                text_block.append(line.strip())

        # Add the last text block to the data list
        if text_block:
            data.append((prev_timestamp, ' '.join(text_block)))

        # Create a dataframe
        data_frame = pd.DataFrame(data, columns=['timestamp', 'text'])
        return data_frame   



    def _remove_thinking_words(self):
        """
        Remove simple stopwords from the text column.
        """
        # create a list of words which people say when they are thinking like
        # 'oh' and 'um' and 'ah'.
        thinking_words = ['oh', 'um', 'ah', 'uh', 'er', 'mm',
                          'hm', 'hmm', 'hmmm', 'huh', 'uhh',
                          'uhm', 'uhmm', 'uhhmm']

        # remove the thinking words
        self.data_frame['text'] = self.data_frame['text'].apply(
            lambda x: ' '.join([word for word in x.split() if word not in
                                thinking_words]))

    def _timestamp_helper(self, timestamp: str):
        """
        Helper function to convert timestamp to datetime. timestamp is in the
        format MM:SS for durations under one hour, and HH:MM:SS for durations
        over one hour.
        """
        if len(timestamp.split(':')) == 2:
            return pd.to_datetime(timestamp, format='%M:%S').time()
        else:
            return pd.to_datetime(timestamp, format='%H:%M:%S').time()

    def _timestamp_to_seconds(self, timestamp: str):
        """
        Convert timestamp to the total number of seconds including the hours and minutes.
        Timestamp is in the format MM:SS for durations under one hour, and HH:MM:SS for durations over one hour.
        """
        time = self._timestamp_helper(timestamp)
        return time.hour * 3600 + time.minute * 60 + time.second

    def rollup_df(self, df, n):
        """
        Roll up the dataframe into chunks of the given size, concatenating
        the text from all consituent rows and using the first timestamp.
        """

        # Create an empty dictionary to hold the new rolled-up data
        rolled_up_data = {"timestamp": [], "text": []}

        # Iterate through the DataFrame in chunks of size n
        for i in range(0, len(df), n):
            # Get the first value of the first column in the chunk
            col1_value = df.iloc[i]["timestamp"]

            # Get all the values of the second column in the chunk and
            # concatenate them
            col2_value = " ".join(df.iloc[i:i+n]["text"].values)

            # Append the rolled-up data to the dictionary
            rolled_up_data["timestamp"].append(col1_value)
            rolled_up_data["text"].append(col2_value)

        # Convert the rolled-up data into a new DataFrame and return it
        return pd.DataFrame(rolled_up_data)

    def roll_up_df(self, chunksize=10):
        """
        Roll up the dataframe into chunks of the given size, concatenating
        the text from all consituent rows and using the first timestamp.
        Args:
            chunksize: the size of the chunk to roll up the dataframe.
        """
        if chunksize < 1:
            raise ValueError('chunksize must be greater than 0')

        if chunksize == 1:
            return self.data_frame

        else:
            self.data_frame['timestamp'] = self.data_frame['timestamp'].apply(
                lambda x: self._timestamp_to_seconds(x))

            self.data_frame = self.rollup_df(self.data_frame, chunksize)

    def get_data_frame(self):
        """
        Return the dataframe.
        """
        return self.data_frame

    def save_data_frame(self, file_path):
        """
        Save the dataframe to a csv file.
        """
        self.data_frame.to_json(file_path, orient='records', lines=True)


class Document():
    """
    Class to ingest a document of any type and process it into 
    something which can be used for analysis. Textract is used to
    extract text from a document, along with metadata such as the
    author, date, and title.
    """

    def __init__(self, file_path):
        """
        Args:
            file_path (str): path to the document file
        """
        self.file_path = file_path
        self.text = self._get_text()

    def _get_text(self):
        """
        Extract text from the document using Textract.
        """
        text = tx.process(self.file_path).decode('utf-8')
        return text


# create a main function to test the class
if __name__ == '__main__':
    def main():
        """
        Test the TextFile class.
        """
        file_path = 'data/raw/Artificial Intelligence in Immigration - Initial Views.vtt'
        text_file = VideoTranscript(file_path, source='TEAMS')
        text_file.save_data_frame('data/intermediate/test_processed.json')

if __name__ == "__main__":
    main()
