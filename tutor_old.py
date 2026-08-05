import os
import sys
from pathlib import Path

import yaml

from tutor_classes import Unit, Topic, Progress
from tutor_classes import Topic
from tutor_classes import Lesson
from tutor_classes import LessonOutline

from utilities import print_box
from utilities import pick_from_list
from utilities import pick_from_list_index
from utilities import pick_only_file
from utilities import pick_folder
from utilities import pick_lesson
from utilities import pick_topic

from gen_curriculum import AddTopicDescriptionsToUnit
from gen_curriculum import generate_topic_files
from gen_curriculum import readings
from gen_curriculum import generate_lesson_content_file
from gen_curriculum import generate_all_lessons_for_a_topic
from gen_curriculum import ragify_textbook
from gen_curriculum import finish_lesson
from gen_curriculum import generate_next_lesson

from gen_teach import teach

from configuration import get_config
from configuration import LastCompletedLesson
from configuration import save_progress

from tutor_codex import auth_codex

from tutor_rag import reset_retriever

from gen_quiz import gen_questions_for_lesson

#def main():
    #unit = Unit.load("C:/Users/dan/source/repos/Tutor/Curricula/BInfoTech/1-DatabaseFundamentals.yaml")
    #print(unit)

def main():
    config = get_config()
    if config.use_codex:
        auth_codex()
    #set working directory to tutor directory
    os.chdir(Path(__file__).resolve().parent)
#    first_options = ["learn","Add textbook to unit","Generate lessons for a unit","textbook recommendations","generate all lessons for a topic"]


    first_options = [
        "continue from last complete",
        "select course to continue",
        "select any lesson",
        "generate unit from yaml file",
        "generate all lessons for part of a unit",
        "progress report",
        "Exit"
    ]
    first_options_res = pick_from_list(first_options,"What to do?")

    if first_options_res == "progress report":
        progress = dict()
        curricula_folder = Path(__file__).resolve().parent / "Curricula"
        courses = curricula_folder.iterdir()
        courses = [course for course in courses if course.is_dir()]
        for course in courses:
            print(course.stem)
            units = course.iterdir()
            units = [unit for unit in units if unit.is_dir()]
            for unit in units:
                print(f"  {unit.stem}")
                topics = (Path(unit) / "topics").glob("*.yaml")
                for topic in topics:
                    current_topic = Topic.load(topic)
                    completed = "■" * current_topic.progress.Completed
                    incomplete = "□" * (current_topic.progress.Total - current_topic.progress.Completed)
                    print(f"    {current_topic.title} {completed}{incomplete} {current_topic.progress.Completed}/{current_topic.progress.Total}")
                   # print(f"      {completed}{incomplete}")
                   #  print(f"      {current_topic.progress.Completed} / {current_topic.progress.Total}")
                    #progress[current_topic.title] = current_topic.progress

    if first_options_res == "select course to continue":
        all_units = Unit.load_all_units()
        options = []
        for unit in all_units:
            print(unit.name)
            unit_progress = unit.lesson_progress_for_unit()
            if unit_progress.Completed == 0:
                options.append((f"Start {unit.name}", unit))
            elif unit_progress.Completed == unit_progress.Total:
                options.append((f"Review {unit.name}", unit))
            else:
                completed = "■" * unit_progress.Completed
                incomplete = "□" * (unit_progress.Total - unit_progress.Completed)
                options.append((f"Continue {unit.name} {completed}{incomplete}", unit))

        keys = [x for x, _ in options]
        result = pick_from_list_index(keys, f"Go")
        selected_unit = options[int(result)][1]

        print(selected_unit.name)

        selected_unit_progress = selected_unit.lesson_progress_for_unit()
        next_topic = selected_unit.get_next_uncompleted_topic()
        if not next_topic:
            print("All topics complete")
            print("Review not implemented yet here, select lessons individually")
            return
        next_lesson = next_topic.get_next_lesson()
        if not next_lesson:
            next_lesson_outline = next_topic.get_next_lesson_outline()
            print("The next lesson isn't generated yet")
            print(f"It will be {next_lesson_outline.title}")
            next_lesson = generate_next_lesson(next_topic, next_lesson_outline)

        # selected_unit_progress = selected_unit.lesson_progress_for_unit()
        # if selected_unit_progress.Completed == 0:
        #     next_topic = selected_unit.get_first_topic()
        #     next_lesson = next_topic.get_first_lesson()
        #     if not next_lesson:
        #         first_lesson_outline = next_topic.lessons_ordered_by_order[0]
        #         print("The next lesson isn't generated yet")
        #         print(f"It will be {first_lesson_outline.title}")
        #         next_lesson = generate_next_lesson(next_topic, first_lesson_outline)
        # else:
        #     next_topic = selected_unit.get_next_uncompleted_topic()
        #     next_lesson = next_topic.get_next_lesson()
        #     if not next_lesson:
        #         next_lesson_outline = next_topic.get_next_lesson_outline()
        #         print("The next lesson isn't generated yet")
        #         print(f"It will be {next_lesson_outline.title}")
        #         next_lesson = generate_next_lesson(next_topic, next_lesson_outline)

        chosen_lesson_outline = LessonOutline.get_lesson_outline_by_id(next_lesson.outline_id)
        print_box(
            f"Topic {next_topic.order + 1}: {next_topic.title}\n{next_lesson.title}")
        teach(next_lesson)
        finish_lesson(chosen_lesson_outline, next_topic, next_lesson)

    if first_options_res == "continue from last complete":
        last_lesson_ref = LastCompletedLesson.load()
        last_lesson = Lesson.load(last_lesson_ref.lesson_path)
        last_topic = Topic.load(last_lesson_ref.topic_path)

        last_lesson_outline = LessonOutline.get_lesson_outline_by_id(last_lesson.outline_id)

        if last_lesson_outline.complete:
            next_lesson_order = last_lesson.order + 1

            if next_lesson_order <= len(last_topic.lesson_outlines) - 1:
                current_topic = last_topic
                next_lesson_id = last_topic.lesson_outlines[next_lesson_order].id
            else:
                # get first lesson of next topic
                print("A new topic is being entered")
                next_topic_order = last_topic.order + 1
                current_topic = Topic.load_topic_by_unit_code_and_order(last_topic.unit_code, next_topic_order)
                next_lesson_order = 0
                next_lesson_id = current_topic.lesson_outlines[next_lesson_order].id
                print(f"Current topic is now {current_topic.title}")


            next_lesson = Lesson.load_from_outline_id(next_lesson_id)
            chosen_lesson_outline = current_topic.lesson_outlines[next_lesson_order]

            if not next_lesson:
                print("The next lesson isn't generated yet")
                print(f"It will be {current_topic.lesson_outlines[next_lesson_order].title}")
                next_lesson = generate_next_lesson(current_topic, chosen_lesson_outline)
        else:
            next_lesson = last_lesson
            current_topic = last_topic
            chosen_lesson_outline = current_topic.lesson_outlines[last_lesson.order]

        print_box(f"Topic {current_topic.order + 1}: {current_topic.title}\n{next_lesson.title}")
        teach(next_lesson)
        finish_lesson(chosen_lesson_outline, current_topic, next_lesson)

    elif first_options_res == "generate unit from yaml file":

        unit_path = pick_only_file(Path(__file__).parent / "InputUnits")
        print("\nSelected file:")
        print(unit_path)
        print("This process can take quite some time...")
        #load the original user input yaml file
        unit = Unit.load(unit_path)

        #RAG left out for now
        # print("Before the topic outlines are generated, you can add a textbook to make it better.")
        # print("The textbook will be used for reference for all future interactions with this unit.")
        # print("The process can take a while...")
        #
        # add_text_bool = input("Add a textbook y/n")
        # if add_text_bool.lower() == "y":
        #     pdf_path = input("Enter full path to PDF: ")
        #     ragify_textbook(pdf_path,unit)


        #copies the input yaml file and adds topic_descriptions to it for each topic
        unit = AddTopicDescriptionsToUnit(unit)
        #generates topic files to populate the topics folder
        generate_topic_files(unit)

    elif first_options_res == "select any lesson":

        course_path = pick_folder(Path(__file__).parent / "Curricula")
        unit_path = pick_folder(course_path)
        print(f"unit_path is {unit_path}")

        topics = []
        topic_files = os.listdir(Path(unit_path) / "topics")
        print("Loading topic files...")
        for topic_file in topic_files:
            topics.append(Topic.load(Path(unit_path) / "topics" / topic_file))

        topic = pick_topic(topics)

        while True:
            chosen_lesson_outline = pick_lesson(topic.lesson_outlines)
            print_box(f"New Lesson. {chosen_lesson_outline.title}")

            if not chosen_lesson_outline.generated:
                generate_lesson_content_file(chosen_lesson_outline,topic.unit_code, chosen_lesson_outline.order)
                for lesson in topic.lesson_outlines:
                    if lesson.id == chosen_lesson_outline.id:
                        lesson.generated = True
                topic.save()

            lesson = Lesson.load(Path(unit_path) / "lessons" / f"{chosen_lesson_outline.id}.yaml")
            print_box(
                f"Topic {topic.order + 1}: {topic.title}\n{lesson.title}")
            teach(lesson)

            finish_lesson(chosen_lesson_outline,topic,lesson)

            option_continue = input("Continue? [Y/n]")
            if option_continue.lower() == "n":
                break

    elif first_options_res == "textbook recommendations":


        course_path = pick_folder(Path(__file__).parent / "Curricula")
        unit_path = pick_folder(course_path)
        unit = Unit.load_from_unit_folder(unit_path)
        readings(unit)
        # course_path = pick_folder("./Curricula/")
        # unit_path = pick_folder(course_path)
        # print(f"unit_path is {unit_path}")
        # unitc = get_single_json_file_in_folder(unit_path)
        # print(f"unit_c is {unitc}")
        # app = App("./memory.json", unitc)
        # print("app loaded")
        # #readings(app)
        # print(app.c.content)
        # readings(app)
    elif first_options_res == "generate all lessons for part of a unit":
        course_path = pick_folder(Path(__file__).parent / "Curricula")
        unit_path = pick_folder(course_path)
        print(f"unit_path is {unit_path}")
        topic_yaml_path = pick_only_file(Path(unit_path) / "topics")
        print(topic_yaml_path)
        topic = Topic.load(topic_yaml_path)
        generate_all_lessons_for_a_topic(topic)

    #print(f"starting lesson {json_firstlesson["title"]}.")

    elif first_options_res == "Add textbook to unit":
        unit_path = pick_only_file(Path(__file__).parent / "InputUnits")
        print("\nSelected file:")
        print(unit_path)
        #load the original user input yaml file
        unit = Unit.load(unit_path)
        pdf_path = input("Enter full path to PDF: ")
        ragify_textbook(pdf_path, unit)
    #parser = argparse.ArgumentParser()
    #parser.add_argument("-p", "--prompt", help="The prompt")
    #args = parser.parse_args()
    #if args.prompt:
    #    generate(args.prompt)
    elif first_options_res == "Exit":
        sys.exit()


if __name__ == "__main__":
    while True:
        main()