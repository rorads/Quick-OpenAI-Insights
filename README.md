Quick setup steps


Set up Python: 

```sh
python3 -m venv .ve
source .ve/bin/activate
pip install -r requirements.txt
```

Set up env:

- Create a copy of the `.env.example` file called `.env`. Insert valid API keys.

Set your linter to flake8. This can be done by searching "select linter" in VSCode command palette.

## Quickstart:

To run a dashboard with the latest version of the data, enter the virtual environment and run:

```sh
streamlit run src/streamlitdemo.py
```

To run the pipeline, you can run [`src/orchestrate.py`](./src/orchestrate.py). This runs within VSCode using the inbuilt run function, assuming your .vscode directory matches what's in version control.

To build a new prompt, fork the one in [./prompt_templates/](./prompt_templates), and register it as the model when running the orchestrate.py script (in the method body for `run_transcript_processing()`.

Note that whilst [preprocessing](src/preprocess.py) and [openai_prompt_engine](src/openai_prompt_engine.py) both have main methods, these are just for testing - they should be run via orchestrate.