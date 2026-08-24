from minah_llm import generate
from pathlib import Path
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from utilities import normalise_filename

def create_html(lesson,out_path):
    prompt = f"""
You're a smart developer who knows how to create static web sites. Please convert this yaml file into a html file that presents the 
learning content in an engaging and clear way in a dark mode theme. Don't change the lesson content and just return the html file. Return the content of the html file, don't try to create the file. {lesson}
"""
    response = generate(prompt)
    path = Path(out_path)
    with open(path, 'w') as f:
        f.write(response)
    return path.resolve()

def serve_folder(folder):

    handler = partial(
        SimpleHTTPRequestHandler,
        directory=folder
    )

    server = HTTPServer(("0.0.0.0", 8082), handler)

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True
    )
    thread.start()

    print("HTTP server running on port 8082")

def create_index(topic,out_path):
    cards = []
    for lesson in topic.lessons:
        link = normalise_filename(lesson.title) + ".html"
        title = normalise_filename(lesson.title)
        summary = lesson.summary
        cards.append(f"Title: {title}\nLink: {link}\nSummary: {summary}")

    prompt = f"""
    You're a smart developer who knows how to create static web sites. Please create a modern dark mode index page
    with the following titles / links / summaries. Only return the content of the html file.
    Return the content of the html file, don't try to create the file.
    {cards}
    """
    response = generate(prompt)
    path = Path(out_path)
    with open(path, 'w') as f:
        f.write(response)
    return path.resolve()