from concurrent.futures import as_completed
import os
import json
import openai
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

client = openai.Client()


metric_custom_functions = [
    {
        'name': 'getMetrics',
        'description': 'Get metrics other fields body of the input text',
        'parameters': {
            'type': 'object',
            'properties': {
                'parsed': {
                    'type': 'string',
                    'description': 'Your best effort to put punctuation and structure into the text'
                },
                'topic': {
                    'type': 'string',
                    'description': 'A two or three word topic for the text'
                },
                'tags': {
                    'type': 'string',
                    'description': 'A comma separated list in square brackets of at most five important tags for the text, each tag in quotes, e.g. ["tag1", "tag2", "tag3"]'
                },
                'sentiment': {
                    'type': 'integer',
                    'description': 'A sentiment star rating for the text, ranging from 0 to 10'
                },
                'urgency': {
                    'type': 'integer',
                    'description': 'An urgency star rating for the text, ranging from 0 to 10, where 0 stars is not urgent and 10 stars is very urgent'
                },
                'descriptive_normative': {
                    'type': 'integer',
                    'description': 'A descriptiveness and normativity star rating for the text, ranging from 0 to 10, where 0 stars is descriptive and 10 stars is normative. Normative is indicated through words like "should", "ought", "must" and descriptive is indicated through words like "is" and "are"'
                },
                'questioning': {
                    'type': 'integer',
                    'description': 'A questioning star rating for the text, ranging from 0 to 10, where 0 stars is indicates no questions contained and 10 stars indicates many questions contained'
                }
            }
        }
    }
]

def get_reseponse_from_function_prompt(text: str, functions: list[dict], temperature: float, engine: str = "gpt-4-turbo-preview"):
    """
    This function uses the OpenAI API to generate a response from a chat model.

    Parameters:
    text (str): The user's input.
    functions (list[dict]): Custom functions to be used by the chat model.
    temperature (float): Controls the randomness of the model's output.
    engine (str): Specifies the model to be used, defaulting to "gpt-4-turbo-preview".

    Returns:
    response: The response from the API.
    """
    response = client.chat.completions.create(
        model = engine,
        temperature=temperature,
        # max_tokens=400,
        # top_p=1,
        # frequency_penalty=0,
        # presence_penalty=0
        messages = [
            {"role": "system", "content": "You are an AI language model that parses and extracts information from text, using the provided function."},
            {'role': 'user', 'content': text}
        ],
        functions = metric_custom_functions,
        function_call = {"name": "getMetrics"}
    )
    return response


def parse_output(response: openai.ChatCompletion):
    """
    Returns a dictionary from the chatcompletion response.
    Args:
        response (openai.ChatCompletion): the response to unpack
    """
    # unpack the response
    data = response.choices[0].message.function_call.arguments

    return data


def parallel_fetch_list(fetch_list: list, temperature: float, engine: str):
    """
    Returns a series with the output from the autocomplete api added as columns.
    Args:
        fetch_list (list): the series of values to process
        temperature (float): the temperature to use for the autocomplete api
        engine (str): the engine to use for the autocomplete api
    """

    import concurrent.futures
    from tqdm import tqdm

    # wrap the function to be executed with a single argument
    def process_item(item):
        return parse_output(get_reseponse_from_function_prompt(item, metric_custom_functions, temperature, engine))

    # Define the maximum number of concurrent threads to use
    max_threads = 60

    # Use the ThreadPoolExecutor to execute the function on each item in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        # Submit the function to the executor for each item in the series
        futures = [executor.submit(process_item, item) for item in fetch_list]

        # Use tqdm to display a progress bar for the parallel execution
        for _ in tqdm(concurrent.futures.as_completed(futures), total=len(fetch_list)):
            pass

        # Collect the results from the futures as they complete
        results = [future.result() for future in as_completed(futures)]

    return results


def run_prompts_transcript(df: pd.DataFrame,
                           downsample: float = 1.0,
                           temperature: float = 0.2,
                           engine: str = "gpt-4-turbo-preview"
                           ):
    """
    Returns a dataframe with the output from the autocomplete api added as columns.
    Args:
        df (pd.DataFrame): the dataframe to process
        downsample (float): the fraction of rows to downsample the dataframe to.
        This is useful for testing, and should be set to 1.0 for production.
        temperature (float): the temperature to use for the autocomplete api
        engine (str): the engine to use for the autocomplete api
    """

    # apply downsample to the dataframe if it's not 1.0
    if downsample != 1.0:
        df = df.sample(frac=downsample, random_state=42)


    # run the prompts in parallel
    df['output'] = parallel_fetch_list(df['text'].values, temperature=temperature, engine=engine)

    # assuming df is your DataFrame and 'output' is the column with the dictionaries
    df_output = pd.json_normalize([json.loads(x) for x in df['output'].values])
    
    df_output.tags = [json.loads(tag) for tag in df_output.tags]

    # assert that df_output has the same number of rows as df
    assert len(df) == len(df_output)

    df_output.index = df.index
    df_output['timestamp'] = df['timestamp']

    return df_output


# run the main function
if __name__ == "__main__":
    """
    Main function to run NLP analysis on a text file. This assumes that the text
    file is in the data/intermediate folder, and creates a downsampled_output.json
    and downsampled_output.xlsx file in the data/final folder. This is used
    for testing and development purposes.
    """
    # set the openai api key
    df = pd.read_json('data/intermediate/processed.json', orient='records', lines=True)
    df = run_prompts_transcript(df, downsample=0.02)
    df.to_json('data/final/downsampled_output.json',
               orient='records', lines=True)
    df.to_excel('data/final/downsampled_output.xlsx',
                sheet_name='Output', index=False)
