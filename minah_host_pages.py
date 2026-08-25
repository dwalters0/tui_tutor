
def get_lesson_html(response):
    return f"""
<head>
    <link rel="stylesheet" href="style.css">
</head>
<div class="layout">
<main id="lesson">
    {response}
</main>


<aside id=chat-panel class="chat-panel">
    <button
    class="chat-toggle"
    id="chatToggle"
    aria-label="Hide chat"
    aria-expanded="true">
    ▼
    </button>
    <div class="chat-header">
        <div>
            <div class="chat-title">Ask about this lesson</div>
            <div class="chat-subtitle">Questions stay focused on the current topic.</div>
        </div>
    </div>
    
    <div class="chat-messages" id="chatMessages">
        <div class="message assistant">
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
</div>
    """ + """
<script>

/*
 * Mobile chat panel hide
 */
const chatPanel = document.getElementById("chat-panel");
const chatToggle = document.getElementById("chatToggle");

chatToggle.addEventListener("click", () => {
    const collapsed = chatPanel.classList.toggle("collapsed");

    chatToggle.textContent = collapsed ? "▲" : "▼";
    chatToggle.setAttribute("aria-expanded", !collapsed);
    chatToggle.setAttribute(
        "aria-label",
        collapsed ? "Show chat" : "Hide chat"
    );
});

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

def get_index_css():
    return """
html, body {
    margin: 0;
    height: 100%;

.layout {
    display: flex;
    height: 100vh;
    overflow: hidden;
}

main {
    flex: 1;
    min-width: 0;
    overflow-y: auto;
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
    width: 350px;
    overflow-y: auto;
    border-left: 1px solid #ccc;
}

.chat-toggle {
    display: none;
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
    padding: 0px;
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
    font-size: 16px;
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

/* Mobile */
@media (max-width: 1620px) {
    .chat-panel {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        max-height: 45vh;
        transition: transform 0.25s ease;
    }
    
    .chat-title {
        display: none;
    }
    .chat-subtitle {
        display: none;
    }

    /*
     * Move everything except the toggle button below the screen.
     * 40px is the height left visible for the toggle.
     */
    .chat-panel.collapsed {
        height: 40px
    }

.chat-toggle {
        display: block;
        position: sticky;
        top: 0;
        z-index: 10;

        height: 40px;
        width: 100%;
        cursor: pointer;
    }

        .chat-header{
    display: none;
    }
}
"""