const BACKEND_URL = "http://localhost:5000/chat";

let questionCount = 0;

function updateDashboard(sentiment, language) {
  questionCount++;

  // Update question count with animation
  const qEl = document.getElementById("stat-questions");
  qEl.style.color = "#19c37d";
  qEl.innerText = questionCount;
  setTimeout(() => qEl.style.color = "#ececec", 600);

  // Update mood
  const moodEl = document.getElementById("stat-mood");
  if (sentiment === "negative") {
    moodEl.innerHTML = "😔 Upset";
    moodEl.style.color = "#ff6b6b";
  } else if (sentiment === "positive") {
    moodEl.innerHTML = "😊 Happy";
    moodEl.style.color = "#19c37d";
  } else {
    moodEl.innerHTML = "😐 Neutral";
    moodEl.style.color = "#8e8e8e";
  }

  // Update language
  const langEl = document.getElementById("stat-lang");
  langEl.innerHTML = language === "hindi" ? "🇮🇳 Hindi" : "🇬🇧 English";

  // Update response mode
  const modeEl = document.getElementById("stat-mode");
  if (sentiment === "negative") {
    modeEl.innerHTML = "💙 Empathy";
    modeEl.style.color = "#ff6b6b";
  } else {
    modeEl.innerHTML = "⚡ Standard";
    modeEl.style.color = "#19c37d";
  }
}

// Conversation history array — this gives the bot MEMORY
// Every message is stored here and sent to backend each time
let conversationHistory = [];

// Add a message bubble to chat
function addMessage(text, role, sentiment = "neutral") {
  const messages = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = `message ${role}`;

  if (role === "bot") {
    let sentimentBadge = "";
    if (sentiment === "negative") {
      sentimentBadge = `<span style="font-size:10px;color:#ff6b6b;margin-left:6px;">● empathy mode</span>`;
    } else if (sentiment === "positive") {
      sentimentBadge = `<span style="font-size:10px;color:#19c37d;margin-left:6px;">● positive</span>`;
    }

    const uid = "tb" + Date.now();
    div.innerHTML = `
      <div class="bot-icon">🤖</div>
      <div>
        <div style="display:flex;align-items:center;margin-bottom:4px;">
          <span style="font-size:11px;color:#5a5a5a;font-weight:500;">EduBot</span>
          ${sentimentBadge}
        </div>
        <div class="bubble" id="${uid}"></div>
      </div>`;

    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;

    // Letter by letter typing
    const bubble = document.getElementById(uid);
    let i = 0;
    function typeChar() {
      if (i < text.length) {
        bubble.innerHTML = text.substring(0, i + 1).replace(/\n/g, "<br>");
        i++;
        messages.scrollTop = messages.scrollHeight;
        setTimeout(typeChar, 16);
      }
    }
    typeChar();

  } else {
    div.innerHTML = `<div class="bubble">${text}</div>`;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }
}
// Show or hide typing indicator
function showTyping(visible) {
  document.getElementById("typing").style.display =
    visible ? "flex" : "none";
}

// Main function — sends message to backend WITH history
async function sendMessage(text) {
  if (!text || text.trim() === "") return;

  document.getElementById("user-input").disabled = true;

  // Add user message to screen
  addMessage(text, "user");

  // Add to conversation history (memory)
  conversationHistory.push({
    role: "user",
    content: text
  });

  showTyping(true);

  try {
    const response = await fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        history: conversationHistory  // Send full history for memory
      })
    });

    const data = await response.json();
    showTyping(false);

    if (data.answer) {
      // Add bot response to screen with sentiment
      addMessage(data.answer, "bot", data.sentiment);
      updateDashboard(data.sentiment, data.language);

      // Add bot response to history too (so bot remembers what IT said)
      conversationHistory.push({
        role: "assistant",
        content: data.answer
      });

      // Keep history to last 10 messages only (5 turns)
      if (conversationHistory.length > 10) {
        conversationHistory = conversationHistory.slice(-10);
      }

    } else {
      addMessage("Sorry, something went wrong. Please try again!", "bot");
    }

  } catch (error) {
    showTyping(false);
    addMessage(
      "Connection error. Make sure the backend server is running!\n(Run: python app.py in your terminal)",
      "bot"
    );
    console.error("Error:", error);
  }

  document.getElementById("user-input").disabled = false;
  document.getElementById("user-input").focus();
}

// Send button
function handleSend() {
  const input = document.getElementById("user-input");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  sendMessage(text);
}

// Enter key
function handleKey(event) {
  if (event.key === "Enter") handleSend();
}

// Clear chat button — resets memory too
function clearChat() {
  conversationHistory = [];
  const messages = document.getElementById("messages");
  messages.innerHTML = `
    <div class="message bot">
      <div class="bot-icon">🤖</div>
      <div class="bubble" style="color:#8e8e8e">
        Hi! I'm EduBot — your college AI helpdesk. Ask me anything about admissions, fees, exams, hostel, or placements!
      </div>
    </div>`;
}