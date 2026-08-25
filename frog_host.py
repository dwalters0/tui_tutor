from frog_classes import Lesson
from frog_llm import generate
from pathlib import Path
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from utilities import normalise_filename
import json
from frog_classes import Lesson
from frog_host_pages import get_index_css, get_lesson_html

# singleton lesson context
_context = ""
current_lesson = None




def get_current_lesson() -> Lesson:
    global current_lesson
    return current_lesson

def set_current_lesson(new_lesson):
    global current_lesson
    current_lesson = new_lesson

def reset_current_lesson():
    global current_lesson
    current_lesson = None

def get_context():

    global _context

    return _context

def append_to_context(new_context):
    global _context
    _context += new_context + "\n"

def reset_context():
    global _context
    _context = ""


class Handler(SimpleHTTPRequestHandler):

    def do_POST(self):
        # Route: POST /api/ask
        if self.path == "/api/ask":
            self.handle_ask()
            return

        # Anything else doesn't exist
        self.send_error(404, "Not Found")

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store")
        super().end_headers()

    def do_GET(self):
        if self.path == "/api/lesson":
            print("lesson hit")
            return
        else:
            reset_context()
            if self.path not in (
                    "/",
                    "/index.html",
                    "/style.css",
                    "/favicon.ico"
            ):
                print(self.path)
                lesson_outline_id = self.path.split("/")[2].split(".")[0]
                print(lesson_outline_id)
                lesson = Lesson.load_from_outline_id(lesson_outline_id)
                if lesson:
                    set_current_lesson(lesson)

            super().do_GET()


    def handle_ask(self):
        try:
            # Read request body
            content_length = int(
                self.headers.get("Content-Length", 0)
            )

            body = self.rfile.read(content_length)

            # Decode JSON
            request = json.loads(body)

            question = request.get("question")
            lesson = request.get("lesson")
            messages = request.get("messages", [])

            if not question:
                self.send_json(
                    {"error": "Missing question"},
                    status=400
                )
                return

            print("Question:", question)
            print("Lesson:", lesson)
            print("Messages:", messages)

            # -----------------------------------
            # CALL YOUR LLM HERE
            # -----------------------------------

            answer = ask_llm(
                question=question,
                lesson=lesson,
                messages=messages
            )

            # -----------------------------------

            self.send_json({
                "answer": answer
            })

            append_to_context(f"""
            ###START STUDENT QUESTION###
            {question}
            ###END STUDENT QUESTION###
            """)
            append_to_context(f"""
            ###START LLM ANSWER###
            {answer}
            ###END LLM ANSWER###
            """)

        except Exception as e:
            print("API error:", e)

            self.send_json(
                {"error": str(e)},
                status=500
            )


    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )
        self.send_header(
            "Content-Length",
            str(len(body))
        )
        self.end_headers()

        self.wfile.write(body)

def serve(folder):
    # Directory containing your generated HTML
    handler = partial(
        Handler,
        directory=folder
    )

    server = HTTPServer(
        ("0.0.0.0", 8082),
        handler
    )

    print("Serving on http://localhost:8082")

    server.serve_forever()

    print("HTTP server running on port 8082")

def ask_llm(question, lesson, messages):
    print("-----------------------------------------")
    lesson = get_current_lesson()
    print("Lesson:", lesson.outline_id)
    print("-----------------------------------------")
    append_to_context(lesson.content)
    prompt = f"""You are a teacher and you have just taught the following lesson
###BEGIN LESSON YOU TAUGHT###
{lesson.content}
###END LESSON YOU TAUGHT###
    Previous context from the conversation
is as follows 
###START CONTEXT###
{get_context()}
###END CONTEXT###
The user has asked {question}.
"""

    answer = generate(prompt,False)
    return f"{answer}"




def create_lesson_html(lesson, out_path):
    prompt = f"""
You're a smart developer who knows how to create static web sites. Please convert this yaml file into a html file that presents the 
learning content in an engaging and clear way in a dark mode theme. Don't change the lesson content and just return the html file. Return the content of the html file, don't try to create the file. {lesson}
"""
    response = generate(prompt,False)
    html_page = get_lesson_html(response)
    path = Path(out_path)
    with open(path, 'w') as f:
        f.write(html_page)
    return path.resolve()



def create_index(topic,out_path):
    cards = []
    for lesson in topic.lessons:
        link = normalise_filename(lesson.outline_id) + ".html"
        title = normalise_filename(lesson.title)
        summary = lesson.summary
        cards.append(f"Title: {title}\nLink: {link}\nSummary: {summary}")

    prompt = f"""
    You're a smart developer who knows how to create static web sites. Please create a modern dark mode index page
    with the following titles / links / summaries. Only return the content of the html file.
    Return the content of the html file, don't try to create the file.
    {cards}
    """
    response = generate(prompt,False)
    path = Path(out_path)

    css = get_index_css()

    css_path = Path(out_path).parent / "style.css"
    with open(css_path, 'w') as f:
        f.write(css)

    with open(path, 'w') as f:
        f.write(response)
    return path.resolve()