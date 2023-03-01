import json
import openai
from preprocess import YTVideoTranscript
from dotenv import load_dotenv
load_dotenv()


def make_prompt(text: str):
    """
    Returns a prompt for the autocomplete api with a pre-defined json
    structure and the text to summarize.
    Args:
        text (str): the text to summarize
    """
    prompt = """
    What follows is a chunk of text. I want you to return a json string with the following structure.
    Note that the source text contains no punctuation, and doesn't have well defined boundaries between sentences.
    Json structure:
    {{
        "topic": "a two or three word topic for the text",
        "tags": "a space separated list of at most five important tags for the text, each tag in quotes, and the list enclosed in square brackets",
        "sentiment": a sentiment score for the text, ranging from 0 to 1,
        "urgency": an urgency score for the text, ranging from 0 to 1, where 0 is not urgent and 1 is very urgent,
        "descriptive_normative": a descriptiveness and normativitiy score for the text, ranging from 0 to 1, where 0 is descriptive and 1 is normative,
        "questioning": a questioning score for the text, ranging from 0 to 1, where 0 is not questioning and 1 is very questioning,
    }}

    text:
    \"\"\"
    {}
    \"\"\"
    """.format(text)

    return prompt


def get_dict_from_prompt(
                prompt: str,
                temperature: float = 0.2,
                engine: str = "text-davinci-003"):
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
    return data


# create a main method
def main():
    # get a rolled up dataframe to work with
    file_path = 'data/raw/HMRC DALAS Transcript Raw.txt'
    text_file = YTVideoTranscript(file_path, chunksize=10)

    # downsample the dataframe to 25% of the original size
    # df = text_file.get_data_frame().sample(frac=0.02, random_state=42)
    df = text_file.get_data_frame()

    df['prompt'] = df['text'].apply(lambda x: make_prompt(x))

    # use tqdm to show a progress bar
    from tqdm import tqdm
    tqdm.pandas()

    # apply the get_dict_from_prompt function to the dataframe using
    # the prompt column
    df['output'] = df['prompt'].progress_apply(
        lambda x: get_dict_from_prompt(x))

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

    # save the dataframe to a json file in the final folder,
    # named downsampled_output.json
    df.to_json('data/final/downsampled_output.json',
               orient='records', lines=True)
    df.to_excel('data/final/downsampled_output.xlsx',
                sheet_name='Output', index=False)


# run the main function
if __name__ == "__main__":
    main()
