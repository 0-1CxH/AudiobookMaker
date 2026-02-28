import React, { useState, useEffect } from 'react'
import { listProjects, createProject, deleteProject, processText } from '../api.js'
import { useToast } from '../App.jsx'

export default function ProjectList({ onSelectProject }) {
    const addToast = useToast()
    const [projects, setProjects] = useState([])
    const [loading, setLoading] = useState(true)
    const [showCreate, setShowCreate] = useState(false)
    const [creating, setCreating] = useState(false)

    // Create form state
    const [newName, setNewName] = useState('')
    const [newText, setNewText] = useState('')

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
            const res = await createProject(newName.trim(), newText)
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

    const handleFileUpload = (e) => {
        const file = e.target.files[0]
        if (!file) return
        const reader = new FileReader()
        reader.onload = (event) => {
            setNewText(event.target.result)
            addToast(`已加载文件: ${file.name}`, 'info')
        }
        reader.readAsText(file)
        e.target.value = ''
    }

    return (
        <div className="page-container" style={{ maxWidth: 900, margin: '0 auto' }}>
            {/* Header */}
            <div className="page-header" style={{ paddingTop: 60 }}>
                <h1>ABM - 音频书制作工具</h1>
                <p>从文本自动生成高质量有声书</p>
            </div>

            {/* Create Button */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 'var(--space-4)' }}>
                <button
                    className="btn btn-primary btn-lg"
                    onClick={() => setShowCreate(!showCreate)}
                >
                    {showCreate ? '✕ 收起' : '＋ 创建新项目'}
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
                            placeholder="请输入项目名称（英文或拼音，无空格）"
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
                        <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
                            📁 上传文件
                            <input
                                type="file"
                                accept=".txt,.md"
                                onChange={handleFileUpload}
                                style={{ display: 'none' }}
                            />
                        </label>
                        <button
                            className="btn btn-ghost"
                            onClick={() => setNewText('')}
                            disabled={!newText}
                        >
                            清空文本
                        </button>
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
                                    <h3>📖 {proj.name || proj.project_id}</h3>
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
        </div>
    )
}
