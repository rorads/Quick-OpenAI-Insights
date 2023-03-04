import os
import json
import openai
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


def make_prompt_jinja(text: str, template_path: str):
    """
    Returns a prompt for the autocomplete api with a pre-defined json structure and the text to summarize.
    Args:
        text (str): the text to summarize
        template_path (str): the path to the template to use. This should be in the prompt_templates folder,
        and the path should be relative to that folder.
    """
    # load the template
    env = Environment(loader=FileSystemLoader('./src/prompt_templates'))
    template = env.get_template(template_path)

    # render the template
    prompt = template.render(text=text)

    return prompt


def get_dict_from_prompt(prompt: str, temperature: float, engine: str):
    """
    Returns a json string from a prompt for the autocomplete api.
    Args:
        prompt (str): the prompt to use
        temperature (float): the temperature to use for the autocomplete api
        engine (str): the engine to use for the autocomplete api
    """
    # call the autocomplete api using the make_prompt function
    response = openai.Completion.create(
        engine=engine,
        prompt=prompt,
        temperature=temperature,  # low temp = more conservative
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    output_dict = parse_output_text(response['choices'][0]['text'])
    return output_dict


def parse_output_text(output_text: str):
    """
    Returns a dictionary from the output text from the autocomplete api.
    Args:
        output_text (str): the text to parse
    """
    # Remove arbitrary indentation from the text
    json_text = ""
    for line in output_text.split("\n"):
        json_text += line.strip()
    # Parse the JSON data using the loads() function

    data = json.loads(json_text)

    # wrap the line above in a try/except block which handles JSONDecodeError
    # if the json_text is not valid json, return an empty dictionary
    try:
        data = json.loads(json_text)
    except json.decoder.JSONDecodeError:
        print("JSONDecodeError")
        # halt the program
        raise

    return data


def parallel_fetch_list(fetch_list: list, temperature: float, engine: str):
    """
    Returns a series with the output from the autocomplete api added as columns.
    Args:
        series (pd.Series): the series to process
        temperature (float): the temperature to use for the autocomplete api
        engine (str): the engine to use for the autocomplete api
    """

    import concurrent.futures
    from tqdm import tqdm

    # wrap the function to be executed with a single argument
    def process_item(item):
        return get_dict_from_prompt(item, temperature, engine)

    # Define the maximum number of concurrent threads to use
    max_threads = 50

    # Use the ThreadPoolExecutor to execute the function on each item in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        # Submit the function to the executor for each item in the series
        futures = [executor.submit(process_item, item) for item in fetch_list]

        # Use tqdm to display a progress bar for the parallel execution
        for _ in tqdm(concurrent.futures.as_completed(futures), total=len(fetch_list)):
            pass

        # Collect the results from the futures as they complete
        results = [future.result() for future in futures]

    return results


def run_prompts_transcript(df: pd.DataFrame,
                           prompt_template_path: str,
                           downsample: float = 1.0,
                           temperature: float = 0.2,
                           engine: str = "text-davinci-003"
                           ):
    """
    Returns a dataframe with the output from the autocomplete api added as columns.
    Args:
        df (pd.DataFrame): the dataframe to process
        prompt_template_path (str): the path to the prompt template to use (relative to the prompt_templates folder)
        downsample (float): the fraction of rows to downsample the dataframe to.
        This is useful for testing, and should be set to 1.0 for production.
        temperature (float): the temperature to use for the autocomplete api
        engine (str): the engine to use for the autocomplete api
    """

    # apply downsample to the dataframe if it's not 1.0
    if downsample != 1.0:
        df = df.sample(frac=downsample, random_state=42)

    # create the prompt column via Jinja
    df['prompt'] = df['text'].apply(lambda x: make_prompt_jinja(text=x, template_path=prompt_template_path))

    # run the prompts in parallel
    df['output'] = parallel_fetch_list(df['prompt'].values, temperature=temperature, engine=engine)

    # move values from the output column into their own columns
    df['topic'] = df['output'].apply(lambda x: x['topic'])
    df['tags'] = df['output'].apply(lambda x: x['tags'])
    df['sentiment'] = df['output'].apply(lambda x: x['sentiment'])
    df['urgency'] = df['output'].apply(lambda x: x['urgency'])
    df['descriptive_normative'] = df['output'].apply(
        lambda x: x['descriptive_normative'])
    df['questioning'] = df['output'].apply(lambda x: x['questioning'])

    # drop the prompt and output columns
    df = df.drop(columns=['prompt', 'output'])

    return df


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
    df = run_prompts_transcript(df, prompt_template_path='prompt_v1.j2', downsample=0.2)
    df.to_json('data/final/downsampled_output.json',
               orient='records', lines=True)
    df.to_excel('data/final/downsampled_output.xlsx',
                sheet_name='Output', index=False)
