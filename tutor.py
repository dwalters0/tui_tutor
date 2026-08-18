import os

from pathlib import Path

from configuration import get_config
from tutor_codex import auth_codex

from tutor_init import menu_get_next_lesson, menu_get_unit_continuations, \
    menu_get_progress_report, menu_get_select_any_lesson, \
    menu_get_exit, menu_get_generate_lessons, menu_get_create_unit, Menu

from tutor_live_text import stream_panel

def main():

    config = get_config()
    if config.use_codex:
        auth_codex()

    #set working directory to tutor directory
    os.chdir(Path(__file__).resolve().parent)

    os.system('cls' if os.name == 'nt' else 'clear')


    stream_panel("Welcome","Welcome")
    stream_panel("Here you can learn lots of things! Lets Go!","Welcome")

    os.system('cls' if os.name == 'nt' else 'clear')

    menu = Menu()
    menu.add(menu_get_next_lesson())
    menu.add(menu_get_unit_continuations())
    menu.add(menu_get_progress_report())
    menu.add(menu_get_select_any_lesson())
    #menu.add(menu_get_generate_unit_files_from_yaml())
    #menu.add(menu_get_create_unit_conversationally())
    menu.add(menu_get_create_unit())
    menu.add(menu_get_generate_lessons())
    menu.add(menu_get_exit())

    selected = menu.show_and_select()

    os.system('cls' if os.name == 'nt' else 'clear')

    selected.action()

if __name__ == "__main__":
    while True:
        main()