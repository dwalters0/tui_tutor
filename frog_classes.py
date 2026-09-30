from __future__ import annotations

import math
from typing import Self

import yaml
import json
import uuid

from dataclasses import dataclass, field, asdict
from pathlib import Path
import os

from utilities import normalise_filename

@dataclass
class TopicDescription:
    title: str
    summary : str

@dataclass
class Unit:
    course: str
    course_code: str
    name: str
    unit_code: str
    level: str
    total_duration: str
    outcomes: list[str]
    topic_descriptions: list[TopicDescription]
    path: str
    preferences: str

    @property
    def to_string(self):
        outcomes = "\n\t- " + "\n\t- ".join(self.outcomes)
        topics = "\n\t- " + "\n\t- ".join([topic.title for topic in self.topic_descriptions])

        return f"""
Course: {self.course}
Course Code: {self.course_code}
Unit Name: {self.name}
Level: {self.level}
Total Duration: {self.total_duration}
Outcomes: {outcomes}        
Topics: {topics}
        
"""
    @property
    def unit_folder(self):
        return str(Path(__file__).parent / "Curricula" / f"{self.course_code}" / f"{self.unit_code}")

    @property
    def unit_complete(self):
        return self.progress.Completed == self.progress.Total

    @property
    def topics(self):
        topics = []
        topic_folder = Path(self.unit_folder) / "topics"
        for topic_file in topic_folder.glob("*.yaml"):
            if topic_file.is_file():
                topics.append(Topic.load(topic_file))
        return topics


    def get_next_uncompleted_topic(self):
        topics = self.topics
        uncompleted_topics = [topic for topic in topics if not topic.is_complete]
        if len(uncompleted_topics) == 0:
            return None
        last_incomplete = min(uncompleted_topics, key=lambda x: x.order)
        ret = [topic for topic in topics if topic.order == last_incomplete.order][0]
        return ret


    def get_first_topic(self):
        topic_folder = Path(self.unit_folder) / "topics"
        for topic_file in topic_folder.glob("*.yaml"):
            if topic_file.is_file():
                topic = Topic.load(topic_file)
                if topic and topic.order == 0:
                    return topic
        return None

    @property
    def progress(self):
        topic_count = 0
        completed_topic = 0
        topic_folder = Path(self.unit_folder) / "topics"
        for topic_file in  Path(topic_folder).glob("*.yaml"):
            topic_count += 1
            topic = Topic.load(topic_file)
            if topic.is_complete:
                completed_topic += 1
        return Progress(topic_count,completed_topic)


    def lesson_progress_for_unit(self) -> Progress:
        complete = 0
        total = 0
        for topic in self.topics:
            complete += topic.progress.Completed
            total += topic.progress.Total
        return Progress(total,complete)

    def save(self):
        if not os.path.exists(self.unit_folder):
            os.makedirs(self.unit_folder)

        print(f"Created unit folder at {self.unit_folder}")

        path = Path(self.unit_folder) / f"{self.course_code}{self.unit_code}.yaml"
        self.path = str(path)

        with open(self.path, "w", encoding="utf-8") as file:
            yaml.safe_dump(
                asdict(self),
                file,
                indent=4,
                sort_keys=False,
                allow_unicode=True
            )
        print(f"Saved unit to {self.path}")

    @classmethod
    def load(cls, unit_file) -> Unit | None:
        try:
            with open(unit_file, "r", encoding="utf-8") as file:
                if str(unit_file).endswith(".yaml"):
                    data = yaml.safe_load(file)
                elif str(unit_file).endswith(".json"):
                    data = json.load(file)
                else:
                    raise Exception(f"Unsupported file format: {unit_file}")
                if data.get("path"):
                    get_path = data["path"]
                else:
                    get_path = ""

                the_topic_descriptions = []
                if not isinstance(data["topic_descriptions"], list):
                    the_topic_descriptions = [
                        TopicDescription(
                            title=topic["title"],
                            summary=topic["summary"]
                        )
                        for topic in data["topic_descriptions"]
                    ]
                else:
                    the_topic_descriptions = [
                        TopicDescription(
                            title=topic,
                            summary=""
                        )
                        for topic in data["topic_descriptions"]
                    ]

                unit = cls(
                    course=data["course"],
                    course_code=data["course_code"],
                    name=data["name"],
                    unit_code=data["unit_code"],
                    level=data["level"],
                    total_duration=data["total_duration"],
                    outcomes=data["outcomes"],
                    topic_descriptions=the_topic_descriptions,
                    path=get_path,
                    preferences=data["preferences"]
                )
                return unit
        except FileNotFoundError:
            print("Error: File not found.")

    @classmethod
    def load_all_units(cls) -> list[Unit]:
        all_units = []
        curricula_folder = Path(__file__).resolve().parent / "Curricula"
        if not curricula_folder.exists():
            return []
        courses = curricula_folder.iterdir()
        courses = [course for course in courses if course.is_dir()]
        for course in courses:
            units = course.iterdir()
            units = [unit for unit in units if unit.is_dir()]
            for unit in units:
                for unit_file in unit.glob("*.yaml"):
                    all_units.append(cls.load(unit_file))
        return all_units

    @classmethod
    def load_unit_from_unit_code(cls,unit_code) -> Unit:
        units = cls.load_all_units()
        unit = [unit for unit in units if unit_code == unit.unit_code]
        if len(unit) == 1:
            return unit[0]
        else:
            raise Exception(f"Unit with code {unit_code} not found or data corrupted. (duplicate unit codes)")

@dataclass
class Progress:
    Total: int
    Completed: int

@dataclass
class Topic:
    title: str
    lesson_outlines: list[LessonOutline]
    order: int
    unit_folder: str
    unit_code: str
    path: str = ""
    id: str = ""

    def GetFourRunCompletes(self):
        complete_groups = []
        modulo_four_groups = len(self.lesson_outlines) % 4
        groups_of_four_count = math.floor(len(self.lesson_outlines) / 4)
        for groups_of_four_count in range(groups_of_four_count - 1):
            current_group_start_index = groups_of_four_count * 4
            current_group = []
            current_group.append(self.lesson_outlines[current_group_start_index])
            current_group.append(self.lesson_outlines[current_group_start_index+1])
            current_group.append(self.lesson_outlines[current_group_start_index+2])
            current_group.append(self.lesson_outlines[current_group_start_index+3])
            if all(outline.complete for outline in current_group):
                complete_groups.append(current_group)
        last_group_of_four_index = (groups_of_four_count - 1)*4
        last_group = []
        for last_bit in range(modulo_four_groups - 1):
            last_group.append(self.lesson_outlines[last_group_of_four_index + last_bit + 1])
        if all(outline.complete for outline in last_group):
            complete_groups.append(last_group)
        return complete_groups




    @property
    def lessons_ordered_by_order(self) -> list:
        ordered = self.lesson_outlines
        ordered.sort(key=lambda l: l.order)
        return ordered


    @property
    def is_complete(self):
        for lesson in self.lesson_outlines:
            if lesson.complete == False:
                return False
        return True

    @property
    def progress(self):
        lesson_count = len(self.lesson_outlines)
        completed_count = len([lesson.id for lesson in self.lesson_outlines if lesson.complete])
        return Progress(lesson_count,completed_count)

    def save(self):
        if self.id == "":
            self.id = str(uuid.uuid4())
        topic_name = normalise_filename(self.title)
        topics_path = Path(f"{self.unit_folder}") / "topics"
        if not os.path.exists(topics_path):
            os.makedirs(topics_path)
            print("Created topic folder at " + str(topics_path))
        self.path = str(topics_path / f"{self.order}-{topic_name}.yaml")

        with open(self.path, "w", encoding="utf-8") as file:
            yaml.safe_dump(
                asdict(self),
                file,
                indent=4,
                sort_keys=False,
                allow_unicode=True
            )
        print("Saved topic at " + self.path)

    def update_lesson_outline(self, lesson_outline):
        for i, saved_lesson_outline in enumerate(self.lesson_outlines):
            if saved_lesson_outline.id == lesson_outline.id:
                self.lesson_outlines[i] = lesson_outline
                self.save()
                print("saved generated status")
                break

    def get_first_lesson(self):
        for path in (Path(self.unit_folder) / "lessons").glob("*.yaml"):
            candidate_lesson = Lesson.load(path)
            if candidate_lesson.order == 0:
                return candidate_lesson
        return None

    @property
    def lessons(self):
        all_unit_lessons = []
        for path in (Path(self.unit_folder) / "lessons").rglob("*.yaml"):
            all_unit_lessons.append(Lesson.load(path))
        topic_lessons = [lesson for lesson in all_unit_lessons if lesson.topic_id == self.id]
        topic_lessons.sort(key=lambda l: l.order)
        return topic_lessons

    def get_next_lesson(self):
        lessons = self.lessons
        uncompleted_lessons = [lesson for lesson in lessons if not lesson.complete]
        if uncompleted_lessons:
            return min(uncompleted_lessons, key=lambda x: x.order)
        return None

    def get_next_lesson_outline(self):
        lesson_outlines = self.lesson_outlines
        uncompleted_lessons = [lesson_outline for lesson_outline in lesson_outlines if not lesson_outline.complete]
        if uncompleted_lessons:
            return min(uncompleted_lessons, key=lambda x: x.order)
        return None

    def get_lesson_by_lesson_outline_id(self, lesson_outline_id):
        return [lesson for lesson in self.lessons if lesson.outline_id == lesson_outline_id][0]

    @classmethod
    def load_topic_by_unit_code_and_order(cls, unit_code,order):
        curricula_path = Path(__file__).resolve().parent / "Curricula"
        for path in Path(curricula_path).rglob("*.yaml"):
            if path.parent.parent.stem == unit_code:
                if path.parent.stem == "topics":
                    candidate_topic = cls.load(path)
                    if candidate_topic.order == order:
                        return candidate_topic
        return None




    @classmethod
    def load(cls, topic_file):
        try:
            with open(topic_file, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file)
                topic = cls(
                    title=data["title"],
                    lesson_outlines=[
                        LessonOutline(
                            title=lesson["title"],
                            summary=lesson["summary"],
                            complete=lesson["complete"],
                            id=lesson["id"],
                            generated=lesson["generated"],
                            unit_folder=lesson["unit_folder"],
                            topic_id=data["id"],
                            order=lesson["order"]
                        )
                        for lesson in data["lesson_outlines"]
                    ],
                    order=data["order"],
                    unit_folder=data["unit_folder"],
                    path=topic_file,
                    id=data["id"],
                    unit_code = data["unit_code"]
                )
                return topic
        except FileNotFoundError:
            print("Error: File not found.")



@dataclass
class LessonOutline:
    title: str
    summary: str
    unit_folder: str
    topic_id: str
    order: int
    complete: bool = False
    generated: bool = False
    id: str = ""

    @classmethod
    def get_lesson_outline_by_id(cls, search_id):
        curricula_path = Path(__file__).resolve().parent / "Curricula"
        for path in Path(curricula_path).rglob("*.yaml"):
            if path.parent.stem == "topics":
                topic = Topic.load(path)
                for lesson_outline in topic.lesson_outlines:
                    if lesson_outline.id == search_id:
                        return lesson_outline
        return None

@dataclass
class Lesson:
    title: str
    summary: str
    content: str
    outline_id: str
    unit_folder: str
    topic_id: str
    id: str = ""
    path: str = ""
    unit_code: str = ""
    order: int = 0

    @property
    def complete(self):
        lesson_outline = LessonOutline.get_lesson_outline_by_id(self.outline_id)
        if lesson_outline:
            return lesson_outline.complete
        else:
            return False

    def save(self):
        if self.id == "":
            self.id = str(uuid.uuid4())
        lessons_path = Path(self.unit_folder) / "lessons"
        if not os.path.exists(lessons_path):
            os.makedirs(lessons_path)
        self.path = str(lessons_path / f"{self.outline_id}.yaml")
        with open (self.path,"w", encoding="utf-8") as file:
            yaml.safe_dump(
                asdict(self), 
                file, 
                indent=4,
                sort_keys=False,
                allow_unicode=True
            )

    @classmethod
    def load(cls,lesson_file) -> Self:
        try:
            with open(lesson_file, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file)
                lesson = cls(
                        title = data["title"],
                        summary = data["summary"],
                        content = data["content"],
                        outline_id = data["outline_id"],
                        path = lesson_file,
                        id = data["id"],
                        unit_folder = data["unit_folder"],
                        topic_id = data["topic_id"],
                        unit_code = data["unit_code"],
                        order = data["order"]
                )
                return lesson
        except FileNotFoundError:
            print("Error: File not found.")

    @classmethod
    def load_from_outline_id(cls, id_to_find):
        curricula_path = Path(__file__).resolve().parent / "Curricula"
        for path in Path(curricula_path).rglob("*.yaml"):
            #print(path.stem)
            #print(id_to_find)
            if path.stem == id_to_find:
                return cls.load(path)
        return None

@dataclass
class index_display_html_card:
    title: str
    link: str
    summary: str