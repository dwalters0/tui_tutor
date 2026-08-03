import os
import sys
from pathlib import Path

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
from tutor_codex import auth_codex

from tutor_init import menu_get_next_lesson, menu_get_unit_continuations, \
    menu_get_progress_report, menu_get_select_any_lesson, menu_get_generate_unit_files, \
    menu_get_exit, menu_get_generate_lessons, Menu

from utilities import pick_MenuItem_from_list


def main():

    config = get_config()
    if config.use_codex:
        auth_codex()

    #set working directory to tutor directory
    os.chdir(Path(__file__).resolve().parent)

    os.system('cls' if os.name == 'nt' else 'clear')

    menu = Menu()
    menu.add(menu_get_next_lesson())
    menu.add(menu_get_unit_continuations())
    menu.add(menu_get_progress_report())
    menu.add(menu_get_select_any_lesson())
    menu.add(menu_get_generate_unit_files())
    menu.add(menu_get_generate_lessons())
    menu.add(menu_get_exit())

    selected = menu.show_and_select()

    os.system('cls' if os.name == 'nt' else 'clear')

    selected.action()

if __name__ == "__main__":
    while True:
        main()