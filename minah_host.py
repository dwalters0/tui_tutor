from minah_llm import generate
from pathlib import Path
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from utilities import normalise_filename, run_output_through_latex_and_markdown_rendering
import json


# singleton lesson context
_context = ""


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

    def do_GET(self):
        if self.path == "/api/lesson":
            print("lesson hit")
            return
        else:
            reset_context()
            if Path(self.path).is_file():
                with open(self.translate_path(self.path),"r") as f:
                    lesson = f.read()
                    append_to_context(lesson)
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

            append_to_context(question)
            append_to_context(answer)

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
    prompt = f"""Previous context from the conversation
is as follows {get_context()}
###END CONTEXT###
The user has asked {question}.
"""
    answer = generate(prompt,False)
    return f"{run_output_through_latex_and_markdown_rendering(answer)}"




def create_html(lesson,out_path):
    prompt = f"""
You're a smart developer who knows how to create static web sites. Please convert this yaml file into a html file that presents the 
learning content in an engaging and clear way in a dark mode theme. Don't change the lesson content and just return the html file. Return the content of the html file, don't try to create the file. {lesson}
"""
    response = generate(prompt,False)

    html_page = f"""
<head>
    <link rel="stylesheet" href="style.css">
</head>
<div class="layout">
<main id="lesson">
    {response}
</main>

<aside id="chat">
    <aside class="chat-panel">
    <div class="chat-header">
        <div>
            <div class="chat-title">Ask about this lesson</div>
            <div class="chat-subtitle">Questions stay focused on the current topic.</div>
        </div>
    </div>

    <div class="chat-messages" id="chatMessages">
        <div class="message assistant">
            <div class="message-bubble">
                Ask me anything about this lesson.
            </div>
        </div>
    </div>

    <form class="chat-input-area" id="chatForm">
        <textarea
            id="chatInput"
            rows="1"
            placeholder="Ask a question..."
        ></textarea>

        <button type="submit" id="sendButton">
            Send
        </button>
    </form>
</aside>
</aside>
</div>
    """ + """
<script>
const form = document.getElementById("chatForm");
const input = document.getElementById("chatInput");
const messages = document.getElementById("chatMessages");
const sendButton = document.getElementById("sendButton");

let conversation = [];
let waitingForResponse = false;


/*
 * Add a message bubble to the chat UI.
 */
function addMessage(text, role) {
    const message = document.createElement("div");
    message.className = `message ${role}`;

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = text;

    message.appendChild(bubble);
    messages.appendChild(message);

    scrollToBottom();

    return message;
}


/*
 * Show a temporary "Thinking..." message while waiting
 * for the LLM response.
 */
function addTypingIndicator() {
    const message = document.createElement("div");
    message.className = "message assistant";
    message.id = "typingIndicator";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.textContent = "Thinking...";

    message.appendChild(bubble);
    messages.appendChild(message);

    scrollToBottom();
}


/*
 * Remove the temporary typing indicator.
 */
function removeTypingIndicator() {
    const indicator = document.getElementById("typingIndicator");

    if (indicator) {
        indicator.remove();
    }
}


/*
 * Scroll chat to newest message.
 */
function scrollToBottom() {
    messages.scrollTop = messages.scrollHeight;
}


/*
 * Resize textarea as the user types.
 */
function resizeInput() {
    input.style.height = "auto";

    const maxHeight = 140;

    input.style.height =
        Math.min(input.scrollHeight, maxHeight) + "px";
}


/*
 * Enable/disable chat controls while a request is active.
 */
function setLoading(loading) {
    waitingForResponse = loading;
    sendButton.disabled = loading;

    if (loading) {
        sendButton.textContent = "Sending...";
    } else {
        sendButton.textContent = "Send";
    }
}


/*
 * Submit a question to the backend.
 */
async function askQuestion(question) {
    addMessage(question, "user");

    conversation.push({
        role: "user",
        content: question
    });

    input.value = "";
    resizeInput();

    setLoading(true);
    addTypingIndicator();

    try {
        const response = await fetch("/api/ask", {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                question: question,

                // Send previous conversation so the backend
                // can preserve context if desired.
                messages: conversation,

                // Useful if each lesson has its own URL.
                lesson: window.location.pathname
            })
        });

        if (!response.ok) {
            let errorText;

            try {
                const errorData = await response.json();

                errorText =
                    errorData.error ||
                    errorData.message ||
                    `HTTP ${response.status}`;
            } catch {
                errorText = `HTTP ${response.status}`;
            }

            throw new Error(errorText);
        }

        const data = await response.json();

        if (!data.answer) {
            throw new Error(
                "The server returned no answer."
            );
        }

        removeTypingIndicator();

        addMessage(
            data.answer,
            "assistant"
        );

        conversation.push({
            role: "assistant",
            content: data.answer
        });

    } catch (error) {
        console.error(
            "Chat request failed:",
            error
        );

        removeTypingIndicator();

        addMessage(
            `Sorry, I couldn't get an answer. ${error.message}`,
            "assistant"
        );

    } finally {
        setLoading(false);

        input.focus();

        scrollToBottom();
    }
}


/*
 * Form submission.
 */
form.addEventListener(
    "submit",
    async (event) => {
        event.preventDefault();

        if (waitingForResponse) {
            return;
        }

        const question =
            input.value.trim();

        if (!question) {
            return;
        }

        await askQuestion(question);
    }
);


/*
 * Enter sends.
 * Shift+Enter inserts a newline.
 */
input.addEventListener(
    "keydown",
    (event) => {
        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {
            event.preventDefault();

            form.requestSubmit();
        }
    }
);


/*
 * Auto-resize textarea while typing.
 */
input.addEventListener(
    "input",
    resizeInput
);


/*
 * Initial setup.
 */
resizeInput();
input.focus();
</script>
"""
    path = Path(out_path)
    with open(path, 'w') as f:
        f.write(html_page)
    return path.resolve()



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
    response = generate(prompt,False)
    path = Path(out_path)

    css = """
.layout {
    display: grid;
    grid-template-columns: 1fr 360px;
    height: 100vh;
}

#lesson {
    overflow-y: auto;
    padding: 2rem;
}

#chat {
    border-left: 1px solid #ccc;
    overflow-y: auto;
} 
.chat-panel {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: #f8f9fb;
    border-left: 1px solid #e2e5e9;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.chat-header {
    padding: 20px;
    border-bottom: 1px solid #e2e5e9;
    background: #ffffff;
}

.chat-title {
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
}

.chat-subtitle {
    margin-top: 4px;
    font-size: 12px;
    color: #6b7280;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
}

.message {
    display: flex;
}

.message.user {
    justify-content: flex-end;
}

.message.assistant {
    justify-content: flex-start;
}

.message-bubble {
    max-width: 85%;
    padding: 10px 14px;
    border-radius: 14px;
    line-height: 1.45;
    font-size: 14px;
    white-space: pre-wrap;
}

.message.user .message-bubble {
    background: #2563eb;
    color: white;
    border-bottom-right-radius: 4px;
}

.message.assistant .message-bubble {
    background: white;
    color: #1f2937;
    border: 1px solid #e2e5e9;
    border-bottom-left-radius: 4px;
}

.chat-input-area {
    padding: 14px;
    display: flex;
    gap: 10px;
    align-items: flex-end;
    border-top: 1px solid #e2e5e9;
    background: #ffffff;
}

.chat-input-area textarea {
    flex: 1;
    resize: none;
    max-height: 140px;
    min-height: 42px;
    padding: 10px 12px;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    font: inherit;
    font-size: 14px;
    line-height: 1.4;
    outline: none;
}

.chat-input-area textarea:focus {
    border-color: #2563eb;
}

.chat-input-area button {
    height: 42px;
    padding: 0 16px;
    border: 0;
    border-radius: 10px;
    background: #2563eb;
    color: white;
    font-weight: 600;
    cursor: pointer;
}

.chat-input-area button:hover {
    background: #1d4ed8;
}

.chat-input-area button:disabled {
    opacity: 0.5;
    cursor: default;
}
    """
    css_path = Path(out_path).parent / "style.css"
    with open(css_path, 'w') as f:
        f.write(css)

    with open(path, 'w') as f:
        f.write(response)
    return path.resolve()