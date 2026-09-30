from frog_classes import Lesson, Topic
from frog_llm import generate
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import threading
from utilities import normalise_filename
import json
from frog_host_pages import get_index_css, get_lesson_html
from configuration import LastCompletedLesson, save_progress

class Handler(SimpleHTTPRequestHandler):

    def do_POST(self):
        # Route: POST /api/ask
        if self.path == "/api/ask":
            self.handle_ask()
            return

        # Anything else doesn't exist
        self.send_error(404, "Not Found")

    def do_PUT(self):
        path_parts = urlparse(self.path).path.strip("/").split("/")
        if len(path_parts) == 4 and path_parts[:2] == ["api", "lessons"] and path_parts[3] == "completion":
            self.handle_completion_update(path_parts[2])
            return

        self.send_error(404, "Not Found")

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store")
        super().end_headers()

    def do_GET(self):
        if self.path == "/healthz":
            self.send_json({"status": "ok"})
            return

        if urlparse(self.path).path == "/api/completions":
            self.send_json({"lessons": get_completion_states()})
            return

        super().do_GET()


    def handle_completion_update(self, lesson_id):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            request = json.loads(self.rfile.read(content_length))
        except (ValueError, json.JSONDecodeError):
            self.send_json({"error": "Invalid JSON body"}, status=400)
            return

        complete = request.get("complete")
        if type(complete) is not bool:
            self.send_json({"error": "complete must be a boolean"}, status=400)
            return

        result = set_lesson_completion(lesson_id, complete)
        if not result:
            self.send_json({"error": "Lesson not found"}, status=404)
            return

        self.send_json({"lesson_id": lesson_id, "complete": complete})


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

        self.send_bytes(body, "application/json; charset=utf-8", status)

    def send_bytes(self, body, content_type, status=200):

        self.send_response(status)
        self.send_header(
            "Content-Type",
            content_type
        )
        self.send_header(
            "Content-Length",
            str(len(body))
        )
        self.end_headers()

        self.wfile.write(body)


def find_lesson_outline(lesson_id):
    curricula_path = Path(__file__).resolve().parent / "Curricula"
    for topic_path in curricula_path.glob("*/*/topics/*.yaml"):
        topic = Topic.load(topic_path)
        for lesson_outline in topic.lesson_outlines:
            if lesson_outline.id == lesson_id:
                return topic, lesson_outline
    return None, None


def get_completion_states():
    states = {}
    curricula_path = Path(__file__).resolve().parent / "Curricula"
    for topic_path in curricula_path.glob("*/*/topics/*.yaml"):
        topic = Topic.load(topic_path)
        for lesson_outline in topic.lesson_outlines:
            states[lesson_outline.id] = {"complete": lesson_outline.complete}
    return states


def set_lesson_completion(lesson_id, complete):

    topic, lesson_outline = find_lesson_outline(lesson_id)
    if not topic:
        return False

    lesson_outline.complete = complete
    topic.save()

    if complete:
        lesson = Lesson.load_from_outline_id(lesson_id)
        if lesson:
            save_progress(LastCompletedLesson(str(lesson.path), str(topic.path)))

    return True

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

if __name__ == "__main__":
    serve(Path(__file__).resolve().parent / "html")
