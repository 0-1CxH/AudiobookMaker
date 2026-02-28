/**
 * ABM Frontend - Shared Utilities
 */

const API_BASE = '/api';

// ---- Character Colors ----
const CHARACTER_COLORS = [
    { hex: '#6366f1', rgb: '99, 102, 241' },
    { hex: '#ec4899', rgb: '236, 72, 153' },
    { hex: '#14b8a6', rgb: '20, 184, 166' },
    { hex: '#f59e0b', rgb: '245, 158, 11' },
    { hex: '#8b5cf6', rgb: '139, 92, 246' },
    { hex: '#06b6d4', rgb: '6, 182, 212' },
    { hex: '#f43f5e', rgb: '244, 63, 94' },
    { hex: '#84cc16', rgb: '132, 204, 22' },
    { hex: '#e879f9', rgb: '232, 121, 249' },
    { hex: '#fb923c', rgb: '251, 146, 60' },
];

function getCharacterColor(index) {
    return CHARACTER_COLORS[index % CHARACTER_COLORS.length];
}

// ---- API Helpers ----
async function apiGet(path) {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Request failed: ${res.status}`);
    }
    return res.json();
}

async function apiPost(path, body = null) {
    const res = await fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Request failed: ${res.status}`);
    }
    return res.json();
}

async function apiPut(path, body) {
    const res = await fetch(`${API_BASE}${path}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Request failed: ${res.status}`);
    }
    return res.json();
}

async function apiDelete(path) {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Request failed: ${res.status}`);
    }
    return res.json();
}

// Actually correct delete implementation
async function apiDeleteMethod(path) {
    const res = await fetch(`${API_BASE}${path}`, { method: 'DELETE' });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Request failed: ${res.status}`);
    }
    return res.json();
}

// ---- Toast Notifications ----
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = { success: '✓', error: '✕', info: 'ℹ' };
    toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span> ${escapeHtml(message)}`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
        if (container.children.length === 0) container.remove();
    }, 4000);
}

// ---- Loading Button State ----
function setButtonLoading(btn, loading, originalText = null) {
    if (loading) {
        btn._originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner"></span> 处理中...`;
    } else {
        btn.disabled = false;
        btn.innerHTML = originalText || btn._originalText || btn.textContent;
    }
}

// ---- Modal Helpers ----
function openModal(id) {
    const overlay = document.getElementById(id);
    if (overlay) {
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(id) {
    const overlay = document.getElementById(id);
    if (overlay) {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Close modal when clicking overlay background
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
        document.body.style.overflow = '';
    }
});

// ---- Escape HTML ----
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ---- Truncate Text ----
function truncateText(text, maxLen = 80) {
    if (!text) return '';
    return text.length > maxLen ? text.substring(0, maxLen) + '...' : text;
}

// ---- Navigate ----
function navigateTo(url) {
    window.location.href = url;
}

// ---- Confirm Dialog ----
function confirmAction(message) {
    return window.confirm(message);
}

// ---- Skeleton Loader ----
function renderSkeletons(container, count = 3) {
    let html = '';
    for (let i = 0; i < count; i++) {
        html += `<div class="skeleton skeleton-block"></div>`;
    }
    container.innerHTML = html;
}

// ---- Build character color map ----
function buildCharacterColorMap(characters) {
    const map = {};
    characters.forEach((ch, i) => {
        const color = getCharacterColor(i);
        map[ch.name] = color;
    });
    return map;
}
