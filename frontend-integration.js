// This file contains the updated JavaScript for the frontend to connect with the Flask backend

// Configuration
const API_BASE_URL = 'http://localhost:5000';
const API_CHAT_ENDPOINT = '/api/chat';
const API_HEALTH_ENDPOINT = '/api/health';

// State management
let chatMessages = [];
let isFirstMessage = true;
let isWaitingForResponse = false;

// Initialize connection
document.addEventListener('DOMContentLoaded', function() {
    checkBackendHealth();
    setupEventListeners();
});

/**
 * Check if backend is running
 */
async function checkBackendHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}${API_HEALTH_ENDPOINT}`);
        const data = await response.json();
        console.log('Backend status:', data);
        if (data.status === 'healthy') {
            console.log('✓ Backend connected successfully');
            showNotification('Backend connected', 'success');
        }
    } catch (error) {
        console.error('Backend not available:', error);
        showNotification('Backend not available - Check if server is running', 'error');
    }
}

/**
 * Setup event listeners for chat interface
 */
function setupEventListeners() {
    const sendButton = document.querySelector('[data-send-button]');
    const inputField = document.querySelector('[data-input-field]');
    const newChatButton = document.querySelector('[data-new-chat-button]');

    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }

    if (inputField) {
        inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    if (newChatButton) {
        newChatButton.addEventListener('click', startNewChat);
    }
}

/**
 * Send message to backend and get response
 */
async function sendMessage() {
    const inputField = document.querySelector('[data-input-field]');
    const message = inputField.value.trim();

    if (!message) {
        showNotification('Please enter a message', 'warning');
        return;
    }

    if (isWaitingForResponse) {
        showNotification('Waiting for previous response...', 'info');
        return;
    }

    // Add user message to chat
    addMessageToChat('user', message);
    inputField.value = '';

    // Transition to chat mode if first message
    if (isFirstMessage) {
        transitionToChat();
        isFirstMessage = false;
    }

    // Show loading indicator
    isWaitingForResponse = true;
    showLoadingIndicator();

    try {
        const response = await fetch(`${API_BASE_URL}${API_CHAT_ENDPOINT}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Add bot response to chat
        addMessageToChat('bot', data.response);

        console.log('Backend response:', data);

    } catch (error) {
        console.error('Error sending message:', error);
        const errorMessage = 'Sorry, I encountered an error processing your query. Please make sure the backend server is running.';
        addMessageToChat('bot', errorMessage);
        showNotification('Error: ' + error.message, 'error');
    } finally {
        isWaitingForResponse = false;
        hideLoadingIndicator();
        scrollToBottom();
    }
}

/**
 * Add message to chat display
 */
function addMessageToChat(sender, text) {
    const chatContainer = document.querySelector('[data-chat-messages]');

    if (!chatContainer) {
        console.error('Chat container not found');
        return;
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.setAttribute('data-message-type', sender);

    const timestamp = new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
    });

    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = timestamp;

    const contentSpan = document.createElement('span');
    contentSpan.className = 'message-content';
    contentSpan.textContent = text;

    messageDiv.appendChild(contentSpan);
    messageDiv.appendChild(timeSpan);

    chatContainer.appendChild(messageDiv);

    chatMessages.push({
        sender: sender,
        text: text,
        timestamp: timestamp
    });
}

/**
 * Transition from centered input to bottom sticky input
 */
function transitionToChat() {
    const chatArea = document.querySelector('[data-chat-area]');
    if (chatArea) {
        chatArea.classList.add('chat-active');
    }
}

/**
 * Start a new chat
 */
function startNewChat() {
    chatMessages = [];
    isFirstMessage = true;

    const chatContainer = document.querySelector('[data-chat-messages]');
    if (chatContainer) {
        chatContainer.innerHTML = '';
    }

    const chatArea = document.querySelector('[data-chat-area]');
    if (chatArea) {
        chatArea.classList.remove('chat-active');
    }

    const inputField = document.querySelector('[data-input-field]');
    if (inputField) {
        inputField.value = '';
        inputField.focus();
    }

    console.log('Chat reset - ready for new conversation');
}

/**
 * Show loading indicator
 */
function showLoadingIndicator() {
    const chatContainer = document.querySelector('[data-chat-messages]');
    if (!chatContainer) return;

    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message bot-message loading';
    loadingDiv.setAttribute('data-loading', 'true');
    loadingDiv.innerHTML = '<span class="loading-dots">●●●</span>';

    chatContainer.appendChild(loadingDiv);
    scrollToBottom();
}

/**
 * Hide loading indicator
 */
function hideLoadingIndicator() {
    const loadingDiv = document.querySelector('[data-loading="true"]');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

/**
 * Scroll chat to bottom
 */
function scrollToBottom() {
    const chatContainer = document.querySelector('[data-chat-messages]');
    if (chatContainer) {
        setTimeout(() => {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 100);
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // You can enhance this to show visual notifications on the page
}