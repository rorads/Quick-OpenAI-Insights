"""
This script uses existing python classes from this project to run NLP analysis
on a text file. Import TextFile class from src/refactor.py to read the text
file and return a dataframe with timestamp and text.
"""

import pandas as pd
import openai_prompt_engine_func
from preprocess import VideoTranscript


def run_text_processing_HMRC():
    """
    Main function to run NLP analysis on a text file.
    """
    file_path = 'data/raw/HMRC DALAS Transcript Raw.txt'
    text_file = VideoTranscript(file_path, chunksize=10)
    text_file.save_data_frame('data/intermediate/processed.json')


def run_transcript_processing_HMRC():
    """
    Main function to run NLP analysis on a text file.
    """
    df = pd.read_json('data/intermediate/processed.json', orient='records', lines=True)
    df = openai_prompt_engine_func.run_prompts_transcript(
        df, temperature=0.0, downsample=1.0)  # run with no downsample 
    df.to_json('data/final/output.json',
               orient='records', lines=True)
    df.to_excel('data/final/output.xlsx',
                sheet_name='Output', index=False)



if __name__ == "__main__":
    run_text_processing_HMRC()
    run_transcript_processing_HMRC()
