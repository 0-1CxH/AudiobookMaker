import React, { useState, useEffect } from 'react'
import { listProjects, createProject, deleteProject, processText } from '../api.js'
import { useToast } from '../App.jsx'
import SettingsModal from './SettingsModal.jsx'

export default function ProjectList({ onSelectProject }) {
    const addToast = useToast()
    const [projects, setProjects] = useState([])
    const [loading, setLoading] = useState(true)
    const [showCreate, setShowCreate] = useState(false)
    const [creating, setCreating] = useState(false)
    const [showSettings, setShowSettings] = useState(false)
    const [selectedProjectId, setSelectedProjectId] = useState(null)

    // Create form state
    const [newName, setNewName] = useState('')
    const [newText, setNewText] = useState('')
    const [showAdvancedSettings, setShowAdvancedSettings] = useState(false)
    const [projectSettings, setProjectSettings] = useState({
        split_format: 'line',
        quote_format: 'auto',
        context_window: 10,
        default_duration: 0.2,
        line_break_duration: 0.5,
        sentence_margin_duration: 0.3,
        voice_lib_folder_path: './workspace/voice_lib',
        design_model_path: './workspace/design_model',
        clone_model_path: './workspace/clone_model',
        use_flash_attention: false,
    })

    const fetchProjects = async () => {
        try {
            setLoading(true)
            const res = await listProjects()
            setProjects(res.data?.projects || [])
        } catch (err) {
            addToast('加载项目列表失败: ' + err.message, 'error')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchProjects()
    }, [])

    const handleSettingChange = (key, value) => {
        setProjectSettings(prev => ({ ...prev, [key]: value }))
    }

    const handleCreate = async () => {
        if (!newName.trim()) {
            addToast('请输入项目名称', 'error')
            return
        }
        if (!newText.trim()) {
            addToast('请输入原始文本', 'error')
            return
        }

        try {
            setCreating(true)
            const res = await createProject(newName.trim(), newText, projectSettings)
            addToast('项目创建成功，正在处理文本...', 'success')

            // Auto-process text
            try {
                await processText(newName.trim())
                addToast('文本处理完成', 'success')
            } catch (e) {
                addToast('文本处理失败: ' + e.message, 'error')
            }

            // Navigate to the project
            onSelectProject(newName.trim(), newName.trim())
        } catch (err) {
            addToast('创建项目失败: ' + err.message, 'error')
        } finally {
            setCreating(false)
        }
    }

    const handleDelete = async (projectId, e) => {
        e.stopPropagation()
        if (!confirm(`确定删除项目 "${projectId}" 吗？此操作不可撤销。`)) return
        try {
            await deleteProject(projectId)
            addToast('项目已删除', 'success')
            fetchProjects()
        } catch (err) {
            addToast('删除失败: ' + err.message, 'error')
        }
    }


    return (
        <div className="page-container" style={{ maxWidth: 900, margin: '0 auto' }}>
            {/* Header */}
            <div className="page-header" style={{ paddingTop: 60 }}>
                <h1>AudiobookMaker 音频书制作智能工作流</h1>
                <p>由LLM驱动的文字自动生成高质量有声书应用</p>
            </div>

            {/* Create Button */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 'var(--space-4)' }}>
                <button
                    className="btn btn-primary btn-lg"
                    onClick={() => setShowCreate(!showCreate)}
                >
                    {showCreate ? '✕' : '＋'}
                </button>
            </div>

            {/* Create Panel */}
            {showCreate && (
                <div className="create-project-panel" style={{ marginBottom: 'var(--space-6)' }}>
                    <h2>创建新项目</h2>

                    <div className="form-group">
                        <label className="form-label">项目名称</label>
                        <input
                            className="input"
                            type="text"
                            placeholder="请输入项目名称"
                            value={newName}
                            onChange={e => setNewName(e.target.value)}
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">原始文本</label>
                        <textarea
                            className="textarea"
                            rows={10}
                            placeholder="在此粘贴文本内容..."
                            value={newText}
                            onChange={e => setNewText(e.target.value)}
                            style={{ minHeight: 200 }}
                        />
                    </div>

                    <div style={{ display: 'flex', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
                        <button
                            className="btn btn-ghost"
                            onClick={() => setNewText('')}
                            disabled={!newText}
                        >
                            清空文本
                        </button>
                    </div>

                    {/* Advanced Settings */}
                    <div style={{ marginBottom: 'var(--space-4)' }}>
                        <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                            style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}
                        >
                            {showAdvancedSettings ? '▼' : '▶'} 高级设置
                        </button>

                        {showAdvancedSettings && (
                            <div style={{
                                marginTop: 'var(--space-3)',
                                padding: 'var(--space-4)',
                                background: 'var(--base-2)',
                                borderRadius: 'var(--radius-lg)',
                                border: '1px solid var(--border)'
                            }}>
                                {/* Text Processing Settings */}
                                <div style={{ marginBottom: 'var(--space-4)' }}>
                                    <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, marginBottom: 'var(--space-3)' }}>文本处理设置</h3>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 'var(--space-3)' }}>
                                        <div className="form-group">
                                            <label className="form-label">分割方式</label>
                                            <select
                                                className="select"
                                                value={projectSettings.split_format}
                                                onChange={e => handleSettingChange('split_format', e.target.value)}
                                            >
                                                <option value="line">按行分割</option>
                                                <option value="sentence">按句子分割</option>
                                            </select>
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">引语检测</label>
                                            <select
                                                className="select"
                                                value={projectSettings.quote_format}
                                                onChange={e => handleSettingChange('quote_format', e.target.value)}
                                            >
                                                <option value="auto">自动检测</option>
                                            </select>
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">上下文窗口大小</label>
                                            <input
                                                className="input"
                                                type="number"
                                                min={1}
                                                max={50}
                                                value={projectSettings.context_window}
                                                onChange={e => handleSettingChange('context_window', parseInt(e.target.value) || 10)}
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Audio Settings */}
                                <div style={{ marginBottom: 'var(--space-4)' }}>
                                    <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, marginBottom: 'var(--space-3)' }}>音频设置</h3>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 'var(--space-3)' }}>
                                        <div className="form-group">
                                            <label className="form-label">默认空白时长 (秒)</label>
                                            <input
                                                className="input"
                                                type="number"
                                                step="0.1"
                                                min={0}
                                                value={projectSettings.default_duration}
                                                onChange={e => handleSettingChange('default_duration', parseFloat(e.target.value) || 0.2)}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">换行停顿时长 (秒)</label>
                                            <input
                                                className="input"
                                                type="number"
                                                step="0.1"
                                                min={0}
                                                value={projectSettings.line_break_duration}
                                                onChange={e => handleSettingChange('line_break_duration', parseFloat(e.target.value) || 0.5)}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">句间停顿时长 (秒)</label>
                                            <input
                                                className="input"
                                                type="number"
                                                step="0.1"
                                                min={0}
                                                value={projectSettings.sentence_margin_duration}
                                                onChange={e => handleSettingChange('sentence_margin_duration', parseFloat(e.target.value) || 0.3)}
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Model Paths */}
                                <div>
                                    <h3 style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, marginBottom: 'var(--space-3)' }}>TTS模型路径</h3>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                                        <div className="form-group">
                                            <label className="form-label">声音库文件夹路径</label>
                                            <input
                                                className="input"
                                                type="text"
                                                value={projectSettings.voice_lib_folder_path}
                                                onChange={e => handleSettingChange('voice_lib_folder_path', e.target.value)}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">设计模型路径</label>
                                            <input
                                                className="input"
                                                type="text"
                                                value={projectSettings.design_model_path}
                                                onChange={e => handleSettingChange('design_model_path', e.target.value)}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">克隆模型路径</label>
                                            <input
                                                className="input"
                                                type="text"
                                                value={projectSettings.clone_model_path}
                                                onChange={e => handleSettingChange('clone_model_path', e.target.value)}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label className="checkbox-group">
                                                <input
                                                    type="checkbox"
                                                    checked={projectSettings.use_flash_attention}
                                                    onChange={e => handleSettingChange('use_flash_attention', e.target.checked)}
                                                />
                                                <span>使用 Flash Attention 加速</span>
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end' }}>
                        <button className="btn btn-ghost" onClick={() => setShowCreate(false)}>取消</button>
                        <button
                            className="btn btn-primary btn-lg"
                            onClick={handleCreate}
                            disabled={creating}
                        >
                            {creating ? '创建中...' : '创建项目'}
                        </button>
                    </div>
                </div>
            )}

            {/* Project List */}
            <div>
                <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600, marginBottom: 'var(--space-4)' }}>
                    所有项目
                </h2>

                {loading ? (
                    <div className="loading-spinner">
                        <div className="spinner" />
                    </div>
                ) : projects.length === 0 ? (
                    <div className="empty-state">
                        <div className="empty-state-icon">📚</div>
                        <p>还没有项目，点击上方按钮创建第一个有声书项目</p>
                    </div>
                ) : (
                    <div className="projects-grid">
                        {projects.map(proj => (
                            <div
                                key={proj.project_id}
                                className="project-item"
                                onClick={() => onSelectProject(proj.project_id, proj.name || proj.project_id)}
                            >
                                <div className="project-item-info">
                                    <h3>{proj.name || proj.project_id}</h3>
                                    <div className="project-item-meta">
                                        {proj.segment_count > 0 && (
                                            <span>{proj.segment_count} 文本片段</span>
                                        )}
                                        {proj.character_count > 0 && (
                                            <span>{proj.character_count} 个角色</span>
                                        )}
                                        {proj.generated_audio_count > 0 && (
                                            <span>{proj.generated_audio_count} 段音频</span>
                                        )}
                                    </div>
                                </div>
                                <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                                    <button
                                        className="btn btn-primary"
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            onSelectProject(proj.project_id, proj.name || proj.project_id)
                                        }}
                                    >
                                        加载
                                    </button>
                                    <button
                                        className="btn btn-secondary btn-sm"
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            setSelectedProjectId(proj.project_id)
                                            setShowSettings(true)
                                        }}
                                    >
                                        ⚙️ 项目设置
                                    </button>
                                    <button
                                        className="btn btn-ghost btn-sm"
                                        onClick={(e) => handleDelete(proj.project_id, e)}
                                        style={{ color: 'var(--accent-red)' }}
                                    >
                                        删除
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {showSettings && (
                <SettingsModal
                    projectId={selectedProjectId}
                    onClose={() => setShowSettings(false)}
                />
            )}
        </div>
    )
}
