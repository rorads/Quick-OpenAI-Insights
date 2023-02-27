"""
This class uses the OpenAI API to generate insigts from a dataframe with
timestamp and text.
"""

# TODO: reading the following:
# - https://platform.openai.com/docs/guides/embeddings/use-cases
# - https://github.com/openai/openai-cookbook/blob/2f5e350bbe66a418184899b0e12f182dbb46a156/examples/Obtain_dataset.ipynb
# - https://github.com/openai/openai-cookbook/blob/main/examples/Clustering.ipynb

# imports
import pandas as pd
import tiktoken
from openai.embeddings_utils import get_embedding
from dotenv import load_dotenv

# load environment variables
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
