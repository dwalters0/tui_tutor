import os
import sys
from pathlib import Path
from functools import partial
from dataclasses import dataclass, field

from rich.console import Console
from rich.table import Table
console = Console()

from frog_classes import Lesson, Topic, LessonOutline, Unit, quiz_creation_info_lesson

from utilities import print_box, pick_folder, pick_topic, pick_lesson, pick_folder_title, \
    pick_only_file, pick_from_list, there_is_a_curricula_folder_with_something_in_it, normalise_filename, \
    pick_lesson_for_quizzes

from configuration import LastCompletedLesson, get_config

from gen_teach import teach
from gen_curriculum import generate_next_lesson, finish_lesson, generate_lesson_content_file, \
    AddTopicDescriptionsToUnit, generate_topic_files, generate_all_lessons_for_a_topic, convo_unit_gen, \
    ask_user_for_unit_preference

from frog_live_text import stream_panel

from gen_html import create_lesson_html, create_index

from gen_quiz import gen_quiz_set

@dataclass
class MenuItem:
    title: str
    action: partial

@dataclass()
class Menu:
    menu_items: list[MenuItem] = field(default_factory=list[MenuItem])

    def show_and_select(self):
        logo = r"""
                @..@
               (----)
              ( >__< )
              ^^ ~~ ^^

            TUTOR FROG
          Jump into a topic.
        """

        print("\033[92m" + logo + "\033[0m")

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

def run_configure():
    while True:
        print("Configuration Menu")
        config=get_config()
        config_options = attrs = list((vars(config).items()))
        config_options.append(("Return to main menu",None))
        choice = pick_from_list(config_options,"Select configuration to update")
        print(choice[0])
        if choice[0] == "Return to main menu":
            break
        new_val = input("Enter the new value.")
        setattr(config, choice[0], new_val)
        config.save()

def run_menu_get_configure():
    title = "Configuration options"
    callable_partial =  partial(run_configure)
    return MenuItem(title,callable_partial)

def run_quiz():
    # get lesson
    curricula_path = Path(__file__).resolve().parent / "Curricula"
    if not curricula_path.exists():
        print("No lessons yet. No units loaded")
        return
    course_path = pick_folder_title(curricula_path, "Choose Course")
    unit_path = pick_folder_title(course_path, "Choose Unit")
    # print(f"unit_path is {unit_path}")

    topics = []
    topic_files = os.listdir(Path(unit_path) / "topics")
    print("Loading topic files...")
    for topic_file in topic_files:
        topics.append(Topic.load(Path(unit_path) / "topics" / topic_file))
    topics.sort(key=lambda topic: topic.order)
    topic = pick_topic(topics)

    chosen_lesson_outlines = pick_lesson_for_quizzes(topic.lesson_outlines)

    quiz_infos = []
    for chosen_lesson_outline in chosen_lesson_outlines:
        if not chosen_lesson_outline.generated:
            print("No lesson to run a quiz on yet!")
            return

        lesson = Lesson.load(Path(unit_path) / "lessons" / f"{chosen_lesson_outline.id}.yaml")

        quiz_info = quiz_creation_info_lesson(lesson,2)
        quiz_infos.append(quiz_info)

    gen_quiz_set(quiz_infos)

def run_menu_get_quiz():
    title = "run quiz"
    callable_partial = partial(run_quiz)
    return MenuItem(title, callable_partial)

def run_generate_web_topic():
    curricula_path = Path(__file__).resolve().parent / "Curricula"
    if not curricula_path.exists():
        print("No lessons yet. No units loaded")
        return
    course_path = pick_folder_title(curricula_path, "Choose Course")
    unit_path = pick_folder_title(course_path, "Choose Unit")

    topics = []
    topic_files = os.listdir(Path(unit_path) / "topics")
    print("Loading topic files...")
    for topic_file in topic_files:
        topics.append(Topic.load(Path(unit_path) / "topics" / topic_file))
    topics.sort(key=lambda topic: topic.order)
    topic = pick_topic(topics)
    unit_web_folder = f"{normalise_filename(topic.unit_code)}"
    topic_id = f"{normalise_filename(topic.id)}"
    topic_html_folder = Path(__file__).resolve().parent / "html" / "courses" / unit_web_folder / topic_id
    if topic_html_folder.exists():
        print("Html folder already exists")
    else:
        chosen_topic_lessons_not_generated_yet = [outline for outline in topic.lesson_outlines if not outline.generated]
        if chosen_topic_lessons_not_generated_yet:
            not_generated_titles = [outline.title for outline in chosen_topic_lessons_not_generated_yet]
            not_generated_titles_out = "\n  -".join(not_generated_titles)
            print(f"The following lessons aren't generated yet. If you don't generate them now, the html folder will be incomplete.\n  -{not_generated_titles_out}")
            gen_lessons_now = input("\nGenerate now? (Y/n): ")
            if gen_lessons_now.lower() == "y" or gen_lessons_now == "":
                generate_all_lessons_for_a_topic(topic)
        print("Html files not generated yet")
        gen_now = input("\nGenerate now? (Y/n): ")
        if gen_now.lower() == "y" or gen_now == "":
            topic_html_folder.mkdir(parents=True, exist_ok=True)
            for lesson in topic.lessons:
                print(f"Generating {lesson.title}")
                lesson_html_file = topic_html_folder / (normalise_filename(lesson.outline_id) + ".html")
                html_file = create_lesson_html(lesson, lesson_html_file)
                print(f"Done with {html_file}")
            print("Adding finishing touches")
            create_index(topic, topic_html_folder / "index.html")
    print("done!")
    print(f"Access the site at {get_config().display_url_for_html_content}")
    input("Press enter to continue...")
def get_menu_generate_web_topic():
    title = "Turn a topic into a website"
    callable_partial = partial(run_generate_web_topic)
    return MenuItem(title,callable_partial)

def run_host():
    serve("html")
    input("Now hosting. It'll keep hosting till you quit the app. Any key to continue...")


def get_menu_host():
    title = "Host any websites you've made"
    callable_partial = partial(run_host)
    return MenuItem(title,callable_partial)


def run_menu_get_next_lesson(next_lesson, next_topic, chosen_lesson_outline):
    if not next_lesson:
        print("The next lesson isn't generated yet")
        print(f"It will be {chosen_lesson_outline.title}")
        next_lesson = generate_next_lesson(next_topic, chosen_lesson_outline)
    print_box(
        f"Topic {next_topic.order + 1}: {next_topic.title}\n{next_lesson.title}")
    end_lesson = teach(next_lesson)
    if end_lesson:
        finish_lesson(chosen_lesson_outline, next_topic, next_lesson)

def menu_get_next_lesson() -> MenuItem | None:
    if not there_is_a_curricula_folder_with_something_in_it():
        return None
    last_lesson_ref = LastCompletedLesson.load()
    if not last_lesson_ref:
        return None

    if Path(last_lesson_ref.lesson_path).exists():
        last_lesson = Lesson.load(last_lesson_ref.lesson_path)
        last_topic = Topic.load(last_lesson_ref.topic_path)
    else:
        last_lesson = None
        last_topic = None
    if not last_lesson or not last_topic:
        return None

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

        next_lesson = Lesson.load_from_outline_id(next_lesson_id)
        chosen_lesson_outline = current_topic.lesson_outlines[next_lesson_order]
    else:
        next_lesson = last_lesson
        current_topic = last_topic
        chosen_lesson_outline = current_topic.lesson_outlines[last_lesson.order]

    first = f"Continue from last lesson:"
    second = f"{current_topic.unit_code}, {current_topic.title}"
    third =  f"{chosen_lesson_outline.title}"
    max_detail = max(len(second),len(third))
    second = second.ljust(max_detail)
    third = third.ljust(max_detail)
    second = "| "+second+" |"
    third = "| "+third+" |"

    if console.width > max_detail:
        lines = (max_detail+4) * "-"
    else:
        lines = console.width * "-"
    title = first+"\n"+lines+"\n"+second+"\n"+third+"\n"+lines

    callable_partial = partial(run_menu_get_next_lesson, next_lesson, current_topic,chosen_lesson_outline)
    return MenuItem(title,callable_partial)

def menu_get_unit_continuations() -> MenuItem | None:
    if not there_is_a_curricula_folder_with_something_in_it():
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
            #completed = "■" * unit_progress.Completed
            #incomplete = "□" * (unit_progress.Total - unit_progress.Completed)
            title = f"Continue {unit.name} ({(unit_progress.Completed / unit_progress.Total * 100):.2f}% complete)."

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
    end_lesson = teach(next_lesson)
    if end_lesson:
        finish_lesson(chosen_lesson_outline, next_topic, next_lesson)

def menu_get_progress_report() -> MenuItem | None:
    if not there_is_a_curricula_folder_with_something_in_it():
        return None
    title = "Progress report"
    callable_partial = partial(run_progress_report)
    return MenuItem(title,callable_partial)

def run_progress_report():
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
            topics_loaded = []
            for topic in topics:
                topics_loaded.append(Topic.load(topic))
            topics_loaded.sort(key=lambda topic: topic.order)
            for current_topic in topics_loaded:
                completed = "■" * current_topic.progress.Completed
                incomplete = "□" * (current_topic.progress.Total - current_topic.progress.Completed)
                print(f"    {current_topic.title} {completed}{incomplete} {current_topic.progress.Completed}/{current_topic.progress.Total}")
    print()
    input("Press Enter to continue...")

def menu_get_select_any_lesson() -> MenuItem | None:
    if not there_is_a_curricula_folder_with_something_in_it():
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
    topics.sort(key=lambda topic: topic.order)
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
    end_lesson = teach(lesson)
    if end_lesson:
        finish_lesson(chosen_lesson_outline,topic,lesson)

def menu_get_media_break():
    title = "Select Media Break"
    callable_partial = partial(run_media_break)
    return MenuItem(title, callable_partial)

def run_media_break():
    print("Here for each group of four lessons that have been completed, there will be 3 youtube recommendations"
          "that relate to the content you just learned")
    curricula_path = Path(__file__).resolve().parent / "Curricula"
    if not curricula_path.exists():
        print("No lessons yet. No units loaded")
        return
    course_paths = [dir for dir in curricula_path.iterdir() if dir.is_dir()]
    for course_path in course_paths:
        unit_paths = [dir for dir in course_path.iterdir() if dir.is_dir()]
        for unit_path in unit_paths:
            topics_folder = unit_path / "topics"
            topic_files = topics_folder.glob("*.yaml")
            for topic_file in topic_files:
                topic = Topic.load(topic_file)
                complete_groups = topic.GetFourRunCompletes()
                for complete in complete_groups:
                    print(complete.title)
            input("press enter to continue")
    #get all completed lessons aggregated by subject and topic
    #show a menu with any 4 lesson completed runs
    #when an item is selected, get the context from the four lessons then ask the LLM to recommend youtubes



def menu_get_create_unit():
    title = "Dig into something new"
    callable_partial = partial(run_create_unit)
    return MenuItem(title, callable_partial)

def run_create_unit():
    options = ("Generate conversationally","Upload yaml file")
    choice = pick_from_list(options,"New Topic")
    unit = None

    os.system('cls' if os.name == 'nt' else 'clear')

    if choice == "Generate conversationally":
        unit = convo_unit_gen()
        unit.save()
    elif choice == "Upload yaml file":
        unit_path = pick_only_file(Path(__file__).parent / "InputUnits")
        print("\nSelected file:")
        unit = Unit.load(unit_path)

    if unit:
        preference = ask_user_for_unit_preference()
        print("Working on the topic outlines (Process 1 of 2).")
        unit = AddTopicDescriptionsToUnit(unit)
        unit.preferences = preference
        unit.save()
        # generates topic files to populate the topics folder
        print("Now we're really generating the topics. (Process 2 of 2).")
        generate_topic_files(unit)
    else:
        raise Exception("No unit generated, something went wrong.")


# def menu_get_create_unit_conversationally() -> MenuItem:
#     title = "Create Unit Conversationally"
#     callable_partial = partial(run_get_create_unit_conversationally)
#     return MenuItem(title,callable_partial)
#
# def run_get_create_unit_conversationally():
#     unit = convo_unit_gen()
#     unit.save()
#     print("Working on the topic outlines.")
#     unit = AddTopicDescriptionsToUnit(unit)
#
#     # generates topic files to populate the topics folder
#     print("Now we're really generating the topics.")
#     generate_topic_files(unit)
#
#
# def menu_get_generate_unit_files_from_yaml() -> MenuItem:
#     title = "Create unit"
#     callable_partial = partial(run_generate_unit_files_from_yaml)
#     return MenuItem(title, callable_partial)
#
# def run_generate_unit_files_from_yaml():
#     unit_path = pick_only_file(Path(__file__).parent / "InputUnits")
#     print("\nSelected file:")
#     #print(unit_path)
#
#     #load the original user input yaml file
#     unit = Unit.load(unit_path)
#     #copies the input yaml file and adds topic_descriptions to it for each topic
#     print("Working on the topic outlines.")
#     unit = AddTopicDescriptionsToUnit(unit)
#
#     #generates topic files to populate the topics folder
#     print("Now we're really generating the topics.")
#     generate_topic_files(unit)

def menu_get_exit() -> MenuItem:
    title = "Exit"
    callable_partial = partial(sys.exit)
    return MenuItem(title, callable_partial)

def menu_get_generate_lessons() -> MenuItem | None:
    if not there_is_a_curricula_folder_with_something_in_it():
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

1