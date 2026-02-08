/**
 * RAG 파일럿 시스템 - 프론트엔드 로직
 */

const API_BASE = 'http://localhost:8000';

// ========== 상태 관리 ==========
let currentLLM = 'ollama';
let currentTheme = 'dark';
let isLoading = false;

// ========== 초기화 ==========
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initUpload();
    loadSources();
    checkLLMStatus();
    autoResizeTextarea();
});

// ========== 테마 관리 ==========
function initTheme() {
    // 저장된 테마 또는 시스템 설정 확인
    const savedTheme = localStorage.getItem('rag-theme');
    if (savedTheme) {
        currentTheme = savedTheme;
    } else if (window.matchMedia('(prefers-color-scheme: light)').matches) {
        currentTheme = 'light';
    }
    document.documentElement.setAttribute('data-theme', currentTheme);
}

function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);
    localStorage.setItem('rag-theme', currentTheme);
    showToast(`${currentTheme === 'dark' ? '🌙' : '☀️'} ${currentTheme === 'dark' ? '다크' : '라이트'} 테마로 전환`, 'info');
}

// ========== 업로드 초기화 ==========
function initUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');

    // 클릭으로 업로드
    uploadArea.addEventListener('click', () => fileInput.click());

    // 파일 선택
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
        }
    });

    // 드래그 앤 드롭
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');

        if (e.dataTransfer.files.length > 0) {
            uploadFile(e.dataTransfer.files[0]);
        }
    });
}

// ========== 파일 업로드 ==========
async function uploadFile(file) {
    const allowedTypes = ['txt', 'pdf', 'docx'];
    const ext = file.name.split('.').pop().toLowerCase();

    if (!allowedTypes.includes(ext)) {
        showToast('지원하지 않는 파일 형식입니다.', 'error');
        return;
    }

    showLoading('파일 업로드 중...');

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showToast(`✅ ${data.message} (${data.chunks} 청크)`, 'success');
            loadSources();
        } else {
            showToast(`❌ ${data.detail}`, 'error');
        }
    } catch (error) {
        showToast('서버 연결 실패. 백엔드가 실행 중인지 확인하세요.', 'error');
    } finally {
        hideLoading();
    }
}

// ========== 소스 목록 로드 ==========
async function loadSources() {
    try {
        const response = await fetch(`${API_BASE}/sources`);
        const data = await response.json();

        const sourcesList = document.getElementById('sources-list');
        const sourceCount = document.getElementById('source-count');

        sourceCount.textContent = data.total;

        if (data.sources.length === 0) {
            sourcesList.innerHTML = `
                <div class="empty-sources">
                    <p style="color: var(--text-muted); font-size: 13px; text-align: center; padding: 20px;">
                        아직 업로드된 문서가 없습니다
                    </p>
                </div>
            `;
            return;
        }

        sourcesList.innerHTML = data.sources.map(source => `
            <div class="source-item" data-id="${source.id}">
                ${getFileIcon(source.name)}
                <div class="source-info">
                    <div class="source-name">${source.name}</div>
                    <div class="source-meta">${source.chunks} 청크</div>
                </div>
                <button class="source-delete" onclick="deleteSource('${source.id}', '${source.name}')">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>
            </div>
        `).join('');

    } catch (error) {
        console.error('소스 로드 실패:', error);
    }
}

// ========== 소스 삭제 ==========
async function deleteSource(docId, name) {
    if (!confirm(`"${name}"을(를) 삭제하시겠습니까?`)) return;

    try {
        const response = await fetch(`${API_BASE}/sources/${docId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showToast('소스가 삭제되었습니다.', 'success');
            loadSources();
        } else {
            showToast('삭제 실패', 'error');
        }
    } catch (error) {
        showToast('서버 연결 실패', 'error');
    }
}

// ========== 메시지 전송 ==========
async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();

    if (!message || isLoading) return;

    // 사용자 메시지 추가
    addMessage(message, 'user');
    input.value = '';
    input.style.height = 'auto';

    // 환영 메시지 숨기기
    const welcome = document.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    setLoading(true);

    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        addMessage(data.answer, 'assistant', data.sources);

    } catch (error) {
        addMessage('서버 연결에 실패했습니다. 백엔드가 실행 중인지 확인하세요.', 'assistant');
    } finally {
        setLoading(false);
    }
}

// ========== 메시지 추가 ==========
function addMessage(text, role, sources = []) {
    const container = document.getElementById('messages-container');

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatarIcon = role === 'user'
        ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
               <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
               <circle cx="12" cy="7" r="4"/>
           </svg>`
        : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
               <path d="M12 2l2.4 7.2H22l-6 4.8 2.4 7.2L12 16.8l-6.4 4.4L8 14l-6-4.8h7.6L12 2z"/>
           </svg>`;

    let sourcesHTML = '';
    if (sources && sources.length > 0) {
        sourcesHTML = `
            <div class="message-sources">
                <div class="sources-title">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
                    </svg>
                    참고 문서 (클릭하여 전체 보기)
                </div>
                ${sources.map(s => `
                    <div class="source-citation" onclick="openDocumentByName('${s.source.replace(/'/g, "\\'")}')">
                        <strong>${s.source}</strong>: ${s.content_preview}
                    </div>
                `).join('')}
            </div>
        `;
    }

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatarIcon}</div>
        <div class="message-content">
            <div class="message-text">${formatMessage(text)}</div>
            ${sourcesHTML}
        </div>
    `;

    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

// ========== 메시지 포맷팅 ==========
function formatMessage(text) {
    // 줄바꿈 처리
    return text.replace(/\n/g, '<br>');
}

// ========== LLM 전환 ==========
async function switchLLM(provider) {
    try {
        const response = await fetch(`${API_BASE}/llm/switch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider })
        });

        const data = await response.json();

        currentLLM = provider;
        updateLLMButtons();
        showToast(`🔄 ${data.message}`, 'info');

        // Ollama 전환 시 모델 목록 로드
        if (provider === 'ollama') {
            loadOllamaModels();
        }

    } catch (error) {
        showToast('LLM 전환 실패', 'error');
    }
}

function updateLLMButtons() {
    document.getElementById('btn-ollama').classList.toggle('active', currentLLM === 'ollama');
    document.getElementById('btn-openai').classList.toggle('active', currentLLM === 'openai');
}

async function checkLLMStatus() {
    try {
        const response = await fetch(`${API_BASE}/llm/status`);
        const data = await response.json();
        currentLLM = data.provider;
        updateLLMButtons();

        // Ollama가 활성화된 경우 모델 목록 로드
        if (currentLLM === 'ollama') {
            loadOllamaModels();
        }
    } catch (error) {
        console.log('LLM 상태 확인 실패');
    }
}

// ========== Ollama 모델 관리 ==========
let currentOllamaModel = '';

async function loadOllamaModels() {
    const select = document.getElementById('ollama-model-select');

    try {
        const response = await fetch(`${API_BASE}/ollama/models`);
        const data = await response.json();

        currentOllamaModel = data.current_model;

        if (data.models.length === 0) {
            select.innerHTML = '<option value="">설치된 모델 없음</option>';
            return;
        }

        select.innerHTML = data.models.map(model => {
            const size = formatBytes(model.size);
            const isSelected = model.name === data.current_model;
            return `<option value="${model.name}" ${isSelected ? 'selected' : ''}>${model.name} (${size})</option>`;
        }).join('');

    } catch (error) {
        select.innerHTML = '<option value="">모델 로드 실패</option>';
        console.error('Ollama 모델 로드 실패:', error);
    }
}

async function changeOllamaModel(modelName) {
    if (!modelName) return;

    try {
        const response = await fetch(`${API_BASE}/ollama/model`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: modelName })
        });

        const data = await response.json();

        if (data.success) {
            currentOllamaModel = modelName;
            showToast(`🤖 모델 변경: ${modelName}`, 'success');
        } else {
            showToast('모델 변경 실패', 'error');
        }
    } catch (error) {
        showToast('모델 변경 실패', 'error');
    }
}

function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// 설정 모달 열기 (나중에 확장 가능)
function openSettingsModal() {
    showToast('ℹ️ Ollama 모델은 아래 드롭다운에서 선택할 수 있습니다.', 'info');
}

// ========== 유틸리티 ==========
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'txt': `<svg class="source-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>`,
        'pdf': `<svg class="source-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <path d="M9 13h2"/>
                    <path d="M9 17h6"/>
                </svg>`,
        'docx': `<svg class="source-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                     <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                     <polyline points="14 2 14 8 20 8"/>
                     <line x1="16" y1="13" x2="8" y2="13"/>
                     <line x1="16" y1="17" x2="8" y2="17"/>
                     <line x1="10" y1="9" x2="8" y2="9"/>
                 </svg>`,
        'doc': `<svg class="source-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                </svg>`
    };
    return icons[ext] || icons['txt'];
}

function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function autoResizeTextarea() {
    const textarea = document.getElementById('message-input');
    textarea.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });
}

function setLoading(loading) {
    isLoading = loading;
    const btn = document.getElementById('send-btn');
    btn.disabled = loading;

    if (loading) {
        btn.innerHTML = '<div class="loading-spinner" style="width:20px;height:20px;border-width:2px;"></div>';
    } else {
        btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>`;
    }
}

// ========== 로딩 & 토스트 ==========
function showLoading(text = '처리 중...') {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading-overlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.remove('active');
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ========== 문서 뷰어 ==========

// 소스 이름-ID 매핑 저장 (캐시)
let sourceNameToIdMap = {};

// 소스 목록 로드 시 매핑 업데이트
async function updateSourceMap() {
    try {
        const response = await fetch(`${API_BASE}/sources`);
        const data = await response.json();
        sourceNameToIdMap = {};
        data.sources.forEach(s => {
            sourceNameToIdMap[s.name] = s.id;
        });
    } catch (error) {
        console.error('소스 맵 업데이트 실패:', error);
    }
}

// 문서 이름으로 열기
async function openDocumentByName(documentName) {
    // 먼저 소스 맵 업데이트
    await updateSourceMap();

    const docId = sourceNameToIdMap[documentName];
    if (!docId) {
        showToast('문서를 찾을 수 없습니다.', 'error');
        return;
    }

    openDocumentViewer(docId, documentName);
}

// 문서 뷰어 열기
async function openDocumentViewer(docId, docName) {
    const modal = document.getElementById('document-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');

    modal.classList.add('active');
    modalTitle.textContent = docName || '문서 내용';
    modalBody.innerHTML = '<p style="text-align: center; color: var(--text-muted);">로딩 중...</p>';

    try {
        const response = await fetch(`${API_BASE}/sources/${docId}/content`);

        if (!response.ok) {
            throw new Error('문서를 찾을 수 없습니다.');
        }

        const data = await response.json();

        modalTitle.textContent = data.name;

        // 청크별로 표시
        if (data.chunks_detail && data.chunks_detail.length > 0) {
            modalBody.innerHTML = `
                <div class="document-info" style="margin-bottom: 16px; padding: 12px; background: var(--bg-tertiary); border-radius: 8px;">
                    <strong>총 ${data.chunks}개 청크</strong>
                </div>
                ${data.chunks_detail.map((chunk, i) => `
                    <div class="document-chunk">
                        <div class="chunk-header">청크 ${i + 1}</div>
                        <div class="document-content">${escapeHtml(chunk.content)}</div>
                    </div>
                `).join('')}
            `;
        } else {
            modalBody.innerHTML = `
                <div class="document-content">${escapeHtml(data.full_content)}</div>
            `;
        }

    } catch (error) {
        modalBody.innerHTML = `<p style="color: var(--error);">오류: ${error.message}</p>`;
    }
}

// 모달 닫기
function closeDocumentModal() {
    document.getElementById('document-modal').classList.remove('active');
}

// HTML 이스케이프
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ESC 키로 모달 닫기
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeDocumentModal();
    }
});

// 모달 배경 클릭 시 닫기
document.addEventListener('click', (e) => {
    if (e.target.id === 'document-modal') {
        closeDocumentModal();
    }
});
