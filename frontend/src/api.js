const API_BASE = '/api';

async function request(url, options = {}) {
    const config = {
        headers: {
            'Content-Type': 'application/json',
        },
        ...options,
    };

    if (config.body && typeof config.body === 'object') {
        config.body = JSON.stringify(config.body);
    }

    const response = await fetch(`${API_BASE}${url}`, config);
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || `Request failed: ${response.status}`);
    }

    return data;
}

// ===== Projects =====
export async function listProjects() {
    return request('/projects/');
}

export async function createProject(name, rawText, settings = null) {
    return request('/projects/', {
        method: 'POST',
        body: { name, raw_text: rawText, settings },
    });
}

export async function getProject(projectId) {
    return request(`/projects/${projectId}`);
}

export async function updateProject(projectId, data) {
    return request(`/projects/${projectId}`, {
        method: 'PUT',
        body: data,
    });
}

export async function deleteProject(projectId) {
    return request(`/projects/${projectId}`, {
        method: 'DELETE',
    });
}

export async function processText(projectId) {
    return request(`/projects/${projectId}/text/process-text`, {
        method: 'POST',
        body: {},
    });
}

// ===== Text Segments =====
export async function getSegments(projectId) {
    return request(`/projects/${projectId}/text/segments`);
}

// ===== Characters =====
export async function getCharacters(projectId) {
    return request(`/projects/${projectId}/characters/`);
}

export async function extractCharacters(projectId) {
    return request(`/projects/${projectId}/characters/extract`, {
        method: 'POST',
        body: {},
    });
}

export async function addCharacter(projectId, characterData) {
    return request(`/projects/${projectId}/characters/`, {
        method: 'POST',
        body: characterData,
    });
}

export async function updateCharacter(projectId, characterName, data) {
    return request(`/projects/${projectId}/characters/${encodeURIComponent(characterName)}`, {
        method: 'PUT',
        body: data,
    });
}

export async function deleteCharacter(projectId, characterName) {
    return request(`/projects/${projectId}/characters/${encodeURIComponent(characterName)}`, {
        method: 'DELETE',
    });
}

export async function generateCharacterDescription(projectId, characterName, suggestion = '') {
    return request(`/projects/${projectId}/characters/${encodeURIComponent(characterName)}/generate-description`, {
        method: 'POST',
        body: { suggestion },
    });
}

// ===== Dialogues =====
export async function getDialogues(projectId) {
    return request(`/projects/${projectId}/dialogues/`);
}

export async function allocateDialogues(projectId) {
    return request(`/projects/${projectId}/dialogues/allocate`, {
        method: 'POST',
        body: {},
    });
}

export async function updateDialogue(projectId, segmentIndex, speaker) {
    return request(`/projects/${projectId}/dialogues/${segmentIndex}`, {
        method: 'PUT',
        body: { speaker },
    });
}

// ===== Voice Designs =====
export async function getVoiceDesigns(projectId) {
    return request(`/projects/${projectId}/voice/designs`);
}

export async function generateVoiceDesigns(projectId) {
    return request(`/projects/${projectId}/voice/generate-designs`, {
        method: 'POST',
        body: {},
    });
}

export async function updateVoiceDesign(projectId, voiceName, data) {
    return request(`/projects/${projectId}/voice/designs/${encodeURIComponent(voiceName)}/update`, {
        method: 'PUT',
        body: data,
    });
}

export async function generateReferenceAudio(projectId, characterName = null) {
    return request(`/projects/${projectId}/voice/generate-reference-audio`, {
        method: 'POST',
        body: characterName ? { character_name: characterName } : {},
    });
}

// ===== Audio =====
export async function generateAudio(projectId) {
    return request(`/projects/${projectId}/audio/generate`, {
        method: 'POST',
        body: {},
    });
}

export async function getAudioStatus(projectId, taskId) {
    return request(`/projects/${projectId}/audio/status/${taskId}`);
}

export async function getAudioSegments(projectId) {
    return request(`/projects/${projectId}/audio/segments`);
}

export async function regenerateSegment(projectId, segmentIndex) {
    return request(`/projects/${projectId}/audio/segments/${segmentIndex}/regenerate`, {
        method: 'POST',
        body: {},
    });
}

export async function getAudioProgress(projectId) {
    return request(`/projects/${projectId}/audio/progress`);
}

// ===== Output =====
export async function renderAudio(projectId) {
    return request(`/projects/${projectId}/output/render`, {
        method: 'POST',
        body: {},
    });
}

export async function getOutputStatus(projectId) {
    return request(`/projects/${projectId}/output/status`);
}

export function getDownloadUrl(projectId) {
    return `${API_BASE}/projects/${projectId}/output/download`;
}

// ===== Project Settings =====
export async function updateProjectSettings(projectId, settings) {
    return request(`/projects/${projectId}`, {
        method: 'PUT',
        body: { project_setting: settings },
    });
}

// ===== Save project =====
export async function saveProject(projectId) {
    // Save is done implicitly by the backend on each operation
    // But we can trigger it through a project update
    return request(`/projects/${projectId}`, {
        method: 'PUT',
        body: {},
    });
}
