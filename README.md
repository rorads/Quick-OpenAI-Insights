## Important Context for Contributors

This work is only approved on **open and/or non-sensitive** sources. So youtube videos, or publicly avaialable documents are absolutely fine, as would be anything that is non-confidential. If you're not sure, ask.


## Aim

Currently, this project is a quick demonstration of OpenAI as a way of running analysis on text.

Specifically, this project looks at this video: https://www.youtube.com/watch?v=Ir3TIRmaSL8, and creates a dashboard currently published here: https://rorads-quick-openai-insights-srcstreamlitdemo-1igria.streamlit.app/.

## Quick setup steps

### Set up Python

Note that python version should be 3.10.3, though 3.8 onwards should also work with the existing requirements.

This project also uses poetry and (informally) pyenv. Ensure that both of these are set up in their default configuration. Then, within the project root folder, run:

```sh
pyenv install 3.10.3
pyenv global 3.10.3
virtualenvs.in-project = true # ensures that the virtual environment is created locally in `.venv` 
python --version # check you're at the right version
cd /path/to/your/project
poetry shell
poetry install
```

Be sure to set your python interpreter to the one in .ve within VSCode to enable interactive debugging etc. This should be `.venv` if you follow the steps above.

### Set up your environment

- Create a copy of the `.env.example` file called `.env`. Insert valid API keys.

## Quickstart:

Once you're environment is set up, you can run the dashbaord and execute the python procedures as follos.

To run a dashboard with the latest version of the data, enter the virtual environment and run:

```sh
streamlit run src/Video_Analytics.py
```

To run the pipeline, you can run [`src/main.py`](./src/main.py). This runs within VSCode using the inbuilt run function, assuming your .vscode directory matches what's in version control.

To build a new prompt, fork the one in [prompt_templates/](./src/prompt_templates), and register it as the model when running the main.py script (in the method body for `run_transcript_processing()`).

Note that whilst [preprocessing](src/preprocess.py) and [openai_prompt_engine](src/openai_prompt_engine.py) both have main methods, these are just for testing - they should be run via main.py.
