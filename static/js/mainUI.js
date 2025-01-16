const chatBox = document.getElementById('chat-box');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const sidebarToggle = document.getElementById('sidebar-toggle');
const modeToggle = document.getElementById('mode-toggle-checkbox');
const sidebar = document.querySelector('.sidebar');
const chatarea = document.getElementById('multi-chat');
const chatareaButton = document.getElementById('chatarea-button');
const closemulti = document.getElementById('close-multi-chat');
const chatbox = document.getElementById('chat-box');
const inputContainer = document.getElementById('input-container-box')

chatareaButton.addEventListener('click', function() {
    chatarea.style.display = "block";
    chatBox.classList.add("shift-right");
    inputContainer.classList.add("shift-right");
}, false);

closemulti.addEventListener('click', function() {
    chatarea.style.display = "none";
    chatBox.classList.remove("shift-right");
    inputContainer.classList.remove("shift-right");
}, false)

modeToggle.addEventListener('change', () => {
    document.body.classList.toggle('dark-mode');
});

sendButton.addEventListener('click', sendMessage);

userInput.addEventListener('input', function() {
    // Reset height to default
    this.style.height = 'auto';

    // Set height to scroll height
    this.style.height = `${Math.min(this.scrollHeight, 150)}px`;
}, false);

userInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        if (event.shiftKey) {
            // Allow Shift + Enter to add a newline
            return;
        } else {
            // Prevent default "Enter" behavior and send message
            event.preventDefault();
            sendMessage();
        }
    }
});

document.getElementById('mode-toggle-checkbox').addEventListener('change', function () {
    document.body.classList.toggle('dark-mode', this.checked);
});

document.addEventListener('DOMContentLoaded', function () {
    loadInitialMessage();
    const newConversationBtn = document.getElementById('new-conversation-btn');
    const conversationContent = document.querySelector('.conversation-content');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const chatContainer = document.querySelector('.chat-container');

    sidebarToggle.addEventListener('click', function () {
        const sidebar = document.querySelector('.sidebar');
        sidebar.classList.toggle('collapsed');

        if (sidebar.classList.contains('collapsed')) {
            chatContainer.style.width = '96%';
            chatContainer.style.marginLeft = '3%';
        } else {
            chatContainer.style.width = 'calc(100% - 300px)';
            chatContainer.style.marginLeft = '300px';
        }
    });

    newConversationBtn.addEventListener('click', function () {
        conversationContent.textContent = "New Conversation Started!";
    });
});

function sendMessage() {
    const message = userInput.value.trim();
    if (message !== '') {
        const userAvatarElement = document.getElementById('avatar');
        const userAvatarUrl = "static/icon/messi.jpg"; // Fallback to default
        appendMessage('Messi', message, userAvatarUrl);
        getResponse(message);
        userInput.value = '';
        userInput.style.height = 'auto';
    }
}

function loadInitialMessage() {
    fetch('/get-initial-message')
        .then(response => response.json())
        .then(data => {
            const doctorAvatarUrl = "static/icon/doctor.png";
            appendMessage('DoctorQA', data.response, doctorAvatarUrl);
        })
        .catch(error => console.error('Error fetching initial message:', error));
}

function appendMessage(sender, message, imageUrl) {
    // Create a more semantic message container
    const messageContainer = document.createElement('div');
    messageContainer.classList.add('message-container');
    messageContainer.setAttribute('aria-label', `Message from ${sender}`);

    // Check if dark mode is active and apply specific styling for Messi
    if (document.body.classList.contains('dark-mode') && sender === 'Messi') {
        messageContainer.classList.add('dark-messi-message');
    }

    // Create a wrapper for avatar and name
    const avatarWrapper = document.createElement('div');
    avatarWrapper.classList.add('message-avatar-wrapper');

    // Create the image element with improved attributes
    const img = document.createElement('img');
    img.src = imageUrl;
    img.alt = `${sender}'s avatar`;
    img.classList.add('message-avatar');
    img.setAttribute('loading', 'lazy');

    // Create the sender name element
    const nameElement = document.createElement('span');
    nameElement.textContent = sender;
    nameElement.classList.add('message-sender');
    nameElement.setAttribute('aria-label', `Sender: ${sender}`);

    // Add avatar and name to the wrapper
    avatarWrapper.appendChild(img);
    avatarWrapper.appendChild(nameElement);

    // Create the message content element
    const messageContent = document.createElement('div');
    messageContent.innerHTML = marked.parse(message);
    messageContent.classList.add('message-content');
    messageContent.setAttribute('role', 'article');

    // Append avatar wrapper and message content to the message container
    messageContainer.appendChild(avatarWrapper);
    messageContainer.appendChild(messageContent);

    // Append the message container to the chatBox
    chatBox.appendChild(messageContainer);

    // Scroll to the bottom
    chatBox.scrollTop = chatBox.scrollHeight;
}


function getResponse(message) {
    const botAvatarUrl = "static/icon/doctor.png"; // Add chatbot avatar image path
    fetch('/get-response', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: message})
    })
    .then(response => response.json())
    .then(data => {
        const botResponse = data.response;
        setTimeout(() => appendMessage('DoctorQA', botResponse, botAvatarUrl), 1000);
    })
    .catch(error => {
        console.error("Error fetching response:", error);
        appendMessage('DoctorQA', "Sorry, something went wrong.", botAvatarUrl);
    });
}