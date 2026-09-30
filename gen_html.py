from frog_classes import Lesson, Topic, index_display_html_card
from frog_llm import generate, generate_toschema
from frog_host_pages import get_index_css, get_lesson_html, get_index_body, get_index_head
from pathlib import Path
from utilities import normalise_filename, load_json
import json

#ai generated web pages - not used in current version
# def create_lesson_html(lesson, out_path):
#     prompt = f"""
# You're a smart developer who knows how to create static web sites. Please convert this yaml file into a html file that presents the
# learning content in an engaging and clear way in a dark mode theme. Don't change the lesson content and just return the html file. Return the content of the html file, don't try to create the file.
# Don't break the lesson into sections, make it one flat html file.
# {lesson}
# """
#     response = generate(prompt,False)
#     html_page = get_lesson_html(response)
#     path = Path(out_path)
#     with open(path, 'w') as f:
#         f.write(html_page)
#     return path.resolve()

def create_lesson_html(lesson, out_path):

    html_page = get_lesson_html(lesson)
    path = Path(out_path)
    with open(path, 'w') as f:
        f.write(html_page)
    return path.resolve()

def create_index(topic,out_path):
    cards = []
    for lesson in topic.lessons:
        link = normalise_filename(lesson.outline_id) + ".html"
        title = lesson.title
        summary = lesson.summary
        cards.append(
            index_display_html_card(title,link,summary)
        )

    index_html = get_index_head(topic.title)

    prompt = f"""
You're making some summary fields for a topic with many lessons..
The lessons in the lesson topic are as follows:
{cards}
Make topic_header, topic_tagline, and topic summary to match.   
"""
    summary_schema = load_json(Path(__file__).parent / "schemas" / "topic_summary_for_html_index.json")
    summary_fields_json = generate_toschema(prompt,summary_schema)
    summary_fields  = json.loads(summary_fields_json)

    index_html += get_index_body(
        summary_fields["topic_header"],
        summary_fields["topic_tagline"],
        summary_fields["topic_summary"],
        topic,
        cards
    )

    css = get_index_css()
    css_path = Path(out_path).parent / "style.css"
    with open(css_path, 'w') as f:
        f.write(css)

    path = Path(out_path)
    with open(path, 'w') as f:
        f.write(index_html)
    return path.resolve()

#don't ai gen anymore
# def create_index(topic,out_path):
#     cards = []
#     for lesson in topic.lessons:
#         link = normalise_filename(lesson.outline_id) + ".html"
#         title = normalise_filename(lesson.title)
#         summary = lesson.summary
#         cards.append(f"Title: {title}\nLink: {link}\nSummary: {summary}")
#
#     prompt = f"""
#     You're a smart developer who knows how to create static web sites. Please create a modern dark mode index page
#     with the following titles / links / summaries. Only return the content of the html file.
#     Return the content of the html file, don't try to create the file.
#     {cards}
#     """
#     response = generate(prompt,False)
#     path = Path(out_path)
#
#     css = get_index_css()
#
#     css_path = Path(out_path).parent / "style.css"
#     with open(css_path, 'w') as f:
#         f.write(css)
#
#     with open(path, 'w') as f:
#         f.write(response)
#     return path.resolve()