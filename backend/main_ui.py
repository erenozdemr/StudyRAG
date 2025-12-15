"""
ChatGPT-Style UI for StudyRAG
"""

from backend.main import app
from fastapi.responses import HTMLResponse


@app.get("/ui", response_class=HTMLResponse)
async def ui_page() -> HTMLResponse:
    html = '''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>StudyRAG Chat</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0d0d0d; color: #ececec; height: 100vh; display: flex; }
        
        /* Sidebar */
        .sidebar { width: 260px; background: #171717; display: flex; flex-direction: column; border-right: 1px solid #2d2d2d; }
        .sidebar-header { padding: 12px; border-bottom: 1px solid #2d2d2d; }
        .new-chat-btn { width: 100%; padding: 12px 16px; background: transparent; border: 1px solid #4d4d4d; border-radius: 8px; color: #fff; cursor: pointer; display: flex; align-items: center; gap: 10px; font-size: 14px; transition: all 0.2s; }
        .new-chat-btn:hover { background: #2d2d2d; }
        
        .chat-history { flex: 1; overflow-y: auto; padding: 8px; }
        .chat-history h4 { font-size: 11px; color: #8e8e8e; padding: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        .history-item { padding: 10px 12px; border-radius: 8px; cursor: pointer; font-size: 13px; color: #ececec; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: background 0.2s; display: flex; align-items: center; gap: 8px; }
        .history-item:hover { background: #2d2d2d; }
        .history-item.active { background: #2d2d2d; }
        .history-item span { font-size: 14px; }
        .no-history { padding: 12px; font-size: 12px; color: #6e6e6e; text-align: center; }
        
        .quick-actions { padding: 12px; border-top: 1px solid #2d2d2d; }
        .action-btn { width: 100%; padding: 10px 12px; background: transparent; border: none; border-radius: 8px; color: #ececec; cursor: pointer; display: flex; align-items: center; gap: 10px; font-size: 13px; text-align: left; transition: background 0.2s; margin-bottom: 4px; }
        .action-btn:hover { background: #2d2d2d; }
        
        /* Main Chat */
        .main { flex: 1; display: flex; flex-direction: column; }
        .chat-header { padding: 14px 20px; border-bottom: 1px solid #2d2d2d; display: flex; align-items: center; justify-content: space-between; }
        .chat-header h1 { font-size: 16px; font-weight: 600; }
        .header-right { display: flex; align-items: center; gap: 12px; }
        .pdf-badge { padding: 4px 10px; background: #1e3a2f; border-radius: 6px; font-size: 12px; color: #10a37f; display: none; }
        .pdf-badge.show { display: block; }
        .model-badge { padding: 4px 10px; background: #2d2d2d; border-radius: 6px; font-size: 12px; color: #8e8e8e; }
        
        .chat-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 20px; }
        
        .message { max-width: 720px; width: 100%; margin: 0 auto; display: flex; gap: 16px; animation: fadeIn 0.3s ease; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        .message.user { flex-direction: row-reverse; }
        .message-avatar { width: 36px; height: 36px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
        .message.assistant .message-avatar { background: #10a37f; }
        .message.user .message-avatar { background: #5436da; }
        
        .message-content { flex: 1; }
        .message.user .message-content { text-align: right; }
        .message-bubble { display: inline-block; padding: 14px 18px; border-radius: 16px; font-size: 15px; line-height: 1.6; max-width: 100%; text-align: left; }
        .message.assistant .message-bubble { background: #2d2d2d; border-bottom-left-radius: 4px; }
        .message.user .message-bubble { background: #2e2b5f; border-bottom-right-radius: 4px; }
        
        .message-actions { margin-top: 8px; display: flex; gap: 8px; }
        .message.user .message-actions { justify-content: flex-end; }
        .action-icon-btn { background: transparent; border: none; color: #8e8e8e; cursor: pointer; padding: 4px 8px; border-radius: 4px; font-size: 12px; display: flex; align-items: center; gap: 4px; transition: all 0.2s; }
        .action-icon-btn:hover { background: #3d3d3d; color: #fff; }
        
        .typing-indicator { display: flex; gap: 4px; padding: 14px 18px; }
        .typing-dot { width: 8px; height: 8px; background: #8e8e8e; border-radius: 50%; animation: typing 1.4s infinite; }
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing { 0%, 60%, 100% { transform: translateY(0); } 30% { transform: translateY(-8px); } }
        
        /* Input Area */
        .input-area { padding: 20px; border-top: 1px solid #2d2d2d; }
        .input-container { max-width: 720px; margin: 0 auto; position: relative; display: flex; align-items: flex-end; gap: 8px; background: #2d2d2d; border: 1px solid #4d4d4d; border-radius: 16px; padding: 8px 12px; }
        .input-container:focus-within { border-color: #10a37f; }
        .attach-btn { width: 36px; height: 36px; background: transparent; border: none; border-radius: 8px; color: #8e8e8e; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 18px; transition: all 0.2s; flex-shrink: 0; }
        .attach-btn:hover { background: #3d3d3d; color: #fff; }
        .chat-input { flex: 1; padding: 8px 0; background: transparent; border: none; color: #fff; font-size: 15px; resize: none; min-height: 24px; max-height: 200px; outline: none; }
        .chat-input::placeholder { color: #8e8e8e; }
        .send-btn { width: 36px; height: 36px; background: #10a37f; border: none; border-radius: 8px; color: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: opacity 0.2s; flex-shrink: 0; }
        .send-btn:disabled { opacity: 0.4; cursor: default; }
        .send-btn:hover:not(:disabled) { background: #0d8a6a; }
        
        /* Modal */
        .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: none; align-items: center; justify-content: center; z-index: 100; }
        .modal-overlay.show { display: flex; }
        .modal { background: #1e1e1e; border-radius: 16px; padding: 24px; width: 90%; max-width: 480px; border: 1px solid #3d3d3d; }
        .modal h3 { margin-bottom: 20px; font-size: 18px; }
        .modal-row { margin-bottom: 16px; }
        .modal-row label { display: block; font-size: 13px; color: #8e8e8e; margin-bottom: 6px; }
        .modal-row select, .modal-row input { width: 100%; padding: 10px 14px; background: #2d2d2d; border: 1px solid #4d4d4d; border-radius: 8px; color: #fff; font-size: 14px; }
        .modal-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }
        .modal-btn { padding: 10px 20px; border-radius: 8px; font-size: 14px; cursor: pointer; border: none; }
        .modal-btn.primary { background: #10a37f; color: #fff; }
        .modal-btn.secondary { background: #3d3d3d; color: #fff; }
        
        /* Welcome */
        .welcome { text-align: center; padding: 60px 20px; }
        .welcome h2 { font-size: 28px; margin-bottom: 12px; background: linear-gradient(135deg, #10a37f, #5436da); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .welcome p { color: #8e8e8e; font-size: 15px; }
        
        #fileInput { display: none; }
        
        @media (max-width: 768px) { .sidebar { display: none; } }
    </style>
</head>
<body>
    <aside class="sidebar">
        <div class="sidebar-header">
            <button class="new-chat-btn" onclick="newChat()">
                <span>➕</span> Yeni Sohbet
            </button>
        </div>
        <div class="chat-history" id="chatHistory">
            <h4>Sohbet Geçmişi</h4>
            <div class="no-history" id="noHistory">Henüz sohbet yok</div>
        </div>
        <div class="quick-actions">
            <button class="action-btn" onclick="openQuizModal()"><span>📝</span> Quiz Oluştur</button>
            <button class="action-btn" onclick="openPlanModal()"><span>📅</span> Çalışma Planı</button>
        </div>
    </aside>
    
    <main class="main">
        <header class="chat-header">
            <h1>StudyRAG</h1>
            <div class="header-right">
                <span class="pdf-badge" id="pdfBadge">📄 PDF yüklendi</span>
                <span class="model-badge">Gemini Pro</span>
            </div>
        </header>
        
        <div class="chat-container" id="chatContainer">
            <div class="welcome">
                <h2>StudyRAG'e Hoş Geldin! 👋</h2>
                <p>📎 butonuyla PDF yükle ve soru sormaya başla</p>
            </div>
        </div>
        
        <div class="input-area">
            <div class="input-container">
                <button class="attach-btn" onclick="document.getElementById('fileInput').click()" title="PDF Yükle">📎</button>
                <input type="file" id="fileInput" accept=".pdf"/>
                <textarea class="chat-input" id="chatInput" placeholder="Bir soru sor..." rows="1" onkeydown="handleKeyDown(event)"></textarea>
                <button class="send-btn" id="sendBtn" onclick="sendMessage()">➤</button>
            </div>
        </div>
    </main>
    
    <!-- Quiz Modal -->
    <div class="modal-overlay" id="quizModal">
        <div class="modal">
            <h3>📝 Quiz Oluştur</h3>
            <div class="modal-row"><label>Quiz Türü</label><select id="quizType"><option value="multiple_choice">Çoktan Seçmeli</option><option value="true_false">Doğru-Yanlış</option><option value="open_ended">Açık Uçlu</option><option value="mixed">Karışık</option></select></div>
            <div class="modal-row"><label>Soru Sayısı</label><input type="number" id="quizNum" value="5" min="1" max="20"/></div>
            <div class="modal-row"><label>Zorluk</label><select id="quizDiff"><option value="easy">Kolay</option><option value="medium" selected>Orta</option><option value="hard">Zor</option></select></div>
            <div class="modal-row"><label>Konu (opsiyonel)</label><input type="text" id="quizTopic" placeholder="örn: türev"/></div>
            <div class="modal-actions"><button class="modal-btn secondary" onclick="closeModals()">İptal</button><button class="modal-btn primary" onclick="generateQuiz()">Oluştur</button></div>
        </div>
    </div>
    
    <!-- Plan Modal -->
    <div class="modal-overlay" id="planModal">
        <div class="modal">
            <h3>📅 Çalışma Planı</h3>
            <div class="modal-row"><label>Gün Sayısı</label><input type="number" id="planDays" value="7" min="1" max="30"/></div>
            <div class="modal-row"><label>Günlük Dakika</label><input type="number" id="planMinutes" value="120" min="30" max="600"/></div>
            <div class="modal-row"><label>Odak Konu (opsiyonel)</label><input type="text" id="planFocus" placeholder="örn: integral"/></div>
            <div class="modal-actions"><button class="modal-btn secondary" onclick="closeModals()">İptal</button><button class="modal-btn primary" onclick="generatePlan()">Oluştur</button></div>
        </div>
    </div>

<script>
const { jsPDF } = window.jspdf;
let messages = [];
let chats = JSON.parse(localStorage.getItem('studyrag_chats') || '[]');
let currentChatId = null;

renderHistory();

const fileInput = document.getElementById('fileInput');
fileInput.addEventListener('change', e => { if(e.target.files[0]) uploadPDF(e.target.files[0]); });

async function uploadPDF(file) {
    if(!file.name.endsWith('.pdf')) { alert('Sadece PDF yükleyebilirsin'); return; }
    addMessage('user', `📄 ${file.name} yükleniyor...`);
    
    const fd = new FormData();
    fd.append('file', file);
    fd.append('vectorstore_name', 'default');
    
    try {
        const res = await fetch('/upload', { method: 'POST', body: fd });
        const data = await res.json();
        if(!res.ok) throw new Error(data.detail);
        document.getElementById('pdfBadge').textContent = `📄 ${file.name}`;
        document.getElementById('pdfBadge').classList.add('show');
        addMessage('assistant', `✅ **${file.name}** başarıyla yüklendi!\\n\\n${data.num_chunks} parçaya bölündü. Artık sorularını sorabilirsin.`);
        saveChat();
    } catch(e) {
        addMessage('assistant', '❌ Hata: ' + e.message);
    }
}

function newChat() {
    if(messages.length > 0) saveChat();
    messages = [];
    currentChatId = Date.now().toString();
    document.getElementById('chatContainer').innerHTML = `<div class="welcome"><h2>StudyRAG'e Hoş Geldin! 👋</h2><p>📎 butonuyla PDF yükle ve soru sormaya başla</p></div>`;
    renderHistory();
}

function saveChat() {
    if(messages.length === 0) return;
    const title = messages[0].content.substring(0, 30) + (messages[0].content.length > 30 ? '...' : '');
    const existing = chats.findIndex(c => c.id === currentChatId);
    const chatData = { id: currentChatId || Date.now().toString(), title, messages, timestamp: Date.now() };
    if(existing >= 0) chats[existing] = chatData;
    else chats.unshift(chatData);
    chats = chats.slice(0, 20);
    localStorage.setItem('studyrag_chats', JSON.stringify(chats));
    currentChatId = chatData.id;
    renderHistory();
}

function loadChat(id) {
    const chat = chats.find(c => c.id === id);
    if(!chat) return;
    if(messages.length > 0 && currentChatId !== id) saveChat();
    currentChatId = id;
    messages = chat.messages;
    const container = document.getElementById('chatContainer');
    container.innerHTML = '';
    messages.forEach((m, i) => renderMessage(m.role, m.content, i));
    renderHistory();
}

function renderHistory() {
    const container = document.getElementById('chatHistory');
    const noHistory = document.getElementById('noHistory');
    container.querySelectorAll('.history-item').forEach(el => el.remove());
    if(chats.length === 0) { noHistory.style.display = 'block'; return; }
    noHistory.style.display = 'none';
    chats.forEach(chat => {
        const div = document.createElement('div');
        div.className = `history-item ${chat.id === currentChatId ? 'active' : ''}`;
        div.innerHTML = `<span>💬</span> ${chat.title}`;
        div.onclick = () => loadChat(chat.id);
        container.appendChild(div);
    });
}

function handleKeyDown(e) { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if(!text) return;
    input.value = '';
    input.style.height = 'auto';
    addMessage('user', text);
    showTyping();
    
    try {
        const res = await fetch('/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: text, k: 4, include_sources: true }) });
        const data = await res.json();
        hideTyping();
        if(!res.ok) throw new Error(data.detail);
        let answer = data.answer;
        if(data.sources?.length) answer += '\\n\\n📚 **Kaynaklar:** ' + data.sources.map(s => `Sayfa ${s.page || '?'}`).join(', ');
        addMessage('assistant', answer);
        saveChat();
    } catch(e) { hideTyping(); addMessage('assistant', '❌ Hata: ' + e.message); }
}

function addMessage(role, content) {
    const container = document.getElementById('chatContainer');
    const welcome = container.querySelector('.welcome');
    if(welcome) welcome.remove();
    messages.push({ role, content });
    renderMessage(role, content, messages.length - 1);
    container.scrollTop = container.scrollHeight;
}

function renderMessage(role, content, idx) {
    const container = document.getElementById('chatContainer');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `<div class="message-avatar">${role === 'assistant' ? '🤖' : '👤'}</div><div class="message-content"><div class="message-bubble">${formatContent(content)}</div>${role === 'assistant' ? `<div class="message-actions"><button class="action-icon-btn" onclick="copyText(${idx})">📋 Kopyala</button><button class="action-icon-btn" onclick="downloadPDF(${idx})">📥 PDF</button></div>` : ''}</div>`;
    container.appendChild(div);
}

function formatContent(text) { return text.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>').replace(/\\n/g, '<br>'); }
function showTyping() { const c = document.getElementById('chatContainer'); const d = document.createElement('div'); d.className = 'message assistant'; d.id = 'typingMsg'; d.innerHTML = `<div class="message-avatar">🤖</div><div class="message-content"><div class="message-bubble"><div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div></div></div>`; c.appendChild(d); c.scrollTop = c.scrollHeight; }
function hideTyping() { const el = document.getElementById('typingMsg'); if(el) el.remove(); }
function copyText(idx) { navigator.clipboard.writeText(messages[idx].content); }
function downloadPDF(idx) { const doc = new jsPDF(); doc.setFont('helvetica'); doc.setFontSize(12); doc.text(doc.splitTextToSize(messages[idx].content.replace(/\\*\\*/g, ''), 180), 15, 20); doc.save('studyrag-cevap.pdf'); }

function openQuizModal() { document.getElementById('quizModal').classList.add('show'); }
function openPlanModal() { document.getElementById('planModal').classList.add('show'); }
function closeModals() { document.querySelectorAll('.modal-overlay').forEach(m => m.classList.remove('show')); }

async function generateQuiz() {
    closeModals(); addMessage('user', '📝 Quiz oluştur'); showTyping();
    try {
        const res = await fetch('/generate-quiz', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ quiz_type: document.getElementById('quizType').value, num_questions: parseInt(document.getElementById('quizNum').value), difficulty: document.getElementById('quizDiff').value, topic: document.getElementById('quizTopic').value || null }) });
        const data = await res.json(); hideTyping(); if(!res.ok) throw new Error(data.detail);
        let text = `📝 **Quiz** (${data.difficulty} - ${data.num_questions} soru)\\n\\n`;
        data.questions.forEach((q, i) => { text += `**${i+1}. ${q.question}**\\n`; if(q.choices) text += q.choices.join('\\n') + '\\n'; text += `✅ ${q.correct_answer}\\n📖 ${q.explanation}\\n\\n`; });
        addMessage('assistant', text); saveChat();
    } catch(e) { hideTyping(); addMessage('assistant', '❌ ' + e.message); }
}

async function generatePlan() {
    closeModals(); addMessage('user', '📅 Çalışma planı'); showTyping();
    try {
        const res = await fetch('/study-plan', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ days: parseInt(document.getElementById('planDays').value), daily_minutes: parseInt(document.getElementById('planMinutes').value), focus: document.getElementById('planFocus').value || null }) });
        const data = await res.json(); hideTyping(); if(!res.ok) throw new Error(data.detail);
        let text = `📅 **${data.total_days} Günlük Plan**\\n${data.strategy_summary}\\n\\n`;
        data.days.forEach(d => { text += `**Gün ${d.day_index}: ${d.title}** (${d.estimated_minutes} dk)\\n📌 ${d.focus_topics.join(', ')}\\n🎯 ${d.goals.join(', ')}\\n\\n`; });
        addMessage('assistant', text); saveChat();
    } catch(e) { hideTyping(); addMessage('assistant', '❌ ' + e.message); }
}

document.getElementById('chatInput').addEventListener('input', function() { this.style.height = 'auto'; this.style.height = Math.min(this.scrollHeight, 200) + 'px'; });
</script>
</body>
</html>'''
    return HTMLResponse(content=html)
