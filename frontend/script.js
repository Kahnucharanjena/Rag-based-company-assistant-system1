const API_URL = "http://127.0.0.1:8000";

let sessionId = localStorage.getItem("session_id");

if (!sessionId) {
    sessionId = Date.now().toString();
    localStorage.setItem("session_id", sessionId);
}

const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const chatContainer = document.getElementById("chatContainer");

const fileInput = document.getElementById("fileInput");
const processButton = document.getElementById("processButton");
const fileName = document.getElementById("fileName");


function addMessage(message, type) {

    const div = document.createElement("div");

    div.className = "message " + type;

    const content = document.createElement("div");

    content.className = "message-content";

    content.textContent = message;

    div.appendChild(content);

    chatContainer.appendChild(div);

    chatContainer.scrollTop = chatContainer.scrollHeight;

    return div;
}


/* =========================
   CHAT
========================= */

async function sendMessage() {

    const message = messageInput.value.trim();

    if (message === "") {
        return;
    }

    addMessage(message, "user");

    messageInput.value = "";

    const thinking = addMessage("Thinking...", "ai");

    sendButton.disabled = true;

    try {

        console.log("Sending message:", message);

        const response = await fetch(
            API_URL + "/api/chat",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: message,
                    session_id: sessionId
                })
            }
        );

        const data = await response.json();

        console.log("Chat response:", data);

        if (!response.ok) {
            throw new Error(
                data.detail || "Server error: " + response.status
            );
        }

        thinking.querySelector(
            ".message-content"
        ).textContent = data.answer;

    } catch (error) {

        console.error("CHAT ERROR:", error);

        thinking.querySelector(
            ".message-content"
        ).textContent =
            "Error: " + error.message;

    } finally {

        sendButton.disabled = false;
    }
}


/* SEND BUTTON */

sendButton.addEventListener(
    "click",
    sendMessage
);


/* ENTER KEY */

messageInput.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();
        }
    }
);


/* =========================
   FILE SELECTION
========================= */

fileInput.addEventListener(
    "change",
    function() {

        if (fileInput.files.length > 0) {

            fileName.textContent =
                fileInput.files[0].name;

            console.log(
                "Selected:",
                fileInput.files[0].name
            );

        } else {

            fileName.textContent =
                "No file selected";
        }
    }
);


/* =========================
   PROCESS PDF
========================= */

processButton.addEventListener(
    "click",
    async function() {

        if (fileInput.files.length === 0) {

            alert(
                "Please select a PDF file first."
            );

            return;
        }

        const file = fileInput.files[0];

        if (
            !file.name
                .toLowerCase()
                .endsWith(".pdf")
        ) {

            alert(
                "Please select a PDF file."
            );

            return;
        }

        processButton.disabled = true;

        processButton.textContent =
            "Processing...";

        try {

            console.log(
                "Uploading PDF:",
                file.name
            );

            const formData = new FormData();

            formData.append(
                "file",
                file
            );

            const response = await fetch(
                API_URL + "/api/upload",
                {
                    method: "POST",
                    body: formData
                }
            );

            const data = await response.json();

            console.log(
                "Upload response:",
                data
            );

            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Upload failed: " +
                    response.status
                );
            }

            processButton.textContent =
                "Processed ✓";

            alert(
                data.message ||
                "Document processed successfully!"
            );

        } catch (error) {

            console.error(
                "UPLOAD ERROR:",
                error
            );

            processButton.textContent =
                "Process Document";

            alert(
                "Error: " + error.message
            );

        } finally {

            processButton.disabled = false;
        }
    }
);


/* =========================
   SUGGESTIONS
========================= */

function useSuggestion(question) {

    messageInput.value = question;

    messageInput.focus();
}