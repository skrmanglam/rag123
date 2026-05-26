// State management
const state = {
    currentBot: null,
    currentSession: 'default',
    sessions: {},
    messages: [],
    bots: [],
    documents: [],
    useFuzzyFaq: false
};

// API base URL
const API_BASE = '';

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
});

async function initializeApp() {
    await loadBots();
    showWelcomeScreen();
}

function setupEventListeners() {
    // Bot selection
    document.getElementById('botSelect').addEventListener('change', handleBotSelection);
    
    // Bot creation
    document.getElementById('createBotBtn').addEventListener('click', showBotCreationForm);
    document.getElementById('cancelBotBtn').addEventListener('click', () => {
        if (state.bots.length === 0) {
            showWelcomeScreen();
        } else {
            document.getElementById('botCreationForm').style.display = 'none';
            document.getElementById('botInterface').style.display = 'flex';
        }
    });
    document.getElementById('createBotFormElement').addEventListener('submit', handleBotCreation);
    
    // Chat
    document.getElementById('sendBtn').addEventListener('click', sendMessage);
    document.getElementById('chatInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    document.getElementById('fuzzyFaqToggle').addEventListener('change', (e) => {
        state.useFuzzyFaq = e.target.checked;
        updateFaqModeIndicator();
    });
    
    // Clear chat
    document.getElementById('clearChatBtn').addEventListener('click', clearChat);
    
    // Sessions
    document.getElementById('newSessionBtn').addEventListener('click', createNewSession);
    
    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Documents
    document.getElementById('uploadDocsBtn').addEventListener('click', uploadDocuments);
    
    // FAQ
    document.getElementById('uploadFaqBtn').addEventListener('click', uploadFaq);
    document.getElementById('testFaqBtn').addEventListener('click', testFaqSearch);
    document.getElementById('deleteFaqBtn').addEventListener('click', deleteFaq);
    
    // Config
    document.getElementById('refreshConfigBtn').addEventListener('click', refreshBotConfig);
    document.getElementById('updatePromptBtn').addEventListener('click', updateSystemPrompt);
    document.getElementById('deleteBotBtn').addEventListener('click', deleteBotWithConfirmation);
}

// Password hashing utility
async function hashPassword(password) {
    if (!password) return null;
    
    try {
        // Check if crypto.subtle is available
        if (!window.crypto || !window.crypto.subtle) {
            console.error('crypto.subtle not available - using fallback');
            // Fallback: simple hash (not secure, but works for demo)
            return simpleHash(password);
        }
        
        const encoder = new TextEncoder();
        const data = encoder.encode(password);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        return hashHex;
    } catch (error) {
        console.error('Error hashing password:', error);
        // Fallback to simple hash
        return simpleHash(password);
    }
}

// Simple hash fallback (for demo purposes only)
function simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32bit integer
    }
    return hash.toString(16);
}

// Bot Management
async function loadBots() {
    try {
        const response = await fetch(`${API_BASE}/bots`);
        state.bots = await response.json();
        
        const select = document.getElementById('botSelect');
        select.innerHTML = '<option value="">Create New Bot</option>';
        
        state.bots.forEach(bot => {
            const option = document.createElement('option');
            option.value = bot.bot_id;
            const lockIcon = bot.is_protected ? '🔒 ' : '';
            option.textContent = lockIcon + bot.bot_name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading bots:', error);
        showError('Failed to load bots');
    }
}

async function verifyBotPassword(botId) {
    // Always ask for password (no session storage)
    const password = prompt('🔒 This bot is password protected.\n\nPlease enter the password:');
    
    if (password === null) {
        return false; // User cancelled
    }
    
    const passwordHash = await hashPassword(password);
    
    try {
        const response = await fetch(`${API_BASE}/bots/${botId}/verify-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password_hash: passwordHash })
        });
        
        const result = await response.json();
        
        if (result.verified) {
            return true;
        } else {
            showError('❌ Incorrect password');
            return false;
        }
    } catch (error) {
        console.error('Error verifying password:', error);
        showError('Failed to verify password');
        return false;
    }
}

async function handleBotSelection(e) {
    const botId = e.target.value;
    
    if (!botId) {
        showBotCreationForm();
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/bots/${botId}`);
        const bot = await response.json();
        
        // Check if bot is protected
        if (bot.is_protected) {
            const verified = await verifyBotPassword(botId);
            if (!verified) {
                // Reset selection
                e.target.value = state.currentBot ? state.currentBot.bot_id : '';
                return;
            }
        }
        
        state.currentBot = bot;
        
        // Initialize session for this bot
        if (!state.sessions[botId]) {
            state.sessions[botId] = {
                default: {
                    name: 'New Chat',
                    messages: []
                }
            };
        }
        
        state.currentSession = 'default';
        state.messages = state.sessions[botId][state.currentSession].messages;
        
        showBotInterface();
        await loadDocuments();
        await loadFaqStats();
    } catch (error) {
        console.error('Error loading bot:', error);
        showError('Failed to load bot');
    }
}

async function handleBotCreation(e) {
    e.preventDefault();
    
    const password = document.getElementById('botPassword').value;
    const passwordHash = await hashPassword(password);
    
    const formData = {
        bot_name: document.getElementById('botName').value,
        role: document.getElementById('botRole').value,
        tone: document.getElementById('botTone').value,
        strictness: document.getElementById('botStrictness').value,
        citation_required: document.getElementById('botCitation').checked,
        fallback_behavior: document.getElementById('botFallback').value,
        behavior_instructions: document.getElementById('botInstructions').value || null,
        password_hash: passwordHash
    };
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/bots`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create bot');
        }
        
        const bot = await response.json();
        await loadBots();
        
        // Select the new bot
        document.getElementById('botSelect').value = bot.bot_id;
        state.currentBot = bot;
        
        // Initialize session
        state.sessions[bot.bot_id] = {
            default: {
                name: 'New Chat',
                messages: []
            }
        };
        state.currentSession = 'default';
        state.messages = [];
        
        showBotInterface();
        showSuccess('Bot created successfully!');
    } catch (error) {
        console.error('Error creating bot:', error);
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

// UI State Management
function showWelcomeScreen() {
    document.getElementById('welcomeScreen').style.display = 'flex';
    document.getElementById('botCreationForm').style.display = 'none';
    document.getElementById('botInterface').style.display = 'none';
}

function showBotCreationForm() {
    document.getElementById('welcomeScreen').style.display = 'none';
    document.getElementById('botCreationForm').style.display = 'block';
    document.getElementById('botInterface').style.display = 'none';
    
    // Reset form
    document.getElementById('createBotFormElement').reset();
}

function showBotInterface() {
    document.getElementById('welcomeScreen').style.display = 'none';
    document.getElementById('botCreationForm').style.display = 'none';
    document.getElementById('botInterface').style.display = 'flex';
    
    // Update bot title
    document.getElementById('botTitle').textContent = state.currentBot.bot_name;
    
    // Show chat sessions
    document.getElementById('chatSessions').style.display = 'block';
    updateSessionList();
    
    // Render messages
    renderMessages();
    updateChatMessageCount();
    updateFaqModeIndicator();
    
    // Load bot config
    loadBotConfig();
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}Tab`).classList.add('active');
    
    // Load tab-specific data
    if (tabName === 'documents') {
        loadDocuments();
    } else if (tabName === 'faq') {
        loadFaqStats();
    }
}

// Chat Functions
function updateChatMessageCount() {
    const count = state.messages.length;
    const countEl = document.getElementById('chatMessageCount');
    if (count > 0) {
        countEl.textContent = `💬 ${count} messages`;
    } else {
        countEl.textContent = '';
    }
}

function updateFaqModeIndicator() {
    const indicator = document.getElementById('faqModeIndicator');
    if (state.useFuzzyFaq) {
        indicator.textContent = '🔍 FAQ Mode: Fuzzy Search (no embeddings)';
    } else {
        indicator.textContent = '🔍 FAQ Mode: Vector Search (with embeddings)';
    }
}

function clearChat() {
    if (state.messages.length === 0) {
        return;
    }
    
    if (!confirm('Are you sure you want to clear the chat history?')) {
        return;
    }
    
    state.messages = [];
    state.sessions[state.currentBot.bot_id][state.currentSession].messages = [];
    state.sessions[state.currentBot.bot_id][state.currentSession].name = 'New Chat';
    
    renderMessages();
    updateSessionList();
    updateChatMessageCount();
    showSuccess('Chat cleared!');
}

function isGreeting(text) {
    const greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening'];
    const lowerText = text.toLowerCase().trim();
    return greetings.includes(lowerText) || greetings.some(g => lowerText.startsWith(g));
}

function generateGreetingResponse() {
    const bot = state.currentBot;
    const roleName = (bot.role || 'assistant').replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    const botName = bot.bot_name;
    
    return `Hello! I'm ${botName}, your ${roleName}. I can help you find information from the uploaded documents. Feel free to ask me any questions about the documents!`;
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const question = input.value.trim();
    
    if (!question) return;
    
    // Add user message
    const userMessage = { role: 'user', content: question };
    state.messages.push(userMessage);
    state.sessions[state.currentBot.bot_id][state.currentSession].messages = state.messages;
    
    // Update session name if it's the first message
    if (state.messages.length === 1) {
        state.sessions[state.currentBot.bot_id][state.currentSession].name =
            question.substring(0, 30) + (question.length > 30 ? '...' : '');
        updateSessionList();
    }
    
    input.value = '';
    renderMessages();
    updateChatMessageCount();
    
    // Check for greetings
    if (isGreeting(question)) {
        const greetingResponse = generateGreetingResponse();
        const assistantMessage = {
            role: 'assistant',
            content: greetingResponse,
            sources: []
        };
        state.messages.push(assistantMessage);
        state.sessions[state.currentBot.bot_id][state.currentSession].messages = state.messages;
        renderMessages();
        updateChatMessageCount();
        return;
    }
    
    // Show thinking indicator
    showThinkingIndicator();
    
    try {
        const response = await fetch(`${API_BASE}/chat/${state.currentBot.bot_id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                use_fuzzy_faq: state.useFuzzyFaq
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to get response');
        }
        
        const data = await response.json();
        
        // Add assistant message
        const assistantMessage = {
            role: 'assistant',
            content: data.answer,
            sources: data.sources
        };
        state.messages.push(assistantMessage);
        state.sessions[state.currentBot.bot_id][state.currentSession].messages = state.messages;
        
        removeThinkingIndicator();
        renderMessages();
        updateChatMessageCount();
    } catch (error) {
        console.error('Error sending message:', error);
        removeThinkingIndicator();
        showError('Failed to get response');
        state.messages.pop(); // Remove user message on error
        renderMessages();
        updateChatMessageCount();
    }
}

function showThinkingIndicator() {
    const container = document.getElementById('chatMessages');
    const thinkingDiv = document.createElement('div');
    thinkingDiv.id = 'thinkingIndicator';
    thinkingDiv.className = 'message thinking-indicator';
    thinkingDiv.innerHTML = `
        <div class="message-header">
            <span class="message-role assistant">🤖 Assistant</span>
        </div>
        <div class="message-content thinking">
            <span class="thinking-dots">
                <span>.</span><span>.</span><span>.</span>
            </span>
            <span class="thinking-text">Thinking...</span>
        </div>
    `;
    container.appendChild(thinkingDiv);
    container.scrollTop = container.scrollHeight;
}

function removeThinkingIndicator() {
    const indicator = document.getElementById('thinkingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

function renderMessages() {
    const container = document.getElementById('chatMessages');
    container.innerHTML = '';
    
    if (state.messages.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No messages yet. Start a conversation!</p>';
        return;
    }
    
    state.messages.forEach(message => {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        
        const header = document.createElement('div');
        header.className = 'message-header';
        
        const role = document.createElement('span');
        role.className = `message-role ${message.role}`;
        role.textContent = message.role === 'user' ? '👤 You' : '🤖 Assistant';
        header.appendChild(role);
        
        const content = document.createElement('div');
        content.className = 'message-content';
        content.textContent = message.content;
        
        messageDiv.appendChild(header);
        messageDiv.appendChild(content);
        
        // Add sources if present
        if (message.sources && message.sources.length > 0) {
            const sources = document.createElement('details');
            sources.className = 'message-sources';
            
            const summary = document.createElement('summary');
            summary.textContent = `📚 Sources (${message.sources.length})`;
            sources.appendChild(summary);
            
            message.sources.forEach(source => {
                const sourceItem = document.createElement('div');
                sourceItem.className = 'source-item';
                sourceItem.innerHTML = `
                    <strong>${source.file_name}</strong>
                    ${source.page ? `<br>Page: ${source.page}` : ''}
                `;
                sources.appendChild(sourceItem);
            });
            
            messageDiv.appendChild(sources);
        }
        
        container.appendChild(messageDiv);
    });
    
    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

// Session Management
function createNewSession() {
    const sessionId = `session_${Date.now()}`;
    state.sessions[state.currentBot.bot_id][sessionId] = {
        name: 'New Chat',
        messages: []
    };
    state.currentSession = sessionId;
    state.messages = [];
    
    updateSessionList();
    renderMessages();
    updateChatMessageCount();
}

function switchSession(sessionId) {
    state.currentSession = sessionId;
    state.messages = state.sessions[state.currentBot.bot_id][sessionId].messages;
    renderMessages();
    updateSessionList();
    updateChatMessageCount();
}

function deleteSession(sessionId) {
    if (Object.keys(state.sessions[state.currentBot.bot_id]).length === 1) {
        showError('Cannot delete the last session');
        return;
    }
    
    delete state.sessions[state.currentBot.bot_id][sessionId];
    
    if (state.currentSession === sessionId) {
        const firstSession = Object.keys(state.sessions[state.currentBot.bot_id])[0];
        switchSession(firstSession);
    } else {
        updateSessionList();
    }
}

function updateSessionList() {
    const container = document.getElementById('sessionList');
    container.innerHTML = '';
    
    const sessions = state.sessions[state.currentBot.bot_id];
    Object.entries(sessions).forEach(([sessionId, session]) => {
        const item = document.createElement('div');
        item.className = `session-item ${sessionId === state.currentSession ? 'active' : ''}`;
        
        const name = document.createElement('span');
        name.className = 'session-name';
        name.textContent = session.name;
        name.onclick = () => switchSession(sessionId);
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-session';
        deleteBtn.textContent = '🗑️';
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            deleteSession(sessionId);
        };
        
        item.appendChild(name);
        item.appendChild(deleteBtn);
        container.appendChild(item);
    });
}

// Document Management
async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE}/bots/${state.currentBot.bot_id}/documents`);
        state.documents = await response.json();
        renderDocuments();
    } catch (error) {
        console.error('Error loading documents:', error);
    }
}

function renderDocuments() {
    const container = document.getElementById('documentsList');
    
    if (state.documents.length === 0) {
        container.innerHTML = '<p class="text-muted">No documents uploaded yet.</p>';
        return;
    }
    
    container.innerHTML = '';
    state.documents.forEach(doc => {
        const item = document.createElement('div');
        item.className = 'document-item';
        item.innerHTML = `
            <div class="document-info">
                <div class="document-name">📄 ${doc.file_name}</div>
                <div class="document-meta">${new Date(doc.created_at).toLocaleString()}</div>
            </div>
            <span class="document-status ${doc.status}">${doc.status}</span>
        `;
        container.appendChild(item);
    });
}

async function uploadDocuments() {
    const input = document.getElementById('documentUpload');
    const files = input.files;
    
    if (files.length === 0) {
        showError('Please select files to upload');
        return;
    }
    
    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }
    
    try {
        showLoadingWithMessage(`Processing ${files.length} file(s)...`);
        const response = await fetch(`${API_BASE}/bots/${state.currentBot.bot_id}/documents`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Failed to upload documents');
        }
        
        const result = await response.json();
        
        // Show detailed results
        displayDocumentProcessingResults(result.results);
        
        input.value = '';
        await loadDocuments();
    } catch (error) {
        console.error('Error uploading documents:', error);
        showError('Failed to upload documents');
    } finally {
        showLoading(false);
    }
}

function displayDocumentProcessingResults(results) {
    const successCount = results.filter(r => r.status === 'success').length;
    const errorCount = results.filter(r => r.status === 'error').length;
    
    let message = '📄 Document Processing Results:\n\n';
    
    results.forEach(result => {
        if (result.status === 'success') {
            message += `✅ ${result.file_name} - Success (${result.chunks || 0} chunks)\n`;
        } else {
            message += `❌ ${result.file_name} - Error: ${result.message || 'Unknown error'}\n`;
        }
    });
    
    message += `\n📊 Summary: ${successCount} succeeded, ${errorCount} failed`;
    
    alert(message);
}

// FAQ Management
async function loadFaqStats() {
    try {
        const response = await fetch(`${API_BASE}/bots/${state.currentBot.bot_id}/faq/stats`);
        const stats = await response.json();
        
        if (stats.total_faqs > 0) {
            document.getElementById('faqStats').style.display = 'block';
            document.getElementById('faqStatsContent').innerHTML = `
                <p><strong>Total FAQs:</strong> ${stats.total_faqs}</p>
                <p><strong>Similarity Threshold:</strong> ${stats.similarity_threshold}</p>
                ${stats.categories ? `<p><strong>Categories:</strong> ${Object.keys(stats.categories).join(', ')}</p>` : ''}
            `;
        } else {
            document.getElementById('faqStats').style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading FAQ stats:', error);
    }
}

async function uploadFaq() {
    const input = document.getElementById('faqUpload');
    const file = input.files[0];
    
    if (!file) {
        showError('Please select a CSV file');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/bots/${state.currentBot.bot_id}/faq/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to upload FAQ');
        }
        
        const result = await response.json();
        
        // Display validation results
        displayFaqValidation(result);
        
        showSuccess(`FAQ uploaded! ${result.stats.added} entries added.`);
        
        input.value = '';
        await loadFaqStats();
    } catch (error) {
        console.error('Error uploading FAQ:', error);
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

function displayFaqValidation(result) {
    const container = document.getElementById('faqValidation');
    const validation = result.validation;
    
    if (!validation) return;
    
    container.style.display = 'block';
    
    let html = '';
    let className = 'success';
    
    if (!validation.valid) {
        className = 'error';
        html += '<h4>❌ Validation Failed</h4>';
        html += '<ul>';
        if (validation.duplicates && validation.duplicates.length > 0) {
            validation.duplicates.forEach(dup => {
                html += `<li>${dup}</li>`;
            });
        }
        html += '</ul>';
    } else if (validation.warnings && validation.warnings.length > 0) {
        className = 'warning';
        html += '<h4>⚠️ Warnings</h4>';
        html += '<ul>';
        validation.warnings.forEach(warning => {
            html += `<li>${warning}</li>`;
        });
        html += '</ul>';
    } else {
        html += '<h4>✅ Validation Successful</h4>';
        html += `<p>Total entries: ${validation.total_entries}, Unique IDs: ${validation.unique_question_ids}</p>`;
    }
    
    container.className = `faq-validation ${className}`;
    container.innerHTML = html;
}

async function testFaqSearch() {
    const query = document.getElementById('faqTestQuery').value.trim();
    const searchMethod = document.getElementById('faqSearchMethod').value;
    const topK = parseInt(document.getElementById('faqTopK').value) || 3;
    
    if (!query) {
        showError('Please enter a question');
        return;
    }
    
    try {
        const useFuzzy = searchMethod === 'fuzzy';
        const response = await fetch(`${API_BASE}/bots/${state.currentBot.bot_id}/faq/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: query,
                top_k: topK,
                use_fuzzy_faq: useFuzzy
            })
        });
        
        const result = await response.json();
        const container = document.getElementById('faqTestResults');
        
        if (result.matches === 0) {
            container.innerHTML = `<p class="text-muted">No matching FAQs found using ${searchMethod} search.</p>`;
            return;
        }
        
        container.innerHTML = `<p class="text-muted">Found ${result.matches} match(es) using ${searchMethod} search</p>`;
        result.results.forEach(faq => {
            const item = document.createElement('div');
            item.className = 'faq-result';
            const scoreLabel = searchMethod === 'vector' ? 'Similarity Score' : 'Match Score';
            item.innerHTML = `
                <div class="faq-result-score">${scoreLabel}: ${(faq.score * 100).toFixed(1)}%</div>
                <div class="faq-result-question"><strong>Q:</strong> ${faq.question}</div>
                <div class="faq-result-answer"><strong>A:</strong> ${faq.answer}</div>
                ${faq.category ? `<div class="faq-result-category"><strong>Category:</strong> ${faq.category}</div>` : ''}
            `;
            container.appendChild(item);
        });
    } catch (error) {
        console.error('Error testing FAQ:', error);
        showError('Failed to search FAQs');
    }
}

async function deleteFaq() {
    if (!confirm('Are you sure you want to delete all FAQ entries?')) {
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/bots/${state.currentBot.bot_id}/faq`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete FAQs');
        }
        
        showSuccess('All FAQ entries deleted');
        await loadFaqStats();
        document.getElementById('faqTestResults').innerHTML = '';
    } catch (error) {
        console.error('Error deleting FAQs:', error);
        showError('Failed to delete FAQs');
    } finally {
        showLoading(false);
    }
}

// Bot Configuration
function loadBotConfig() {
    const container = document.getElementById('botConfigDetails');
    const bot = state.currentBot;
    
    container.innerHTML = `
        <div class="config-item">
            <div class="config-label">Bot ID</div>
            <div class="config-value">${bot.bot_id}</div>
        </div>
        <div class="config-item">
            <div class="config-label">Bot Name</div>
            <div class="config-value">${bot.bot_name}</div>
        </div>
        <div class="config-item">
            <div class="config-label">Role</div>
            <div class="config-value">${bot.role || 'N/A'}</div>
        </div>
        <div class="config-item">
            <div class="config-label">Tone</div>
            <div class="config-value">${bot.tone || 'N/A'}</div>
        </div>
        <div class="config-item">
            <div class="config-label">Strictness</div>
            <div class="config-value">${bot.strictness || 'N/A'}</div>
        </div>
        <div class="config-item">
            <div class="config-label">Citation Required</div>
            <div class="config-value">${bot.citation_required ? 'Yes' : 'No'}</div>
        </div>
        <div class="config-item">
            <div class="config-label">Created At</div>
            <div class="config-value">${new Date(bot.created_at).toLocaleString()}</div>
        </div>
    `;
    
    // Load system prompt
    loadSystemPrompt();
    
    // Load API documentation
    loadApiDocumentation();
}

async function loadSystemPrompt() {
    try {
        const response = await fetch(`${API_BASE}/bots/${state.currentBot.bot_id}/system-prompt`);
        const data = await response.json();
        document.getElementById('systemPromptEditor').value = data.system_prompt || '';
    } catch (error) {
        console.error('Error loading system prompt:', error);
    }
}

function loadApiDocumentation() {
    const botId = state.currentBot.bot_id;
    const endpoint = `POST ${window.location.origin}/chat/${botId}`;
    document.getElementById('apiEndpoint').textContent = endpoint;
    
    const example = `curl -X POST ${window.location.origin}/chat/${botId} \\
  -H "Content-Type: application/json" \\
  -d '{"question": "What is the leave policy?"}'`;
    document.getElementById('apiExample').textContent = example;
}

async function refreshBotConfig() {
    try {
        const response = await fetch(`${API_BASE}/bots/${state.currentBot.bot_id}`);
        state.currentBot = await response.json();
        loadBotConfig();
        showSuccess('Configuration refreshed!');
    } catch (error) {
        console.error('Error refreshing config:', error);
        showError('Failed to refresh configuration');
    }
}

async function updateSystemPrompt() {
    const newPrompt = document.getElementById('systemPromptEditor').value.trim();
    
    if (!newPrompt) {
        showError('System prompt cannot be empty!');
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/bots/${state.currentBot.bot_id}/system-prompt`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ system_prompt: newPrompt })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update system prompt');
        }
        
        showSuccess('✅ System prompt updated! Changes will apply to new conversations immediately.');
    } catch (error) {
        console.error('Error updating system prompt:', error);
        showError('Failed to update system prompt');
    } finally {
        showLoading(false);
    }
}

// Utility Functions
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = show ? 'flex' : 'none';
    if (!show) {
        // Reset message when hiding
        overlay.querySelector('p').textContent = 'Processing...';
    }
}

function showLoadingWithMessage(message) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = 'flex';
    overlay.querySelector('p').textContent = message;
}

function showSuccess(message) {
    // Simple alert for now - could be replaced with a toast notification
    alert('✅ ' + message);
}

function showError(message) {
    // Simple alert for now - could be replaced with a toast notification
    alert('❌ ' + message);
}

async function deleteBotWithConfirmation() {
    const botName = state.currentBot.bot_name;
    const botId = state.currentBot.bot_id;
    
    const confirmed = confirm(
        `⚠️ WARNING: This will permanently delete "${botName}" and ALL associated data:\n\n` +
        `• All uploaded documents\n` +
        `• All FAQ entries\n` +
        `• All chat history\n` +
        `• All configuration\n\n` +
        `This action CANNOT be undone!\n\n` +
        `Click OK to continue, or Cancel to abort.`
    );
    
    if (!confirmed) return;
    
    const userInput = prompt(`Please type "${botName}" to confirm deletion:`);
    
    if (userInput !== botName) {
        showError('Bot name does not match. Deletion cancelled.');
        return;
    }
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE}/bots/${botId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete bot');
        }
        
        showSuccess(`Bot "${botName}" deleted successfully!`);
        
        // Reset state
        state.currentBot = null;
        state.currentSession = 'default';
        state.messages = [];
        delete state.sessions[botId];
        
        // Reload bots and show welcome screen
        await loadBots();
        
        if (state.bots.length === 0) {
            showWelcomeScreen();
        } else {
            // Select first available bot
            document.getElementById('botSelect').value = state.bots[0].bot_id;
            await handleBotSelection({ target: { value: state.bots[0].bot_id } });
        }
    } catch (error) {
        console.error('Error deleting bot:', error);
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

