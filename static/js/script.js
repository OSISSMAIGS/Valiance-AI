document.addEventListener('DOMContentLoaded', function() {
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');
    const welcomeScreen = document.getElementById('welcome-screen');
    const newChatBtn = document.querySelector('.new-chat-btn');
    const backBtn = document.querySelector('.back-btn');
    const chatHistory = document.querySelector('.chat-history');
    
    let conversations = [];
    let currentConversationId = generateId();
    
    // Konfigurasi Marked.js untuk parsing Markdown
    marked.setOptions({
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            } else {
                return hljs.highlightAuto(code).value;
            }
        },
        langPrefix: 'hljs language-',
        breaks: true,
        gfm: true
    });
    
    // Auto-resize textarea as user types
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        
        // Enable/disable send button based on input
        sendButton.disabled = this.value.trim() === '';
    });
    
    // Handle pressing Enter to send message (Shift+Enter for new line)
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!sendButton.disabled) {
                sendMessage();
            }
        }
    });
    
    // Send button click handler
    sendButton.addEventListener('click', sendMessage);
    
    // New chat button handler
    newChatBtn.addEventListener('click', startNewChat);

    backBtn.addEventListener('click', function() {
        window.location.href = 'https://osissmaigs.com';
    });
    
    // Function to send message
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        // Hide welcome screen and show chat
        welcomeScreen.style.display = 'none';
        chatMessages.style.display = 'block';
        
        // Add user message to UI
        appendMessage('user', message);
        
        // Clear input and reset height
        userInput.value = '';
        userInput.style.height = 'auto';
        sendButton.disabled = true;
        
        // Show typing indicator
        const typingIndicator = appendTypingIndicator();
        
        // Save message to current conversation
        if (!conversations.find(c => c.id === currentConversationId)) {
            const newConversation = {
                id: currentConversationId,
                title: message.substring(0, 30) + (message.length > 30 ? '...' : ''),
                messages: []
            };
            conversations.push(newConversation);
            addConversationToSidebar(newConversation);
        }
        
        // Add message to conversation
        const currentConversation = conversations.find(c => c.id === currentConversationId);
        currentConversation.messages.push({
            role: 'user',
            content: message
        });
        
        // Send message to API
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            if (typingIndicator) {
                typingIndicator.remove();
            }
            
            // Add AI response to UI with Markdown support
            appendMarkdownMessage('ai', data.response);
            
            // Add response to conversation
            currentConversation.messages.push({
                role: 'assistant',
                content: data.response,
                rawMarkdown: data.rawMarkdown || data.response
            });
            
            // Save conversations to local storage
            saveConversations();
            
            // Apply syntax highlighting to code blocks
            document.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Remove typing indicator
            if (typingIndicator) {
                typingIndicator.remove();
            }
            
            // Show error message
            appendMessage('ai', 'Maaf, terjadi kesalahan. Silakan coba lagi.');
        });
    }
    
    // Function to add normal message to UI
    function appendMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${role}`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = `avatar avatar-${role}`;
        
        // Use icon for user, image for AI
        if (role === 'user') {
            const icon = document.createElement('i');
            icon.className = 'fas fa-user';
            avatarDiv.appendChild(icon);
        } else {
            const img = document.createElement('img');
            img.src = '/static/assets/logo.png'; // Path to your AI logo image
            img.alt = 'AI Avatar';
            img.style.width = '100%';
            img.style.height = '100%';
            img.style.objectFit = 'cover';
            img.style.borderRadius = '50%';
            avatarDiv.appendChild(img);
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageDiv;
    }
    
    // Function to add markdown message to UI
    function appendMarkdownMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${role}`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = `avatar avatar-${role}`;
        
        // Use icon for user, image for AI
        if (role === 'user') {
            const icon = document.createElement('i');
            icon.className = 'fas fa-user';
            avatarDiv.appendChild(icon);
        } else {
            const img = document.createElement('img');
            img.src = '/static/assets/logo.png'; // Path to your AI logo image
            img.alt = 'AI Avatar';
            img.style.width = '100%';
            img.style.height = '100%';
            img.style.objectFit = 'cover';
            img.style.borderRadius = '50%';
            avatarDiv.appendChild(img);
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content markdown-content';
        
        // Parse and render markdown
        contentDiv.innerHTML = marked.parse(content);
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageDiv;
    }
    
    // Function to show typing indicator
    function appendTypingIndicator() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message message-ai typing-indicator';
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'avatar avatar-ai';
        
        // Use image for AI in typing indicator too
        const img = document.createElement('img');
        img.src = '/static/assets/logo.png'; // Path to your AI logo image
        img.alt = 'AI Avatar';
        img.style.width = '100%';
        img.style.height = '100%';
        img.style.objectFit = 'cover';
        img.style.borderRadius = '50%';
        avatarDiv.appendChild(img);
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = '<span class="typing-dots"><span>.</span><span>.</span><span>.</span></span>';
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageDiv;
    }
    
    // Function to start a new chat
    function startNewChat() {
        // Reset UI
        chatMessages.innerHTML = '';
        welcomeScreen.style.display = 'flex';
        chatMessages.style.display = 'none';
        
        // Create new conversation
        currentConversationId = generateId();
    }
    
    // Function to handle suggestion clicks
    window.suggestPrompt = function(prompt) {
        userInput.value = prompt;
        userInput.style.height = 'auto';
        userInput.style.height = (userInput.scrollHeight) + 'px';
        sendButton.disabled = false;
        sendMessage();
    };
    
    // Function to add conversation to sidebar
    function addConversationToSidebar(conversation) {
        const listItem = document.createElement('li');
        listItem.className = 'chat-item';
        listItem.dataset.id = conversation.id;
        listItem.innerHTML = `
            <i class="fas fa-comment"></i>
            <span>${conversation.title}</span>
        `;
        
        listItem.addEventListener('click', function() {
            loadConversation(conversation.id);
        });
        
        // Add to chat history
        chatHistory.prepend(listItem);
    }
    
    // Function to load a conversation
    function loadConversation(conversationId) {
        const conversation = conversations.find(c => c.id === conversationId);
        if (!conversation) return;
        
        // Update current conversation
        currentConversationId = conversationId;
        
        // Clear chat messages
        chatMessages.innerHTML = '';
        
        // Hide welcome screen and show chat
        welcomeScreen.style.display = 'none';
        chatMessages.style.display = 'block';
        
        // Add all messages to UI
        conversation.messages.forEach(msg => {
            if (msg.role === 'user') {
                appendMessage('user', msg.content);
            } else {
                // Check if we have raw markdown stored
                if (msg.rawMarkdown) {
                    appendMarkdownMessage('ai', msg.rawMarkdown);
                } else {
                    appendMarkdownMessage('ai', msg.content);
                }
            }
        });
        
        // Apply syntax highlighting to code blocks
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
        
        // Highlight active conversation in sidebar
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.id === conversationId) {
                item.classList.add('active');
            }
        });
    }
    
    // Helper function to generate ID
    function generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
    
    // Save conversations to local storage
    function saveConversations() {
        localStorage.setItem('aiGenie_conversations', JSON.stringify(conversations));
    }
    
    // Load conversations from local storage
    function loadConversations() {
        const saved = localStorage.getItem('aiGenie_conversations');
        if (saved) {
            conversations = JSON.parse(saved);
            
            // Add conversations to sidebar
            conversations.forEach(conversation => {
                addConversationToSidebar(conversation);
            });
        }
    }
    
    // Initialize
    loadConversations();
});