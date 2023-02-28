"""set up a python class to ingest a text file from the data folder and
return a dataframe with timestamp and text
"""

import pandas as pd


class TextFile():
    """
    Class to ingest a text file and return a dataframe with timestamp and
    text. The raw data contains timestamps alternating with text line by line.
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

    def __init__(self, file_path):
        self.file_path = file_path
        self.data_frame = self._read_file()

    def _read_file(self):
        """
        Read the text file and return a dataframe with timestamp and text.
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

    def timestamp_helper(self, timestamp: str):
        """
        Helper function to convert timestamp to datetime. timestam is in the
        format MM:SS for durations under one hour, and HH:MM:SS for durations
        over one hour.
        """
        if len(timestamp.split(':')) == 2:
            return pd.to_datetime(timestamp, format='%M:%S').time()
        else:
            return pd.to_datetime(timestamp, format='%H:%M:%S').time()

    def roll_up_df(self, chunksize=10):
        """
        Roll up the dataframe into chunks of the given size, concatenating
        the text from all consituent rows and using the first timestamp.
        """
        # convert timestamp to datetime using helper function
        self.data_frame['timestamp'] = self.data_frame['timestamp'].apply(
            self.timestamp_helper)

        # TODO: sort this out - doesn't currently work
        # roll up the dataframe into chunks of the given size, concatenating 
        # the text from all consituent rows and using the first timestamp
        # this should not be done using a groupby of the timestamp
        # as the timestamp is not necessarily unique
        # instead, use the pandas rolling function
        # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.rolling.html
        self.data_frame = self.data_frame.rolling(
            window=chunksize, min_periods=1)

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


# create a main function to test the class
if __name__ == '__main__':
    def main():
        """
        Test the TextFile class.
        """
        file_path = 'data/raw/HMRC DALAS Transcript Raw.txt'
        text_file = TextFile(file_path)
        text_file.save_data_frame('data/intermediate/processed.json')

if __name__ == "__main__":
    main()
