import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
    getSegments,
    getCharacters,
    extractCharacters,
    addCharacter,
    updateCharacter,
    deleteCharacter,
    generateCharacterDescription,
} from '../api.js'
import { useToast } from '../App.jsx'

// ===== Character Edit Modal =====
function CharacterEditModal({ character, projectId, onClose, onSaved }) {
    const addToast = useToast()
    const isNew = !character
    const [name, setName] = useState(character?.name || '')
    const [description, setDescription] = useState(character?.description || '')
    const [requiresTts, setRequiresTts] = useState(character?.requires_tts ?? true)
    const [voiceName, setVoiceName] = useState(character?.voice_name || character?.name || '')
    const [saving, setSaving] = useState(false)
    const [showSuggestionPopover, setShowSuggestionPopover] = useState(false)
    const [suggestionInput, setSuggestionInput] = useState('')
    const [submittingSuggestion, setSubmittingSuggestion] = useState(false)
    const [descriptionHighlighted, setDescriptionHighlighted] = useState(false)
    const descriptionTextareaRef = useRef(null)

    const handleSave = async () => {
        if (!name.trim()) {
            addToast('请输入角色名称', 'error')
            return
        }
        if (requiresTts && !voiceName.trim()) {
            addToast('请为TTS语音合成输入语音名称', 'error')
            return
        }
        try {
            setSaving(true)
            if (isNew) {
                await addCharacter(projectId, {
                    name: name.trim(),
                    description,
                    requires_tts: requiresTts,
                    voice_name: voiceName,
                })
                addToast(`角色 "${name}" 已添加`, 'success')
            } else {
                await updateCharacter(projectId, character.name, {
                    description,
                    requires_tts: requiresTts,
                    voice_name: voiceName,
                })
                addToast(`角色 "${character.name}" 已更新`, 'success')
            }
            onSaved()
            onClose()
        } catch (err) {
            addToast('保存失败: ' + err.message, 'error')
        } finally {
            setSaving(false)
        }
    }

    const handleShowSuggestionPopup = () => {
        if (isNew) {
            addToast('请先保存角色再生成描述', 'error')
            return
        }
        setShowSuggestionPopover(true)
    }

    const handleSubmitSuggestion = async () => {
        try {
            setSubmittingSuggestion(true)
            const res = await generateCharacterDescription(projectId, character.name, suggestionInput.trim())
            // 支持两种响应格式：res.data?.description 或 res.description
            const newDescription = res.data?.description || res.description
            if (newDescription) {
                setDescription(newDescription)
                // 设置高亮状态并聚焦到textarea
                setDescriptionHighlighted(true)
                if (descriptionTextareaRef.current) {
                    descriptionTextareaRef.current.focus()
                    // 选中所有文本以便用户立即看到新内容
                    descriptionTextareaRef.current.select()
                }
                setShowSuggestionPopover(false)
                setSuggestionInput('')
                addToast('AI描述已生成', 'success')
            } else {
                addToast('生成描述失败：未收到有效的描述', 'error')
            }
        } catch (err) {
            addToast('生成描述失败: ' + err.message, 'error')
        } finally {
            setSubmittingSuggestion(false)
        }
    }

    // 高亮效果定时器
    useEffect(() => {
        if (descriptionHighlighted) {
            const timer = setTimeout(() => {
                setDescriptionHighlighted(false)
            }, 2000) // 2秒后取消高亮
            return () => clearTimeout(timer)
        }
    }, [descriptionHighlighted])

    const handleCancelSuggestion = () => {
        setShowSuggestionPopover(false)
        setSuggestionInput('')
    }

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>{isNew ? '新建角色' : `编辑角色: ${character.name}`}</h2>
                    <button className="btn btn-ghost btn-sm" onClick={onClose}>✕</button>
                </div>
                <div className="modal-body">
                    <div className="form-group">
                        <label className="form-label">角色名称</label>
                        <input
                            className="input"
                            type="text"
                            placeholder="角色名称"
                            value={name}
                            onChange={e => setName(e.target.value)}
                            disabled={!isNew}
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">角色描述</label>
                        <textarea
                            ref={descriptionTextareaRef}
                            className="textarea"
                            rows={4}
                            placeholder="角色描述..."
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                            style={{
                                transition: 'background-color 0.5s ease',
                                backgroundColor: descriptionHighlighted ? 'var(--highlight-bg, #fff3cd)' : ''
                            }}
                        />
                        {!isNew && (
                            <div style={{ position: 'relative', display: 'inline-block' }}>
                                <button
                                    className="btn btn-secondary btn-sm mt-2"
                                    onClick={handleShowSuggestionPopup}
                                    disabled={showSuggestionPopover}
                                >
                                    {showSuggestionPopover ? '输入建议...' : '🧠 AI生成角色描述'}
                                </button>
                                {showSuggestionPopover && (
                                    <div className="popover" style={{
                                        position: 'absolute',
                                        top: 0,
                                        left: '100%',
                                        marginLeft: '8px',
                                        backgroundColor: 'var(--bg-secondary)',
                                        border: '1px solid var(--border-color)',
                                        borderRadius: 'var(--radius-md)',
                                        padding: 'var(--space-3)',
                                        boxShadow: 'var(--shadow-lg)',
                                        zIndex: 1000,
                                        minWidth: '300px'
                                    }}>
                                        <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                                            <input
                                                type="text"
                                                className="input"
                                                placeholder="请输入改进建议..."
                                                value={suggestionInput}
                                                onChange={e => setSuggestionInput(e.target.value)}
                                                style={{ flex: 1 }}
                                                onKeyDown={(e) => {
                                                    if (e.key === 'Enter') {
                                                        handleSubmitSuggestion()
                                                    }
                                                }}
                                            />
                                            <button
                                                className="btn btn-primary btn-sm"
                                                onClick={handleSubmitSuggestion}
                                                disabled={submittingSuggestion}
                                            >
                                                {submittingSuggestion ? '生成中...' : '>'}
                                            </button>
                                            <button
                                                className="btn btn-ghost btn-sm"
                                                onClick={handleCancelSuggestion}
                                            >
                                                ✕
                                            </button>
                                        </div>
                                        <div style={{
                                            fontSize: 'var(--font-size-xs)',
                                            color: 'var(--text-muted)',
                                            marginTop: 'var(--space-2)'
                                        }}>
                                            AI会根据建议生成更符合需求的角色描述
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    <div className="form-group">
                        <label className="checkbox-group">
                            <input
                                type="checkbox"
                                checked={requiresTts}
                                onChange={e => setRequiresTts(e.target.checked)}
                            />
                            <span>需要语音设计</span>
                        </label>
                    </div>

                    {requiresTts && (
                        <div className="form-group">
                            <label className="form-label">语音名称 *</label>
                            <input
                                className="input"
                                type="text"
                                placeholder={"请输入语音名称"}
                                value={voiceName}
                                onChange={e => setVoiceName(e.target.value)}
                            />
                        </div>
                    )}
                </div>
                <div className="modal-footer">
                    <button className="btn btn-ghost" onClick={onClose}>取消</button>
                    <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                        {saving ? '保存中...' : '保存'}
                    </button>
                </div>
            </div>
        </div>
    )
}

// ===== Main Component =====
export default function CharacterExtract({ projectId }) {
    const addToast = useToast()
    const [segments, setSegments] = useState([])
    const [characters, setCharacters] = useState([])
    const [loading, setLoading] = useState(true)
    const [extracting, setExtracting] = useState(false)
    const [editChar, setEditChar] = useState(undefined) // undefined=closed, null=new, object=edit
    const [showEditModal, setShowEditModal] = useState(false)
    const [currentPage, setCurrentPage] = useState(1)
    const segmentsPerPage = 50

    const fetchData = useCallback(async () => {
        try {
            setLoading(true)
            setCurrentPage(1)
            const [segRes, charRes] = await Promise.all([
                getSegments(projectId),
                getCharacters(projectId),
            ])
            setSegments(segRes.data?.segments || [])
            setCharacters(charRes.data?.characters || [])
        } catch (err) {
            addToast('加载数据失败: ' + err.message, 'error')
        } finally {
            setLoading(false)
        }
    }, [projectId])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    const handleExtract = async () => {
        try {
            setExtracting(true)
            addToast('正在AI提取角色...', 'info')
            const res = await extractCharacters(projectId)
            setCharacters(res.data?.characters || [])
            addToast('角色提取完成', 'success')
        } catch (err) {
            addToast('角色提取失败: ' + err.message, 'error')
        } finally {
            setExtracting(false)
        }
    }

    const handleDelete = async (charName) => {
        if (!confirm(`确定删除角色 "${charName}" 吗？`)) return
        try {
            await deleteCharacter(projectId, charName)
            addToast(`角色 "${charName}" 已删除`, 'success')
            fetchData()
        } catch (err) {
            addToast('删除失败: ' + err.message, 'error')
        }
    }

    const openNewChar = () => {
        setEditChar(null)
        setShowEditModal(true)
    }

    const openEditChar = (char) => {
        setEditChar(char)
        setShowEditModal(true)
    }

    if (loading) {
        return (
            <div className="loading-spinner">
                <div className="spinner" />
            </div>
        )
    }

    return (
        <>
            <div className="split-layout">
                {/* Left: Text Segments */}
                <div className="card">
                    <div className="card-header">
                        <span className="card-title">📄 文本处理结果</span>
                        <span className="text-xs text-muted">{segments.length} 个片段</span>
                    </div>
                    <div style={{ maxHeight: 'calc(100vh - 330px)', overflowY: 'auto' }}>
                        {(() => {
                            // 计算分页
                            const startIdx = (currentPage - 1) * segmentsPerPage
                            const endIdx = startIdx + segmentsPerPage
                            const paginatedSegments = segments.slice(startIdx, endIdx)

                            // 分组渲染segments，PLACEHOLDER不换行
                            const rows = []
                            let currentRow = []
                            let rowKey = 0

                            paginatedSegments.forEach((seg, pageIdx) => {
                                const actualIdx = startIdx + pageIdx
                                const isPlaceholder = seg.tag === 'PLACEHOLDER'

                                // 跳过空的PLACEHOLDER
                                if (isPlaceholder && (seg.content === '\n' || seg.content.trim() === '')) {
                                    return
                                }

                                // 如果是PLACEHOLDER且不是换行符，添加到当前行
                                if (isPlaceholder) {
                                    currentRow.push({ seg, idx: actualIdx })
                                } else {
                                    // 如果不是PLACEHOLDER，先提交当前行（如果有）
                                    if (currentRow.length > 0) {
                                        rows.push({ items: currentRow, key: rowKey++ })
                                        currentRow = []
                                    }
                                    // 当前segment作为新行
                                    rows.push({ items: [{ seg, idx: actualIdx }], key: rowKey++ })
                                }
                            })

                            // 处理最后一行
                            if (currentRow.length > 0) {
                                rows.push({ items: currentRow, key: rowKey++ })
                            }

                            return rows.map(row => {
                                // 判断这一行是否只包含PLACEHOLDER
                                const isPlaceholderRow = row.items.every(item => item.seg.tag === 'PLACEHOLDER')

                                return (
                                    <div key={row.key} className="segment-row" style={{
                                        display: 'flex',
                                        flexWrap: 'wrap',
                                        alignItems: 'flex-start',
                                        marginBottom: 'var(--space-2)'
                                    }}>
                                        {row.items.map(({ seg, idx }) => {
                                            const isPlaceholder = seg.tag === 'PLACEHOLDER'
                                            const isDefault = seg.tag === 'DEFAULT'
                                            const tagClass = isPlaceholder ? 'tag-placeholder' : isDefault ? 'tag-default' : 'tag-quote'

                                            return (
                                                <div key={idx} className={`segment-block ${tagClass}`} style={{
                                                    display: isPlaceholderRow ? 'inline-block' : 'block',
                                                    marginBottom: 0,
                                                    marginRight: isPlaceholderRow && isPlaceholder ? 0 : 'var(--space-2)'
                                                }}>
                                                    <span style={{ opacity: 0.4, fontSize: 'var(--font-size-xs)', marginRight: 8 }}>
                                                        #{idx}
                                                    </span>
                                                    {seg.content}
                                                </div>
                                            )
                                        })}
                                    </div>
                                )
                            })
                        })()}
                    </div>
                    {segments.length > segmentsPerPage && (
                        <div style={{ 
                            display: 'flex', 
                            justifyContent: 'center', 
                            alignItems: 'center', 
                            gap: 'var(--space-2)',
                            padding: 'var(--space-3)',
                            borderTop: '1px solid var(--border-color)',
                            marginTop: 'var(--space-2)'
                        }}>
                            <button 
                                className="btn btn-ghost btn-sm"
                                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                            >
                                ← 上一页
                            </button>
                            <span style={{ color: 'var(--text-secondary)' }}>
                                {currentPage} / {Math.ceil(segments.length / segmentsPerPage)}
                            </span>
                            <button 
                                className="btn btn-ghost btn-sm"
                                onClick={() => setCurrentPage(p => Math.min(Math.ceil(segments.length / segmentsPerPage), p + 1))}
                                disabled={currentPage === Math.ceil(segments.length / segmentsPerPage)}
                            >
                                下一页 →
                            </button>
                        </div>
                    )}
                </div>

                {/* Right: Character List */}
                <div className="card">
                    <div className="card-header">
                        <span className="card-title">👥 角色列表</span>
                    </div>

                    <div style={{ display: 'flex', gap: 'var(--space-2)', marginBottom: 'var(--space-4)' }}>
                        <button
                            className="btn btn-primary btn-sm"
                            onClick={handleExtract}
                            disabled={extracting}
                        >
                            {extracting ? '🔄 提取中...' : '🧠 AI角色提取'}
                        </button>
                        <button className="btn btn-secondary btn-sm" onClick={openNewChar}>
                            ＋ 新建角色
                        </button>
                    </div>

                    <div style={{ maxHeight: 'calc(100vh - 340px)', overflowY: 'auto' }}>
                        {characters.length === 0 ? (
                            <div className="empty-state" style={{ padding: 'var(--space-8)' }}>
                                <p>暂无角色，点击"AI角色提取"自动识别</p>
                            </div>
                        ) : (
                            characters.map((char, idx) => (
                                <div key={char.name} className="character-card">
                                    <div className="character-card-header">
                                        <span className="character-name">{char.name}</span>
                                        <div className="character-actions">
                                            <button className="btn btn-ghost btn-sm" onClick={() => openEditChar(char)}>
                                                ✏️ 编辑
                                            </button>
                                            <button
                                                className="btn btn-ghost btn-sm"
                                                style={{ color: 'var(--accent-red)' }}
                                                onClick={() => handleDelete(char.name)}
                                            >
                                                🗑
                                            </button>
                                        </div>
                                    </div>
                                    <div className="character-meta">
                                        {char.description && (
                                            <span style={{ display: 'block', marginBottom: 4, color: 'var(--text-secondary)' }}>
                                                {char.description.length > 60
                                                    ? char.description.substring(0, 60) + '...'
                                                    : char.description}
                                            </span>
                                        )}
                                    </div>
                                    <div className="character-meta" style={{ marginTop: 'var(--space-2)' }}>
                                        <span>语音设计: {char.requires_tts ? '✅' : '❌'}</span>
                                        {char.voice_name && <span>语音名称: {char.voice_name}</span>}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            {/* Edit Modal */}
            {showEditModal && (
                <CharacterEditModal
                    character={editChar}
                    projectId={projectId}
                    onClose={() => setShowEditModal(false)}
                    onSaved={fetchData}
                />
            )}
        </>
    )
}
