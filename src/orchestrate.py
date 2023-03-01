"""
This script uses existing python classes from this project to run NLP analysis
on a text file. Import TextFile class from src/refactor.py to read the text
file and return a dataframe with timestamp and text.
"""

from preprocess import YTVideoTranscript


def main():
    """
    Main function to run NLP analysis on a text file.
    """
    file_path = 'data/raw/HMRC DALAS Transcript Raw.txt'
    text_file = YTVideoTranscript(file_path, chunksize=10)
    text_file.save_data_frame('data/intermediate/processed.json')

    print(text_file.get_data_frame().head())


if __name__ == "__main__":
    main()
