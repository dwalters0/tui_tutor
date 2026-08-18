import requests
import json
import re
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live

from pylatexenc.latex2text import LatexNodes2Text

from configuration import get_config

from tutor_codex import generate as codex_generate
from tutor_codex import generate_toschema as codex_generate_toschema

console = Console()

#TODO generate_toschema and generate maybe can be condensed

#Streaming response, chunks out then dumps at a point, marked defunct for now and
#new generate method added
def generate_streaming(prompt, print_output=True) :
    config = get_config()
    url = config.openapi_api_url
    headers = {}
    payload = ""
    # header|body
    if config.openapi_auth_type == "header":
        payload = {
            "model": config.openapi_api_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "stream": True
        }
        headers = {'Authorization': 'Bearer {}'.format(config.openapi_api_key),
                   'Content-Type': 'application/json',
                   'Accept': 'application/json'}


    elif config.openapi_auth_type == "body":
        payload = {
            "model": config.openapi_api_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "api_key": config.openapi_api_key,
            "stream": True
        }
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}
    try:
        response = requests.post(url, json=payload,headers=headers, stream=True)
    except Exception as e:
        print("There was an error contacting your LLM, maybe the URL is wrong in the config.")
        print(e)
        sys.exit(1)

    output_text = ""
    with Live(Markdown(""), console=console, refresh_per_second=10) as live:
        for line in response.iter_lines():
            if not line:
                continue

                # If requests returned bytes
            if isinstance(line, bytes):
                line = line.decode("utf-8")

                # OpenAI streaming sends "data: ..."
            if line.startswith("data: "):
                line = line[6:]

                # End of stream
            if line == "[DONE]":
                break

            chunk = json.loads(line)


            try:
                output_text = (
                    response.json()
                    .get("choices", [])[0]
                    .get("message", {})
                    .get("content")
                )
            except:
                print("There was an error contacting your LLM, maybe the URL is wrong in the config.")
                sys.exit(1)

            if print_output:
                converter = LatexNodes2Text()
                output_text = converter.latex_to_text(output_text)
                live.update(
                    Markdown(output_text)
                )

    return output_text



def generate_line_by_line(prompt, print_output=True) :
    config = get_config()
    url = config.openapi_api_url
    headers = {}
    payload = ""
    #header|body
    if config.openapi_auth_type == "header":
        payload = {
            "model": config.openapi_api_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.2,
            "top_p": 0.7,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "max_tokens": 1024,
            "stream": False
        }
        headers = {'Authorization': 'Bearer {}'.format(config.openapi_api_key)}

    elif config.openapi_auth_type == "body":
        payload = {
            "model": config.openapi_api_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "api_key": config.openapi_api_key,
            "stream": False
        }

    response = requests.post(url, json=payload, headers=headers)
    try:
        response_text = (
            response.json()
            .get("choices", [])[0]
            .get("message", {})
            .get("content")
        )
    except Exception as e:
        print("There was an error contacting your LLM, maybe the URL is wrong in the config.")
        print(e)
        sys.exit(1)

    LATEX_PATTERN = re.compile(
        r"\$\$[\s\S]*?\$\$"
        r"|\$[^$\n]+?\$"
        r"|\\\[[\s\S]*?\\\]"
        r"|\\\([\s\S]*?\\\)"
    )

    def convert_latex_in_markdown(text: str) -> str:
        def replace_match(match: re.Match) -> str:
            converter = LatexNodes2Text()
            latex = match.group(0)
            return converter.latex_to_text(latex)  # Convert only this expression

        return LATEX_PATTERN.sub(replace_match, text)

    if print_output:
        output_text = convert_latex_in_markdown(response_text)
        chunks = output_text.split("\n\n")
        for chunk in chunks:
            chunk_markdown = Markdown(chunk)
            console.print(chunk_markdown)
            #input()
    return response_text

def generate(prompt, print_output=True) :
    config = get_config()
    if config.use_codex == True:
        return codex_generate(prompt, print_output)
    if config.openapi_api_output_mode == "line_by_line":
       return generate_line_by_line(prompt, print_output)
    elif config.openapi_api_output_mode == "streaming":
       return generate_streaming(prompt, True)

def generate_toschema(prompt, schema):
    config = get_config()
    if config.use_codex == True:
        return codex_generate_toschema(prompt, schema)
    config = get_config()
    url = config.openapi_api_url

    #add "keep_alive" : "10m" to keep the model warm between prompts
    payload = {
        "model": config.openapi_api_model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "stream": False,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "generated_response",
                "strict": True,
                "schema": schema,
            },
        },
    }
    try:
        response = requests.post(url, json=payload)
        # deliberately let this throw if its wrong
        response_text = (
            response.json()
            .get("choices", [])[0]
            .get("message", {})
            .get("content")
        )
    except:
        print("There was an error contacting your LLM, maybe the URL is wrong in the config.")
        sys.exit(1)
    return response_text
