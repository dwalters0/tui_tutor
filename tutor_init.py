from pathlib import Path
from functools import partial
from dataclasses import dataclass, field
import os
import sys

from tutor_classes import Lesson, Topic, LessonOutline, Unit

from utilities import print_box,pick_folder,pick_topic,pick_lesson,pick_folder_title, \
    pick_only_file, pick_from_list, there_are_generated_topics

from configuration import LastCompletedLesson

from gen_teach import teach
from gen_curriculum import generate_next_lesson, finish_lesson,generate_lesson_content_file, \
    AddTopicDescriptionsToUnit,generate_topic_files, generate_all_lessons_for_a_topic

@dataclass
class MenuItem:
    title: str
    action: partial

@dataclass()
class Menu:
    menu_items: list[MenuItem] = field(default_factory=list[MenuItem])

    def show_and_select(self):
        title = "Main Menu"
        print(f"\n{title}\n" + "-" * len(title))

        for i, item in enumerate(self.menu_items):
            print(f"{i}: {item.title}")

        while True:
            choice = input("\nSelect number: ")

            if choice.isdigit():
                idx = int(choice)
                if 0 <= idx < len(self.menu_items):
                    return self.menu_items[idx]

            print("Invalid selection, try again.")

    def add(self,item):
        if not item:
            return
        elif type(item) == MenuItem:
            self.menu_items.append(item)
        elif type(item) == list:
            self.menu_items.extend(item)


def run_menu_get_next_lesson(next_lesson, next_topic, chosen_lesson_outline):
    if not next_lesson:
        print("The next lesson isn't generated yet")
        print(f"It will be {chosen_lesson_outline.title}")
        next_lesson = generate_next_lesson(next_topic, chosen_lesson_outline)
    print_box(
        f"Topic {next_topic.order + 1}: {next_topic.title}\n{next_lesson.title}")
    teach(next_lesson)
    finish_lesson(chosen_lesson_outline, next_topic, next_lesson)

def menu_get_next_lesson() -> MenuItem | None:
    if not there_are_generated_topics():
        return None
    last_lesson_ref = LastCompletedLesson.load()
    if not last_lesson_ref:
        return None
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
            #They were on the last lesson of the last topic in the unit so don't show a continue for it
            if not current_topic:
                return None
            next_lesson_order = 0
            next_lesson_id = current_topic.lesson_outlines[next_lesson_order].id
            print(f"Current topic is now {current_topic.title}")

        next_lesson = Lesson.load_from_outline_id(next_lesson_id)
        chosen_lesson_outline = current_topic.lesson_outlines[next_lesson_order]
    else:
        next_lesson = last_lesson
        current_topic = last_topic
        chosen_lesson_outline = current_topic.lesson_outlines[last_lesson.order]

    completed = "■" * current_topic.progress.Completed
    incomplete = "□" * (current_topic.progress.Total - current_topic.progress.Completed)
    title = f"Continue from last completed\n   {current_topic.unit_code} Topic {current_topic.order + 1}:{current_topic.title} {completed}{incomplete}\n   {chosen_lesson_outline.title}"
    callable_partial = partial(run_menu_get_next_lesson, next_lesson, current_topic,chosen_lesson_outline)
    return MenuItem(title,callable_partial)

def menu_get_unit_continuations() -> MenuItem | None:
    if not there_are_generated_topics():
        return None
    all_units = Unit.load_all_units()
    menu_items  = []

    for unit in all_units:
        title = ""
        unit_progress = unit.lesson_progress_for_unit()
        if unit_progress.Completed == 0:
            title = f"Start {unit.name}"
        elif unit_progress.Completed == unit_progress.Total:
            title = f"Review {unit.name}"
        else:
            completed = "■" * unit_progress.Completed
            incomplete = "□" * (unit_progress.Total - unit_progress.Completed)
            title = f"Continue {unit.name}\n   {completed}{incomplete}"

        callable_partial = get_unit_continuations_action(unit)
        if callable_partial:
            menu_items.append(MenuItem(title,callable_partial))
    return menu_items

def get_unit_continuations_action(unit):
    next_topic = unit.get_next_uncompleted_topic()
    if not next_topic:
        #the unit is complete
        return None
    next_lesson_outline = next_topic.get_next_lesson_outline()
    chosen_lesson_outline = next_lesson_outline
    return partial(run_menu_get_unit_continuations,next_topic,chosen_lesson_outline)

def run_menu_get_unit_continuations(next_topic,chosen_lesson_outline):
    if not chosen_lesson_outline.generated:
        next_lesson_outline = next_topic.get_next_lesson_outline()
        print("The next lesson isn't generated yet")
        print(f"It will be {next_lesson_outline.title}")
        next_lesson = generate_next_lesson(next_topic, next_lesson_outline)
    else:
        next_lesson = next_topic.get_lesson_by_lesson_outline_id(chosen_lesson_outline.id)

    print_box(
        f"Topic {next_topic.order + 1}: {next_topic.title}\n{next_lesson.title}")
    teach(next_lesson)
    finish_lesson(chosen_lesson_outline, next_topic, next_lesson)

def menu_get_progress_report() -> MenuItem | None:
    if not there_are_generated_topics():
        return None
    title = "Progress report"
    callable_partial = partial(run_progress_report)
    return MenuItem(title,callable_partial)

def run_progress_report():
    curricula_folder = Path(__file__).resolve().parent / "Curricula"
    courses = curricula_folder.iterdir()
    for course in courses:
        print(course.stem)
        units = course.iterdir()
        for unit in units:
            print(f"  {unit.stem}")
            topics = (Path(unit) / "topics").iterdir()
            for topic in topics:
                current_topic = Topic.load(topic)
                completed = "■" * current_topic.progress.Completed
                incomplete = "□" * (current_topic.progress.Total - current_topic.progress.Completed)
                print(f"    {current_topic.title} {completed}{incomplete} {current_topic.progress.Completed}/{current_topic.progress.Total}")
    print()
    input("Press Enter to continue...")

def menu_get_select_any_lesson() -> MenuItem | None:
    if not there_are_generated_topics():
        return None
    title = "Select any lesson"
    callable_partial = partial(run_select_any_lesson)
    return MenuItem(title, callable_partial)

def run_select_any_lesson():
    curricula_path = Path(__file__).resolve().parent / "Curricula"
    if not curricula_path.exists():
        print("No lessons yet. No units loaded")
        return
    course_path = pick_folder_title(curricula_path,"Choose Course")
    unit_path = pick_folder_title(course_path,"Choose Unit")
    #print(f"unit_path is {unit_path}")

    topics = []
    topic_files = os.listdir(Path(unit_path) / "topics")
    print("Loading topic files...")
    for topic_file in topic_files:
        topics.append(Topic.load(Path(unit_path) / "topics" / topic_file))

    topic = pick_topic(topics)

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

def menu_get_generate_unit_files() -> MenuItem:
    title = "Create unit"
    callable_partial = partial(run_generate_unit_files)
    return MenuItem(title, callable_partial)

def run_generate_unit_files():
    unit_path = pick_only_file(Path(__file__).parent / "InputUnits")
    print("\nSelected file:")
    print(unit_path)
    print("This process can take quite some time...")
    #load the original user input yaml file
    unit = Unit.load(unit_path)
    #copies the input yaml file and adds topic_descriptions to it for each topic
    unit = AddTopicDescriptionsToUnit(unit)
    #generates topic files to populate the topics folder
    generate_topic_files(unit)

def menu_get_exit() -> MenuItem:
    title = "Exit"
    callable_partial = partial(sys.exit)
    return MenuItem(title, callable_partial)

def menu_get_generate_lessons() -> MenuItem | None:
    if not there_are_generated_topics():
        return None
    title = "Generate lessons"
    callable_partial = partial(run_generate_lessons)
    return MenuItem(title, callable_partial)

def run_generate_lessons():
    print("You can pre-generate lessons with this option.")
    print("Otherwise they are generated on demand when you start a lesson.")
    result = pick_from_list(["Generate all lessons for a unit",
                             "Generate all lessons for a topic",
                             "Return to main menu"], "What do you want to do?")
    if result == "Return to main menu":
        return
    elif result == "Generate all lessons for a topic":
        course_path = pick_folder(Path(__file__).parent / "Curricula")
        unit_path = pick_folder(course_path)
        print(f"unit_path is {unit_path}")
        topic_yaml_path = pick_only_file(Path(unit_path) / "topics")
        print(topic_yaml_path)
        topic = Topic.load(topic_yaml_path)
        generate_all_lessons_for_a_topic(topic)
    elif result == "Generate all lessons for a unit":
        course_path = pick_folder(Path(__file__).parent / "Curricula")
        unit_path = pick_folder(course_path)
        topic_files = (Path(unit_path) / "topics").glob("*.yaml")
        for topic_file in topic_files:
            topic = Topic.load(topic_file)
            print(f"Generating Topic {topic.order + 1} {topic.title}")
            generate_all_lessons_for_a_topic(topic)

