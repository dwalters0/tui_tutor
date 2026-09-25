from frog_classes import Lesson
from frog_llm import generate
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from utilities import normalise_filename
import json
from frog_host_pages import get_index_css, get_lesson_html


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
        if self.path == "/healthz":
            self.send_json({"status": "ok"})
            return

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
            lesson_path = request.get("lesson")
            messages = request.get("messages", [])

            if not question:
                self.send_json(
                    {"error": "Missing question"},
                    status=400
                )
                return

            lesson = load_lesson_from_request_path(lesson_path)
            if not lesson:
                self.send_json(
                    {"error": "Unknown or missing lesson"},
                    status=400
                )
                return

            print("Question:", question)
            print("Lesson:", lesson.outline_id)
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

def load_lesson_from_request_path(lesson_path):
    if not isinstance(lesson_path, str):
        return None

    filename = Path(urlparse(lesson_path).path).name
    if not filename.endswith(".html"):
        return None

    return Lesson.load_from_outline_id(Path(filename).stem)


def serve(folder="html", host="0.0.0.0", port=8082):
    # Directory containing your generated HTML
    handler = partial(
        Handler,
        directory=folder
    )

    server = ThreadingHTTPServer(
        (host, port),
        handler
    )

    print(f"Serving {Path(folder).resolve()} on http://{host}:{port}")

    server.serve_forever()

def ask_llm(question, lesson, messages):
    print("-----------------------------------------")
    print("Lesson:", lesson.outline_id)
    print("-----------------------------------------")
    conversation = json.dumps(messages, ensure_ascii=False)
    prompt = f"""You are a teacher and you have just taught the following lesson
###BEGIN LESSON YOU TAUGHT###
{lesson.content}
###END LESSON YOU TAUGHT###
    Previous context from the conversation
is as follows 
###START CONTEXT###
{conversation}
###END CONTEXT###
The user has asked {question}.
"""

    answer = generate(prompt,False)
    return f"{answer}"




def create_lesson_html(lesson, out_path):
    prompt = f"""
You're a smart developer who knows how to create static web sites. Please convert this yaml file into a html file that presents the 
learning content in an engaging and clear way in a dark mode theme. Don't change the lesson content and just return the html file. Return the content of the html file, don't try to create the file.
Don't break the lesson into sections, make it one flat html file.
{lesson}
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


if __name__ == "__main__":
    serve(Path(__file__).resolve().parent / "html")
