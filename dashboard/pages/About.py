# command flake8 to ignore unused imports
# flake8: noqa: F401
import streamlit as st

# Adding markdown text using a magic command, eabled in the config.toml file
"""
# About this app

This app is a work in progress. So far the following features have been implemented:

- Manually input the transcript of a youtube video
- Preprocess the the transcript into chunks of 10 lines and store in a dataframe, serialised as a json file
- Run NLP analysis on the text file using OpenAI's GPT-3 API
- Analyse and visualise the results using Streamlit

Please get in touch via Github if you have any questions or suggestions, or contact my via my work email address (rory dot scott at paconsulting dot com).

"""
