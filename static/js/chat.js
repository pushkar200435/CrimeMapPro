
document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input-field');
    const messagesContainer = document.getElementById('chat-messages-container');

    if (!chatForm || !chatInput || !messagesContainer) return;

    // Helper: Format markdown bold and newlines to HTML
    function formatMessage(text) {
        // Escapes HTML tags to prevent XSS
        let safeText = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
            
        // Map markdown **text** to <strong>text</strong>
        safeText = safeText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Map *text* to <em>text</em>
        safeText = safeText.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Map newlines to break tags
        return safeText.replace(/\n/g, '<br/>');
    }

    // Helper: Scroll container to bottom
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Helper: Append a message to the UI
    function appendMessage(text, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'message-user' : 'message-bot'}`;
        
        if (isUser) {
            // User message is plain text (no markdown formatting needed)
            messageDiv.textContent = text;
        } else {
            // Bot message gets markdown formatting
            messageDiv.innerHTML = formatMessage(text);
        }
        
        messagesContainer.appendChild(messageDiv);
        scrollToBottom();
        return messageDiv;
    }

    // Helper: Show/Hide typing indicator
    let typingBubble = null;
    function showTypingIndicator() {
        typingBubble = document.createElement('div');
        typingBubble.className = 'message message-bot';
        typingBubble.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Analyzing dataset records...`;
        messagesContainer.appendChild(typingBubble);
        scrollToBottom();
    }

    function removeTypingIndicator() {
        if (typingBubble) {
            typingBubble.remove();
            typingBubble = null;
        }
    }

    // Submit handler
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const messageText = chatInput.value.trim();
        if (!messageText) return;
        
        // 1. Add User Message
        appendMessage(messageText, true);
        chatInput.value = '';
        
        // 2. Add Typing Indicator
        showTypingIndicator();
        
        try {
            // 3. Post to API
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: messageText })
            });
            const data = await response.json();
            
            // 4. Update UI
            removeTypingIndicator();
            appendMessage(data.response || "I couldn't compile a response. Please try again.");
            
        } catch (err) {
            removeTypingIndicator();
            appendMessage("Unable to connect to the dataset analysis chatbot. Please check if your server is running.");
        }
    });

    // Auto-focus input
    chatInput.focus();
});
