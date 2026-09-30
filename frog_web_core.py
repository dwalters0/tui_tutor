import os
import sys
from pathlib import Path
from functools import partial
from dataclasses import dataclass, field
from frog_classes import Lesson, Topic, LessonOutline, Unit, unit_display_info
from utilities import print_box, pick_folder, pick_topic, pick_lesson, pick_folder_title, \
    pick_only_file, pick_from_list, there_is_a_curricula_folder_with_something_in_it, normalise_filename
from configuration import LastCompletedLesson, get_config
from gen_teach import teach
from gen_curriculum import generate_next_lesson, finish_lesson, generate_lesson_content_file, \
    AddTopicDescriptionsToUnit, generate_topic_files, generate_all_lessons_for_a_topic, convo_unit_gen, \
    ask_user_for_unit_preference
from frog_live_text import stream_panel
from gen_html import create_lesson_html, create_index


def generate_web_unit(unit):
    for topic in unit.topics:
        generate_web_topic(topic)

# If topic has already been generated, this WILL overwrite it. Check before this.
def generate_web_topic(topic):
    unit_web_folder = f"{topic.unit_code}"
    topic_title_normalised = f"{topic.order}:{normalise_filename(topic.title)}"
    topic_html_folder = Path(__file__).resolve().parent / "html" / "courses" / unit_web_folder / topic_title_normalised
    chosen_topic_lessons_not_generated_yet = [outline for outline in topic.lesson_outlines if not outline.generated]
    if chosen_topic_lessons_not_generated_yet:
        #skips ones already genned
        generate_all_lessons_for_a_topic(topic)
    topic_html_folder.mkdir(parents=True, exist_ok=True)
    for lesson in topic.lessons:
        lesson_html_file = topic_html_folder / (normalise_filename(lesson.outline_id) + ".html")
        html_file = create_lesson_html(lesson, lesson_html_file)
        create_index(topic, topic_html_folder / "index.html")

def create_unit(user_prompt) -> Unit:
    user_desc = input()
    context += user_prompt
    prompt = f"""
    Please generate a unit definition according to the schema and the 
    following user input {user_desc}. The topic
    descriptions should be very brief (titles more than descriptions).
    """
    schema2 = load_json(Path(__file__).parent / "schemas" / "units.json")
    unit = generate_toschema(prompt, schema2)
    unit_json = json.loads(unit)
    unit_json["preferences"] = ""
    temp_unit_path = Path(__file__).parent / "InputUnits" / "temp.json"
    with open(temp_unit_path, "w", encoding="utf-8") as file:
        json.dump(unit_json, file, indent=4)
    unit = Unit.load(str(temp_unit_path))
    unit.save()
    return unit

def get_unit_info(unit_code):
    curricula_folder = Path(__file__).resolve().parent / "Curricula"
    for path in curricula_folder.rglob(unit_code):
        unit_folder = Path(path)
    unit_file = next(unit_folder.glob(f"*{unit_code}.yaml"))
    unit = Unit.load(str(unit_file))
    return unit_display_info(
        unit.course,
        unit.course_code,
        unit.name,
        unit.unit_code
    )