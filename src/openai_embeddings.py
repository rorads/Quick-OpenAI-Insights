"""
This class uses the OpenAI API to generate insigts from a dataframe with
timestamp and text.
"""

# imports
import pandas as pd
import tiktoken
from openai.embeddings_utils import get_embedding
from dotenv import load_dotenv

load_dotenv()

# embedding model parameters
embedding_model = "text-embedding-ada-002"
# this the encoding for text-embedding-ada-002
embedding_encoding = "cl100k_base"
# the maximum for text-embedding-ada-002 is 8191
max_tokens = 8000

# load data
datafile_path = "data/intermediate/processed.json"
df = pd.read_json(datafile_path, orient="records", lines=True)
df = df.sample(10)

encoding = tiktoken.get_encoding(embedding_encoding)

# omit reviews that are too long to embed
df["n_tokens"] = df.text.apply(lambda x: len(encoding.encode(x)))

# TODO: create a function to get control for the max_tokens

# get embeddings
df["embedding"] = df.text.apply(
    lambda x: get_embedding(x, engine=embedding_model))

# save embeddings
df.to_json("data/intermediate/processed_embeddings.json",
           orient="records", lines=True)
