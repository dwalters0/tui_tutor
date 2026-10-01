import yaml
import json
import uuid

from frog_llm import generate
from frog_llm import generate_toschema

from frog_rag import get_rag_context
from frog_rag import convert_pdf_to_text
from frog_rag import create_rag_storage

from utilities import print_box
from utilities import load_json

from frog_classes import TopicDescription, Unit, Topic, Lesson
from frog_classes import LessonOutline
from frog_classes import Topic
from frog_classes import Lesson

from configuration import LastCompletedLesson
from configuration import save_progress

import os
from pathlib import Path

def convo_unit_gen():
    context = ""
    print("Describe the unit you'd like generated in a few sentences."
    "If you'd like include some desired outcomes and topics you'd like included "
    "and what level of education you're looking for.\n")
    while True:
        user_desc = input()
        context += user_desc
        #todo make this a progress bar or at least a 3 dots appearing pattern
        print("Generating...")
        prompt = f"""
        Please generate a unit definition according to the schema and the 
        following user input {user_desc} and context {context}. The topic
        descriptions should be very brief (titles more than descriptions).
        """
        schema2 = load_json(Path(__file__).parent / "schemas" / "units.json")
        unit = generate_toschema(prompt, schema2)
        unit_json = json.loads(unit)
        unit_json["preferences"] = ""
        temp_unit_path = Path(__file__).parent / "InputUnits" / "temp.json"
        with open(temp_unit_path,"w", encoding="utf-8") as file:
            json.dump(unit_json,file, indent=4)
        context += unit
        unit = Unit.load(str(temp_unit_path))
        print("Happy with the following?")
        print(unit.to_string)
        user_reply = input("Enter /confirm to confirm or /nope to continue refining.\n")
        if user_reply == "/confirm":
            break
        else:
            print("Describe your refinements and we'll fix it up.")
    return unit



def generate_next_lesson(current_topic, chosen_lesson_outline):
    new_lesson = None
    if not chosen_lesson_outline.generated:
        new_lesson = generate_lesson_content_file(chosen_lesson_outline, current_topic.unit_code, chosen_lesson_outline.order)
        #r1
        for lesson in current_topic.lesson_outlines:
            if lesson.id == chosen_lesson_outline.id:
                lesson.generated = True
        current_topic.save()
    return new_lesson

def finish_lesson(chosen_lesson_outline, topic, lesson):
    print_box("Lesson complete.")
    save = input("Mark as complete? [Y/n]")
    if save.lower() != "n":
        chosen_lesson_outline.complete = True
        #r1
        for topic_lesson in topic.lesson_outlines:
            if topic_lesson.id == lesson.outline_id:
                topic_lesson.complete = True
        topic.save()
        progress_save = LastCompletedLesson(str(lesson.path), str(topic.path))
        save_progress(progress_save)

def readings(unit):
    #test yaml path for topic_description title, might not have it yet if before genning outlines
    topics = [topic.title for topic in unit.topic_descriptions]
    prompt = f"""
A student is studying {unit.name} at {unit.level} level in a {unit.course} course. 
The unit has the following outcome goals: {unit.outcomes}.
The topics covered in the unit include {topics}.
Please recommend 5 actual textbooks for the unit ranked from the most useful to least useful 
with a short blurb commenting on ranking. 
Don't recommend types of textbooks, recommend actual textbooks, giving the Title and Author. 
If you're unsure whether a textbook to be recommended exists or not, do not include it.
"""
    generate(prompt)

def ragify_textbook(pdf_path,unit):
    pdf_path = Path(pdf_path)
    if pdf_path.exists():
        pdf_to_txt_out_folder = Path(unit.unit_folder) / "textbooks" / "txt"
        if not pdf_to_txt_out_folder.exists():
            pdf_to_txt_out_folder.mkdir(parents=True)

        pdf_to_txt_out_full_path = pdf_to_txt_out_folder / (pdf_path.name + ".txt")
        convert_pdf_to_text(pdf_path, pdf_to_txt_out_full_path)

        print("Finished converting pdf to text.")

        rag_persist_dir = Path(unit.unit_folder) / "textbooks" / "rag"
        if not rag_persist_dir.exists():
            rag_persist_dir.mkdir(parents=True)
        create_rag_storage(pdf_to_txt_out_folder, rag_persist_dir)

        print("Finished creating rag storage.")

def get_rag_or_warn(unit_folder, rag_question):
    textbook_path = Path(unit_folder) / "textbooks" / "rag"
    if textbook_path.exists():
        return get_rag_context(textbook_path, rag_question)
    #else:
        #print("No textbooks found for this topic.")
        #print("Content will be better with a textbook.")
        #don't wait thats dumb
        #option = input("Press Enter to continue or enter q to quit: ")
        #if option == "q" or option == "Q":
        #    exit()

def ask_user_for_unit_preference() -> str:
    user_pref_raw = input("If you have any preferences about how the unit is taught (eg. don't include chemical"
                          "formulas for nutrition information), enter them here, if none, just press enter.\n")
    if user_pref_raw != "":
        #prompt = f"The user has the following preferences for how this unit is taught. Please summarize and rationalise it to be useful in a preferences prompt to be included with each lesson {user_pref_raw}."
        #print("Understanding your preferences...")
        #preference = generate(prompt, False)
        print("Noted. This will apply to lesson generation for this unit.")
    else:
        preference = ""
    return user_pref_raw

def AddTopicDescriptionsToUnit(unit) -> Unit:
    topic_descriptions = []
    total = len(unit.topic_descriptions)
    count = 1
    for topic in unit.topic_descriptions:

        rag_question=f"""
            {topic.title} {unit.name}
        """

        rag_context = get_rag_or_warn(unit.unit_folder, rag_question)

        prompt = f"""
        You are a curriculum designer and you are designing a {unit.course} {unit.level} {unit.name} unit. The unit has the following outcomes: {unit.outcomes}.
        You are designing a topic outline for the topic {topic.title}. The topic outline should be a single sentence that describes the topic in a way that is appropriate for the level of study and the outcomes of the unit. The topic outline should be written in a way that is appropriate for a {unit.level} {unit.course} {unit.name} unit.
        Please provide the topic outline in a single sentence.
        Here is some context from the lesson materials that may help inform your answer: {rag_context}
        The references may or may not be relevant. Use only those that directly help answer the question.
        """

        topic_summary = generate(prompt,False)
        new_topic_description = TopicDescription(title=topic.title,summary=topic_summary)
        topic_descriptions.append(new_topic_description)
        print(f"Defined {topic.title} {count}/{total}.")
        count += 1
    unit.topic_descriptions = topic_descriptions
    unit.save()

    return unit


def populate_topics_using_topic_descriptions(
        course,
        unit_name,
        level,
        outcomes,
        topic_title,
        topic_summary,
        topic_order,
        unit_folder,
        topic_id,
        unit_code) -> Topic:

    rag_question=f"""
            {topic_summary}
        """
    rag_context = get_rag_or_warn(unit_folder, rag_question)

    prompt = f"""
You are generating lessons for a single topic.

course: {course}
unit: {unit_name}
level: {level}
Outcomes: {outcomes}

topic title: {topic_title}
topic summary: {topic_summary}

Generate narrowly scoped lessons that belong specifically for each topic. 
The topic should be broken into 1 hour lessons. 

Rules:
- Stay strictly within {topic_title} for each lesson.
- Do not include unrelated {course} fields.
- Lessons should each represent about 60 minutes of teaching.
- Concepts should be {level}.
- Prefer concrete {unit_name} concepts over broad academic domains.
- Set each to complete=False

Here is some context from the lesson materials that may help inform your answer: {rag_context}
The references may or may not be relevant. Use only those that directly help answer the question.
"""
    schema1 = load_json(Path(__file__).parent / "schemas" / "topics.json")
    topic = generate_toschema(prompt, schema1)
    topic_json = json.loads(topic)

    title = topic_json["topic"]
    new_lesson_outlines = []

    lesson_order = 0
    for lesson_outline in topic_json["lesson_outlines"]:
        new_lesson_outlines.append(LessonOutline(
                title=lesson_outline["title"],
                summary=lesson_outline["summary"],
                complete=lesson_outline["complete"],
                id=str(uuid.uuid4()),
                unit_folder = unit_folder,
                topic_id = topic_id,
                order= lesson_order
                )
            )
        lesson_order = lesson_order + 1



    topic = Topic(
        title=title,
        lesson_outlines=new_lesson_outlines,
        order=topic_order,
        unit_folder=unit_folder,
        unit_code=unit_code,
        id=topic_id)

    display_fields = generate_topic_display_fields(topic)
    topic.header = display_fields["topic_header"]
    topic.tagline = display_fields["topic_tagline"]
    topic.summary = display_fields["topic_summary"]

    return topic

def generate_topic_display_fields(topic):
    lesson_outlines = []
    for lesson_outline in topic.lesson_outlines:
        lesson_outlines.append([lesson_outline.title, lesson_outline.summary])

    prompt = f"""
    You're making some summary fields for a topic with many lessons..
    The lessons in the lesson topic are as follows:
    {lesson_outlines}
    Make topic_header, topic_tagline, and topic summary to match.   
    """
    display_fields_schema = load_json(Path(__file__).parent / "schemas" / "topic_summary_for_html_index.json")
    display_fields_json = generate_toschema(prompt, display_fields_schema)
    display_fields = json.loads(display_fields_json)

    return display_fields


def generate_topic_files(unit):
    order = 0
    total = len(unit.topic_descriptions)
    count = 1
    for topic_description in unit.topic_descriptions:
        topic_id=str(uuid.uuid4())
        topic = populate_topics_using_topic_descriptions(
            unit.course,
            unit.name,
            unit.level,
            unit.outcomes,
            topic_description.title, 
            topic_description.summary,
            order,
            unit.unit_folder,
            topic_id,
            unit.unit_code
            )
        topic.save()
        print(f"Finished filling out {topic.title}. {count}/{total} done.")
        order += 1
        count += 1

def regenerate_lesson_content_file(lesson):
    unit_code = lesson.unit_code
    lesson_order = lesson.order
    lesson_outline = LessonOutline.get_lesson_outline_by_id(lesson.outline_id)
    generate_lesson_content_file(lesson_outline, unit_code, lesson_order)
    print("Lesson overwritten.")



def generate_lesson_content_file(lesson_outline, unit_code, lesson_order):
    print("Generating lesson content for: " + lesson_outline.title)
    # rag_question=f"""
    #         {lesson_outline.summary}
    #     """
    # rag_context = get_rag_or_warn(lesson_outline.unit_folder, rag_question)

    unit = Unit.load_unit_from_unit_code(unit_code)
    prompt = f"""
    Please teach me about {lesson_outline.title} - {lesson_outline.summary}. 
    Do not provide a lesson plan, take the role of the tutor actually teaching the lesson.
    The student has the following preferences about how they are taught the lesson {unit.preferences}. Follow them as closely
    as possible unless the meaning being conveyed by the lesson requires they be bent or broken.
"""
    content = generate(prompt,False)

    lesson = Lesson(
        title = lesson_outline.title,
        summary = lesson_outline.summary,
        content = content,
        outline_id = lesson_outline.id,
        unit_folder = lesson_outline.unit_folder,
        topic_id = lesson_outline.topic_id,
        unit_code = unit_code,
        order = lesson_order
    )

    lesson.save()

    return lesson

def generate_all_lessons_for_a_topic(topic):
    order = 0
    for lesson_outline in topic.lesson_outlines:
        if lesson_outline.generated == False:
            generate_lesson_content_file(lesson_outline,topic.unit_code,order)
            lesson_outline.generated = True
            topic.update_lesson_outline(lesson_outline)
        order = order + 1