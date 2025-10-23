class ChatApp {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatForm = document.getElementById('chatForm');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.newChatBtn = document.getElementById('newChatBtn');
        this.conversationsList = document.getElementById('conversationsList');
        this.welcomeMessage = document.getElementById('welcomeMessage');
        this.currentChatTitle = document.getElementById('currentChatTitle');
        this.currentConversationId = null;
        this.isSending = false; // Flag to prevent double execution
        this.conversations = new Map(); // Store conversation data
        
        this.init();
    }
    
    init() {
        // Event listeners
        this.chatForm.addEventListener('submit', (e) => this.handleSubmit(e));
        this.newChatBtn.addEventListener('click', (e) => this.handleNewChat(e));
        this.messageInput.addEventListener('input', (e) => this.handleInputResize(e));
        this.messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // Load conversations first
        this.loadConversations();
        
        // Focus on input and set initial height
        this.messageInput.focus();
        this.handleInputResize();
    }
    
    
    async handleSubmit(e) {
        e.preventDefault();
        
        // Prevent double execution
        if (this.isSending) {
            console.log('Message already being sent, ignoring duplicate request');
            return;
        }
        
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Hide welcome message on first message
        if (this.welcomeMessage) {
            this.welcomeMessage.style.display = 'none';
        }
        
        // Set sending flag
        this.isSending = true;
        
        // Clear input and disable form
        this.messageInput.value = '';
        this.handleInputResize(); // Reset textarea height
        this.setFormDisabled(true);
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            const response = await this.sendMessage(message);
            this.hideTypingIndicator();
            
            // Create structured message object for display
            const structuredMsg = {
                user_message: message,
                bot_response: response.response,
                context_summary: response.context_summary || null
            };
            
            // Add the complete structured message (user + bot + summary)
            this.addStructuredMessage(structuredMsg);
            
            // Update conversation title if it's the first message
            this.updateConversationTitle(message);
            
            // Refresh conversations list to show the new conversation
            setTimeout(() => {
                this.loadConversations();
            }, 1000);
        } catch (error) {
            this.hideTypingIndicator();
            this.showError(`Error: ${error.message}`);
            console.error('Chat error:', error);
        } finally {
            this.setFormDisabled(false);
            this.isSending = false; // Reset sending flag
            this.messageInput.focus();
        }
    }
    
    handleNewChat(e) {
        e.preventDefault();
        
        // Clear current conversation
        this.currentConversationId = null;
        localStorage.removeItem('currentConversationId');
        
        // Clear current chat
        this.clearCurrentChat();
        
        // Show welcome message
        if (this.welcomeMessage) {
            this.welcomeMessage.style.display = 'flex';
        }
        
        // Update title
        this.currentChatTitle.textContent = 'ChatGPT';
        
        // Update active conversation in sidebar
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Focus on input
        this.messageInput.focus();
    }
    
    handleInputResize(e) {
        const textarea = this.messageInput;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
    
    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.handleSubmit(e);
        }
    }
    
    
    updateConversationTitle(firstMessage) {
        if (this.currentChatTitle.textContent === 'ChatGPT') {
            const title = firstMessage.length > 30 ? firstMessage.substring(0, 30) + '...' : firstMessage;
            this.currentChatTitle.textContent = title;
        }
    }
    
    clearCurrentChat() {
        // Clear messages except welcome message
        const messages = this.chatMessages.querySelectorAll('.message');
        messages.forEach(msg => msg.remove());
        
        // Show welcome message
        if (this.welcomeMessage) {
            this.welcomeMessage.style.display = 'flex';
        }
    }
    
    async sendMessage(message) {
        const response = await fetch('/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
            },
            body: JSON.stringify({ 
                message: message,
                conversation_id: this.currentConversationId
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('API Error:', response.status, errorData);
            throw new Error(errorData.error || `HTTP ${response.status}: Network error`);
        }
        
        const data = await response.json();
        
        // Update conversation ID if provided
        if (data.conversation_id) {
            this.currentConversationId = data.conversation_id;
            localStorage.setItem('currentConversationId', this.currentConversationId);
        }
        
        return data;
    }
    
    async loadConversations() {
        try {
            console.log('Loading conversations...');
            const response = await fetch('/api/conversations/');
            console.log('Response status:', response.status);
            
            if (response.ok) {
                const data = await response.json();
                console.log('Conversations data:', data);
                this.displayConversations(data.conversations || []);
            } else {
                console.error('Failed to load conversations:', response.status);
                this.displayConversations([]);
            }
        } catch (error) {
            console.error('Error loading conversations:', error);
            // Show empty state if no conversations
            this.displayConversations([]);
        }
    }
    
    displayConversations(conversations) {
        console.log('Displaying conversations:', conversations);
        this.conversationsList.innerHTML = '';
        
        if (conversations.length === 0) {
            console.log('No conversations to display');
            // Show a message when no conversations exist
            const noConversationsDiv = document.createElement('div');
            noConversationsDiv.className = 'no-conversations';
            noConversationsDiv.style.cssText = `
                padding: 16px;
                text-align: center;
                color: #9ca3af;
                font-size: 14px;
                font-style: italic;
            `;
            noConversationsDiv.textContent = 'No conversations yet. Start a new chat!';
            this.conversationsList.appendChild(noConversationsDiv);
            return;
        }
        
        conversations.forEach(conv => {
            console.log('Creating conversation element for:', conv);
            const convElement = this.createConversationElement(conv);
            this.conversationsList.appendChild(convElement);
        });
    }
    
    createConversationElement(conversation) {
        const div = document.createElement('div');
        div.className = 'conversation-item';
        if (conversation.id === this.currentConversationId) {
            div.classList.add('active');
        }
        
        div.innerHTML = `
            <div class="conversation-title" title="${conversation.title}">${conversation.title}</div>
            <div class="conversation-actions">
                <button class="conversation-action" onclick="event.stopPropagation(); chatApp.deleteConversation(${conversation.id})" title="Delete">
                    🗑️
                </button>
            </div>
        `;
        
        div.addEventListener('click', () => this.loadConversation(conversation.id));
        
        return div;
    }
    
    async loadConversation(conversationId) {
        if (conversationId === this.currentConversationId) return;
        
        try {
            const response = await fetch(`/api/conversations/${conversationId}/`);
            if (!response.ok) {
                throw new Error('Failed to load conversation');
            }
            
            const data = await response.json();
            const conversation = data.conversation;
            
            this.currentConversationId = conversationId;
            localStorage.setItem('currentConversationId', conversationId);
            
            // Update active conversation
            document.querySelectorAll('.conversation-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // Find and activate the clicked conversation
            const conversationElements = document.querySelectorAll('.conversation-item');
            conversationElements.forEach(item => {
                if (item.querySelector(`[onclick*="${conversationId}"]`)) {
                    item.classList.add('active');
                }
            });
            
            // Clear current chat and load conversation messages
            this.clearCurrentChat();
            
            // Load conversation messages
            this.displayConversationMessages(conversation.messages);
            
            // Update title
            this.currentChatTitle.textContent = conversation.title;
            
            // Focus on input
            this.messageInput.focus();
        } catch (error) {
            console.error('Error loading conversation:', error);
            this.showError('Failed to load conversation');
        }
    }
    
    displayConversationMessages(messages) {
        // Hide welcome message
        if (this.welcomeMessage) {
            this.welcomeMessage.style.display = 'none';
        }
        
        // Display all messages in the conversation
        messages.forEach(msg => {
            this.addStructuredMessage(msg, false);
        });
        
        this.scrollToBottom();
    }
    
    async deleteConversation(conversationId) {
        if (!confirm('Are you sure you want to delete this conversation?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/conversations/${conversationId}/delete/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                }
            });
            
            if (response.ok) {
                // Remove from UI
                const convElement = document.querySelector(`[onclick*="${conversationId}"]`);
                if (convElement) {
                    convElement.remove();
                }
                
                // If this was the current conversation, start a new one
                if (conversationId == this.currentConversationId) {
                    this.handleNewChat(new Event('click'));
                }
            } else {
                throw new Error('Failed to delete conversation');
            }
        } catch (error) {
            console.error('Error deleting conversation:', error);
            this.showError('Failed to delete conversation');
        }
    }
    
    
    addMessage(content, sender, scroll = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = sender === 'user' ? 'You' : 'AI';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;
        
        // Add avatar and content in correct order
        if (sender === 'user') {
            messageDiv.appendChild(messageContent);
            messageDiv.appendChild(avatar);
        } else {
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(messageContent);
        }
        
        this.chatMessages.appendChild(messageDiv);
        
        if (scroll) {
            this.scrollToBottom();
        }
    }
    
    addStructuredMessage(msg, scroll = true) {
        // Add user message
        this.addMessage(msg.user_message, 'user', false);
        
        // Add bot response with structured format
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = 'AI';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Bot Response section
        const botSection = document.createElement('div');
        botSection.className = 'message-section';
        botSection.innerHTML = `
            <div class="section-label">Bot Response</div>
            <div class="section-content">${this.escapeHtml(msg.bot_response)}</div>
        `;
        messageContent.appendChild(botSection);
        
        // Summary section (if exists)
        if (msg.context_summary) {
            const summarySection = document.createElement('div');
            summarySection.className = 'message-section summary-section';
            summarySection.innerHTML = `
                <div class="section-label">Summary</div>
                <div class="section-content">${this.escapeHtml(msg.context_summary)}</div>
            `;
            messageContent.appendChild(summarySection);
        }
        
        // Add avatar and content in correct order for bot
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        this.chatMessages.appendChild(messageDiv);
        
        if (scroll) {
            this.scrollToBottom();
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showTypingIndicator() {
        this.typingIndicator.style.display = 'block';
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        this.chatMessages.appendChild(errorDiv);
        this.scrollToBottom();
        
        // Remove error message after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }
    
    setFormDisabled(disabled) {
        this.sendButton.disabled = disabled;
        this.messageInput.disabled = disabled;
        
        if (disabled) {
            this.sendButton.textContent = 'Sending...';
        } else {
            this.sendButton.textContent = 'Send';
        }
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }
    
    
    
    showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.textContent = message;
        
        this.chatMessages.appendChild(successDiv);
        this.scrollToBottom();
        
        // Remove success message after 3 seconds
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.parentNode.removeChild(successDiv);
            }
        }, 3000);
    }
}

// Initialize the chat app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
    
    // Add global function for debugging
    window.refreshConversations = () => {
        window.chatApp.loadConversations();
    };
    
    // Test API endpoint
    window.testConversationsAPI = async () => {
        try {
            const response = await fetch('/api/conversations/');
            const data = await response.json();
            console.log('API Response:', data);
            return data;
        } catch (error) {
            console.error('API Error:', error);
            return null;
        }
    };
});
