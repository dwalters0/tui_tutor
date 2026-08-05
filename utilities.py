import os
import re
import json
import os

from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from pylatexenc.latex2text import LatexNodes2Text
import re
console = Console()

def there_is_a_curricula_folder_with_something_in_it() -> bool:
    curricula_folder = Path(__file__).resolve().parent / "Curricula"
    if curricula_folder.exists():
        dir_contents = curricula_folder.iterdir()
        for item in dir_contents:
            return True
    return False

def normalise_filename(text):
    # lowercase
    text = text.lower()

    # replace spaces with underscores
    text = text.replace(" ", "_")

    # remove invalid filename characters
    text = re.sub(r'[<>:"/\\|?*]', '', text)

    # remove anything not alphanumeric, underscore, dash, or dot
    text = re.sub(r'[^a-z0-9._-]', '', text)

    # collapse repeated underscores
    text = re.sub(r'_+', '_', text)

    # trim underscores/dots
    text = text.strip("_.")

    return text

def load_json(input_json):
    try:
        with open(input_json, "r", encoding="utf-8") as file:
            return json.load(file)  # Parse JSON file into Python object
    except FileNotFoundError:
        print("Error: File not found.")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in file: {e}")

def print_box(string):
    string = str(string)
    box_len = console.width
    print("-"*box_len)
    print(f"{string}")
    print("-"*box_len)

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

def print_like_it_were_just_genned(content):
    content = convert_latex_in_markdown(content)
    chunks = content.split("\n\n")
    for chunk in chunks:
        chunk_markdown = Markdown(chunk)
        console.print(chunk_markdown)
        #input()


def pick_MenuItem_from_list(items, title):
    print(f"\n{title}\n" + "-" * len(title))

    for i, item in enumerate(items):
        print(f"{i}: {item.title}")

    while True:
        choice = input("\nSelect number: ")

        if choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(items):
                return items[idx]

        print("Invalid selection, try again.")


def pick_from_list(items, title):
    print(f"\n{title}\n" + "-" * len(title))

    for i, item in enumerate(items):
        print(f"{i}: {item}")

    while True:
        choice = input("\nSelect number: ")

        if choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(items):
                return items[idx]

        print("Invalid selection, try again.")

def pick_from_list_index(items, title):
    print(f"\n{title}\n" + "-" * len(title))

    for i, item in enumerate(items):
        print(f"{i}: {item}")

    while True:
        choice = input("\nSelect number: ")

        if choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(items):
                return choice

        print("Invalid selection, try again.")

def pick_folder(root_dir):
    # Step 1: list folders
    folders = [
        f for f in os.listdir(root_dir)
        if os.path.isdir(os.path.join(root_dir, f))
    ]

    if not folders:
        print("No folders found.")
        return None

    selected_folder = pick_from_list(folders, "Folders")

    return os.path.join(root_dir, selected_folder)

def pick_folder_title(root_dir,title):
    # Step 1: list folders
    folders = [
        f for f in os.listdir(root_dir)
        if os.path.isdir(os.path.join(root_dir, f))
    ]

    if not folders:
        print("No folders found.")
        return None

    selected_folder = pick_from_list(folders, title)

    return os.path.join(root_dir, selected_folder)

def pick_file(root_dir):
    # Step 1: list folders
    folders = [
        f for f in os.listdir(root_dir)
        if os.path.isdir(os.path.join(root_dir, f))
    ]

    if not folders:
        print("No folders found.")
        return None

    selected_folder = pick_from_list(folders, "Folders")

    folder_path = os.path.join(root_dir, selected_folder)

    # Step 2: list files
    files = [
        f for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
    ]

    if not files:
        print("No files found in folder.")
        return None

    selected_file = pick_from_list(files, "Files")

    full_path = os.path.join(folder_path, selected_file)

    return full_path

def pick_lesson(lessons):
    title = "Choose Lesson"
    print(f"\n{title}\n" + "-" * len(title))

    for i, lesson in enumerate(lessons):
        complete_string = ""
        if lesson.complete == True:
            complete_string = "Complete"
        else:
            complete_string = "Incomplete"
        print(f"{i}: {lesson.title} - {complete_string}")

    while True:
        choice = input("\nSelect number: ")

        if choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(lessons):
                print(f"{lessons[idx].title} chosen")
                return lessons[idx]

        print("Invalid selection, try again.")

def pick_topic(topics):
    title = "Choose Topic"
    print(f"\n{title}\n" + "-" * len(title))

    for i, topic in enumerate(topics):
        complete_string = ""
        if topic.is_complete:
            complete_string = "Complete"
        else:
            complete_string = "Incomplete"
        print(f"{i}: {topic.title} - {complete_string}")
    while True:
        choice = input("\nSelect number: ")

        if choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(topics):
                print(f"{topics[idx].title} chosen")
                return topics[idx]

        print("Invalid selection, try again.")

def pick_only_file(folder_path):
    files = [
        f for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
    ]

    if not files:
        print("No files found in folder.")
        return None

    selected_file = pick_from_list(files, "Files")

    full_path = os.path.join(folder_path, selected_file)

    return full_path



def get_single_yaml_file_in_folder(folder_path):
    yaml_files = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".yaml"):
            yaml_files.append(filename)

    if len(yaml_files) == 0:
        print("Error: No unit yaml file found.")
        return None

    if len(yaml_files) > 1:
        print("Error: Multiple yaml files found.")
        return None

    return os.path.join(folder_path, yaml_files[0])