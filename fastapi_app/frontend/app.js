let currentUserId = null;
let currentSessionId = null;

const elements = {
    authSection: document.getElementById('auth-section'),
    usernameInput: document.getElementById('username'),
    loginBtn: document.getElementById('login-btn'),
    chatHistory: document.getElementById('chat-history'),
    chatInput: document.getElementById('chat-input'),
    sendBtn: document.getElementById('send-btn'),
    resumeDrop: document.getElementById('resume-drop'),
    userDisplay: document.getElementById('user-display'),
};

function generateUUID() {
    return '10000000-1000-4000-8000-100000000000'.replace(/[018]/g, c =>
      (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
}

// Auth Flow
elements.loginBtn.addEventListener('click', () => {
    const uname = elements.usernameInput.value.trim();
    if (!uname) return;
    
    currentUserId = `user_${uname.replace(/\s+/g, '').toLowerCase()}`;
    currentSessionId = generateUUID();
    
    elements.userDisplay.textContent = uname;
    elements.authSection.style.display = 'none';
    
    // Add initial system message requesting resume
    addMessageToChat('AI Tutor', 'Welcome back! Drop your resume or tell me what skills you have and what job you want.', 'bot');
});

// Chat Flow
async function handleSend() {
    const text = elements.chatInput.value.trim();
    if (!text) return;
    
    elements.chatInput.value = '';
    addMessageToChat('You', text, 'user');
    
    await streamResponse(text);
}

elements.sendBtn.addEventListener('click', handleSend);
elements.chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSend();
});

// Resume Drop (Mock read - simple text send for now)
elements.resumeDrop.addEventListener('click', () => {
    const fakeResume = "I have 1 year of Python experience and know basic HTML/CSS. I want to be a Full Stack Developer.";
    elements.chatInput.value = fakeResume;
    elements.chatInput.focus();
    elements.chatHistory.innerHTML += `<div style="text-align: center; color: var(--success); font-size: 12px; margin: 10px 0;">Resume uploaded to input field! Press enter to analyze.</div>`;
});

function addMessageToChat(author, text, type) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    msgDiv.innerHTML = `
        <div class="msg-avatar">${type === 'user' ? '👤' : '🤖'}</div>
        <div class="msg-bubble">
            <p><strong>${author}</strong></p>
            <div class="content">${marked.parse(text)}</div>
        </div>
    `;
    elements.chatHistory.appendChild(msgDiv);
    elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
    return msgDiv.querySelector('.content');
}

async function streamResponse(prompt) {
    // Add typing indicator
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message bot streaming';
    msgDiv.innerHTML = `
        <div class="msg-avatar">🤖</div>
        <div class="msg-bubble">
            <p><strong class="author-name">AI Tutor</strong></p>
            <div class="content">
                <div class="typing-indicator"><span></span><span></span><span></span></div>
            </div>
        </div>
    `;
    elements.chatHistory.appendChild(msgDiv);
    elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
    
    const contentBox = msgDiv.querySelector('.content');
    const authorSpan = msgDiv.querySelector('.author-name');
    
    try {
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: currentUserId,
                session_id: currentSessionId,
                prompt: prompt
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let fullText = "";
        
        contentBox.innerHTML = ''; // clear typing indicator

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunkArray = decoder.decode(value).split('\n\n');
            for(let chunkStr of chunkArray) {
                if (chunkStr.startsWith('data: ')) {
                    const dataStr = chunkStr.replace('data: ', '');
                    if (dataStr) {
                        try {
                            const data = JSON.parse(dataStr);
                            if (data.type === 'done') continue;
                            
                            if (data.author) {
                                // Dynamic agent name
                                authorSpan.textContent = data.author.replace('_', ' ').toUpperCase();
                            }
                            
                            fullText += data.content;
                            contentBox.innerHTML = marked.parse(fullText);
                            elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
                        } catch (e) {}
                    }
                }
            }
        }
    } catch (err) {
        contentBox.innerHTML = "<span style='color: var(--warning)'>Connection error. Please try again.</span>";
    }
}
