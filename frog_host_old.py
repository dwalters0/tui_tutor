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


COMPLETION_SCRIPT_PATH = "/completion.js"
COMPLETION_SCRIPT_TAG = '<script src="/completion.js" defer></script>'
completion_lock = threading.RLock()

COMPLETION_SCRIPT = r"""
(() => {
    const style = document.createElement("style");
    style.textContent = `
        .frog-completion-control {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            width: fit-content;
            margin: 1rem 0 0;
            padding: 0.55rem 0.75rem;
            border: 1px solid rgba(128, 128, 128, 0.45);
            border-radius: 0.5rem;
            background: rgba(128, 128, 128, 0.12);
            color: inherit;
            font: inherit;
            font-weight: 600;
            cursor: pointer;
        }
        .frog-completion-control input { width: 1.1rem; height: 1.1rem; }
        .frog-completion-control.is-saving { opacity: 0.65; cursor: wait; }
        .frog-completion-error { margin-left: 0.5rem; color: #ef4444; font-size: 0.85rem; }
        .frog-lesson-complete {
            outline: 2px solid #22c55e;
            outline-offset: 2px;
        }
        #frog-lesson-completion { margin: 0 0 1rem; }
    `;
    document.head.appendChild(style);

    let completionState = {};

    function lessonIdFromHref(href) {
        try {
            const path = new URL(href, window.location.href).pathname;
            const filename = path.split("/").pop();
            if (!filename || !filename.endsWith(".html") || filename === "index.html") return null;
            return filename.slice(0, -5);
        } catch {
            return null;
        }
    }

    async function saveCompletion(lessonId, complete, checkbox, container, error) {
        const previous = !complete;
        checkbox.disabled = true;
        container.classList.add("is-saving");
        error.textContent = "";

        try {
            const response = await fetch(`/api/lessons/${encodeURIComponent(lessonId)}/completion`, {
                method: "PUT",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({complete})
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
            completionState[lessonId] = {complete: data.complete};
            setContainerState(container, data.complete);
        } catch (requestError) {
            checkbox.checked = previous;
            setContainerState(container, previous);
            error.textContent = `Could not save: ${requestError.message}`;
        } finally {
            checkbox.disabled = false;
            container.classList.remove("is-saving");
        }
    }

    function setContainerState(container, complete) {
        const tile = container.closest(".lesson-card, article, li");
        if (tile) tile.classList.toggle("frog-lesson-complete", complete);
    }

    function addControl(lessonId, parent, id) {
        if (!lessonId || parent.querySelector(`[data-frog-lesson-id="${CSS.escape(lessonId)}"]`)) return;

        const wrapper = document.createElement("div");
        if (id) wrapper.id = id;

        const label = document.createElement("label");
        label.className = "frog-completion-control";
        label.dataset.frogLessonId = lessonId;

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = Boolean(completionState[lessonId]?.complete);

        const text = document.createElement("span");
        text.textContent = "Completed";

        const error = document.createElement("span");
        error.className = "frog-completion-error";

        label.append(checkbox, text);
        wrapper.append(label, error);
        parent.appendChild(wrapper);
        setContainerState(label, checkbox.checked);

        checkbox.addEventListener("change", () => {
            saveCompletion(lessonId, checkbox.checked, checkbox, label, error);
        });
    }

    function renderControls() {
        const currentFilename = window.location.pathname.split("/").pop();
        const isIndex = !currentFilename || currentFilename === "index.html";

        if (isIndex) {
            document.querySelectorAll('a[href$=".html"]').forEach(anchor => {
                const lessonId = lessonIdFromHref(anchor.href);
                if (!lessonId || !completionState[lessonId]) return;
                const tile = anchor.closest(".lesson-card, article, li") || anchor.parentElement;
                addControl(lessonId, tile);
            });
            return;
        }

        const lessonId = lessonIdFromHref(window.location.href);
        const lesson = document.getElementById("lesson");
        if (lessonId && lesson && completionState[lessonId]) {
            const holder = document.createElement("div");
            lesson.prepend(holder);
            addControl(lessonId, holder, "frog-lesson-completion");
        }
    }

    async function refreshCompletionState() {
        try {
            const response = await fetch("/api/completions", {cache: "no-store"});
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
            completionState = data.lessons || {};

            document.querySelectorAll("[data-frog-lesson-id]").forEach(label => {
                const state = completionState[label.dataset.frogLessonId];
                const checkbox = label.querySelector('input[type="checkbox"]');
                if (state && checkbox && !checkbox.disabled) {
                    checkbox.checked = Boolean(state.complete);
                    setContainerState(label, checkbox.checked);
                }
            });
        } catch (error) {
            console.error("Could not load lesson completion state", error);
        }
    }

    document.addEventListener("DOMContentLoaded", async () => {
        await refreshCompletionState();
        renderControls();
    });
    window.addEventListener("pageshow", refreshCompletionState);
    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") refreshCompletionState();
    });
})();
"""


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

        if urlparse(self.path).path == COMPLETION_SCRIPT_PATH:
            self.send_bytes(
                COMPLETION_SCRIPT.encode("utf-8"),
                "text/javascript; charset=utf-8"
            )
            return

        if self.send_html_with_completion_script():
            return

        super().do_GET()

    def send_html_with_completion_script(self):
        request_path = urlparse(self.path).path
        filesystem_path = Path(self.translate_path(request_path))

        if filesystem_path.is_dir() and request_path.endswith("/"):
            filesystem_path = filesystem_path / "index.html"
        elif not request_path.endswith(".html"):
            return False

        if not filesystem_path.is_file():
            return False

        page = filesystem_path.read_text(encoding="utf-8")
        if COMPLETION_SCRIPT_TAG not in page:
            closing_body = page.lower().rfind("</body>")
            if closing_body >= 0:
                page = page[:closing_body] + COMPLETION_SCRIPT_TAG + "\n" + page[closing_body:]
            else:
                page += "\n" + COMPLETION_SCRIPT_TAG

        self.send_bytes(page.encode("utf-8"), "text/html; charset=utf-8")
        return True

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
    with completion_lock:
        curricula_path = Path(__file__).resolve().parent / "Curricula"
        for topic_path in curricula_path.glob("*/*/topics/*.yaml"):
            topic = Topic.load(topic_path)
            for lesson_outline in topic.lesson_outlines:
                states[lesson_outline.id] = {"complete": lesson_outline.complete}
    return states


def set_lesson_completion(lesson_id, complete):
    with completion_lock:
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
