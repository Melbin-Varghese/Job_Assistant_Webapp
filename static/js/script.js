// // ================================
// // Search Filter Expand
// // ================================

// document.addEventListener("DOMContentLoaded", () => {

//     const triggerInput = document.getElementById("trigger-input");
//     const expandedFilters = document.getElementById("expanded-filters");
//     const searchContainer = document.getElementById("search-container");

//     if (triggerInput && expandedFilters && searchContainer) {

//         triggerInput.addEventListener("focus", () => {
//             expandedFilters.classList.remove("hidden");
//         });

//         document.addEventListener("click", (e) => {
//             if (!searchContainer.contains(e.target)) {
//                 expandedFilters.classList.add("hidden");
//             }
//         });

//     }

// });


// // ================================
// // Navbar Scroll Effect
// // ================================

// document.addEventListener("DOMContentLoaded", () => {

//     const nav = document.querySelector("nav");

//     if (nav) {

//         window.addEventListener("scroll", () => {

//             if (window.scrollY > 20) {

//                 nav.classList.add("bg-white/90");
//                 nav.classList.add("backdrop-blur-md");
//                 nav.classList.remove("bg-surface-container-lowest");

//             } else {

//                 nav.classList.remove("bg-white/90");
//                 nav.classList.remove("backdrop-blur-md");
//                 nav.classList.add("bg-surface-container-lowest");

//             }

//         });

//     }

// });


// // ================================
// // Smooth Scroll
// // ================================

// document.querySelectorAll('a[href^="#"]').forEach(anchor => {

//     anchor.addEventListener("click", function (e) {

//         e.preventDefault();

//         const target = document.querySelector(this.getAttribute("href"));

//         if (target) {

//             target.scrollIntoView({

//                 behavior: "smooth"

//             });

//         }

//     });

// });


// // ================================
// // Hero Animation
// // ================================

// window.addEventListener("load", () => {

//     document.querySelectorAll(".card-hover-effect").forEach(card => {

//         card.classList.add("transition-all");

//     });

// });


// ================================
// Search Filter Expand
// ================================

document.addEventListener("DOMContentLoaded", () => {

    const triggerInput = document.getElementById("trigger-input");
    const expandedFilters = document.getElementById("expanded-filters");
    const searchContainer = document.getElementById("search-container");

    if (triggerInput && expandedFilters && searchContainer) {

        triggerInput.addEventListener("focus", () => {
            expandedFilters.classList.remove("hidden");
        });

        document.addEventListener("click", (e) => {
            if (!searchContainer.contains(e.target)) {
                expandedFilters.classList.add("hidden");
            }
        });

    }

});


// ================================
// Navbar Scroll Effect
// ================================

document.addEventListener("DOMContentLoaded", () => {

    const nav = document.querySelector("nav");

    if (nav) {

        window.addEventListener("scroll", () => {

            if (window.scrollY > 20) {

                nav.classList.add("bg-white/90");
                nav.classList.add("backdrop-blur-md");
                nav.classList.remove("bg-surface-container-lowest");

            } else {

                nav.classList.remove("bg-white/90");
                nav.classList.remove("backdrop-blur-md");
                nav.classList.add("bg-surface-container-lowest");

            }

        });

    }

});


// ================================
// Smooth Scroll
// ================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {

    anchor.addEventListener("click", function (e) {

        e.preventDefault();

        const target = document.querySelector(this.getAttribute("href"));

        if (target) {

            target.scrollIntoView({

                behavior: "smooth"

            });

        }

    });

});


// ================================
// Hero Animation
// ================================

window.addEventListener("load", () => {

    document.querySelectorAll(".card-hover-effect").forEach(card => {

        card.classList.add("transition-all");

    });

});


// ================================
// AI Chat (floating widget + full coach page)
// ================================
// Shared logic for any chat UI on the page: a toggle button (optional --
// the full-page coach view has no toggle, it's always visible), a message
// list, a text input, and a send button. Posts to /api/chat and renders
// the reply. Missing elements are skipped safely so this works whether
// the page has zero, one, or both chat UIs.

function wireChatWidget({ toggleBtnId, closeBtnId, windowId, messagesId, inputId, sendBtnId }) {
    const messages = document.getElementById(messagesId);
    const input = document.getElementById(inputId);
    const sendBtn = document.getElementById(sendBtnId);

    if (!messages || !input || !sendBtn) {
        return; // this chat UI isn't present on this page
    }

    const toggleBtn = toggleBtnId ? document.getElementById(toggleBtnId) : null;
    const closeBtn = closeBtnId ? document.getElementById(closeBtnId) : null;
    const chatWindow = windowId ? document.getElementById(windowId) : null;

    if (toggleBtn && chatWindow) {
        toggleBtn.addEventListener("click", () => {
            chatWindow.classList.toggle("hidden");
        });
    }
    if (closeBtn && chatWindow) {
        closeBtn.addEventListener("click", () => {
            chatWindow.classList.add("hidden");
        });
    }

    function appendMessage(text, sender) {
        const bubble = document.createElement("div");
        bubble.className = `message ${sender === "user" ? "user-message" : "bot-message"}`;
        bubble.textContent = text;
        messages.appendChild(bubble);
        messages.scrollTop = messages.scrollHeight;
    }

    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;

        appendMessage(text, "user");
        input.value = "";
        sendBtn.disabled = true;

        const thinking = document.createElement("div");
        thinking.className = "message bot-message";
        thinking.textContent = "…";
        messages.appendChild(thinking);
        messages.scrollTop = messages.scrollHeight;

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text })
            });
            const data = await response.json();
            thinking.remove();

            if (data.error) {
                appendMessage("Sorry, something went wrong. Please try again.", "bot");
                console.error("Chat API error:", data.error);
            } else {
                appendMessage(data.response, "bot");
            }
        } catch (err) {
            thinking.remove();
            appendMessage("Sorry, I couldn't reach the server. Please try again.", "bot");
            console.error("Chat request failed:", err);
        } finally {
            sendBtn.disabled = false;
            input.focus();
        }
    }

    sendBtn.addEventListener("click", sendMessage);
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            sendMessage();
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    // Floating widget on main_explore.html
    wireChatWidget({
        toggleBtnId: "chat-toggle-btn",
        closeBtnId: "close-chat-btn",
        windowId: "chat-window",
        messagesId: "chat-messages",
        inputId: "chat-input",
        sendBtnId: "send-chat-btn"
    });

    // Full-page coach workspace on chatbot.html (no toggle -- always open)
    wireChatWidget({
        messagesId: "coach-messages",
        inputId: "coach-input",
        sendBtnId: "send-coach-btn"
    });
});