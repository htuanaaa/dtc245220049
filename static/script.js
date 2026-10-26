let username = "";
while (true) {
    username = (prompt("Nhập tên của bạn:") || "").trim() || "khách_" + Math.floor(Math.random() * 1000);
    if (username.length >= 3 && username.length <= 50) break;
    alert("Tên người dùng cần 3 - 50 ký tự. vui lòng nhập lại!");
}
let roomId = "";
while (true) {
    roomId = (prompt("Nhập mã phòng:") || "").trim() || "Phòng_chung";
    if (roomId.length >= 3 && roomId.length <= 30) break;
    alert("Mã phòng cần 3 - 30 ký tự. vui lòng nhập lại!");
}

const protocol = window.location.protocol === "https:" ? "wss" : "ws";
const ws = new WebSocket(`${protocol}://${window.location.host}/ws/${encodeURIComponent(roomId)}?username=${encodeURIComponent(username)}`);

const chatBox = document.getElementById("chat-box");
const msgInput = document.getElementById("message-input");
const typingStatus = document.getElementById("typing-status");
let typingTimeout = null;

document.getElementById("room-display").textContent = roomId;
document.getElementById("user-display").textContent = username;

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.type) {
        case "history":
            data.messages.forEach(msg => renderChatMessage(msg));
            break;
        case "system":
            renderSystemMessage(data.content);
            break;
        case "chat":
            renderChatMessage(data);
            break;
        case "typing":
            showTyping(data.sender);
            break;
    }
};

function renderSystemMessage(text) {
    const el = document.createElement("div");
    el.className = "msg system";
    el.textContent = text;
    chatBox.appendChild(el);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function renderChatMessage(data) {
    const isMe = (data.sender === username);
    const el = document.createElement("div");
    el.className = `msg ${isMe ? "me" : "other"}`;

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = `${isMe ? "Bạn" : data.sender} • ${data.time}`;

    const text = document.createElement("div");
    text.textContent = data.content;

    el.appendChild(meta);
    el.appendChild(text);
    chatBox.appendChild(el);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function showTyping(sender) {
    typingStatus.textContent = `${sender} đang soạn tin nhắn...`;
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        typingStatus.textContent = "";
    }, 2000);
}

function send() {
    const content = msgInput.value.trim();
    if (content && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "chat", content: content }));
        msgInput.value = "";
    }
}

document.getElementById("send-btn").onclick = send;
msgInput.onkeydown = (e) => {
    if (e.key === "Enter") send();
};

msgInput.addEventListener("input", () => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "typing" }));
    }
});

window.addEventListener("pageshow", (event) => {
    const nav = performance.getEntriesByType("navigation")[0];
    if (event.persisted || nav && nav.type === "back_forward") {
        window.location.reload()
    }
});