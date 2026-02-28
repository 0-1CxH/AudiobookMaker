import React, { useState, useEffect, useCallback } from 'react'
import {
    getVoiceDesigns,
    getCharacters,
    generateVoiceDesigns,
    updateVoiceDesign,
    generateReferenceAudio,
} from '../api.js'
import { useToast } from '../App.jsx'

// ===== Voice Design Edit Modal =====
function VoiceEditModal({ design, projectId, onClose, onSaved }) {
    const addToast = useToast()
    const [voiceName] = useState(design?.name || '')
    const [ttsInstruction, setTtsInstruction] = useState(design?.tts_instruction || '')
    const [referenceText, setReferenceText] = useState(design?.reference_text || '')
    const [saving, setSaving] = useState(false)
    const [generatingRef, setGeneratingRef] = useState(false)
    const [generatingDesign, setGeneratingDesign] = useState(false)
    const hasRefAudio = design?.has_reference_audio

    const handleSave = async () => {
        try {
            setSaving(true)
            await updateVoiceDesign(projectId, voiceName, {
                tts_instruction: ttsInstruction,
                reference_text: referenceText,
            })
            addToast('语音设计已保存', 'success')
            onSaved()
            onClose()
        } catch (err) {
            addToast('保存失败: ' + err.message, 'error')
        } finally {
            setSaving(false)
        }
    }

    const handleGenerateRefAudio = async () => {
        try {
            setGeneratingRef(true)
            addToast('正在生成参考音频...', 'info')
            await generateReferenceAudio(projectId, voiceName)
            addToast('参考音频已生成', 'success')
            onSaved()
        } catch (err) {
            addToast('生成参考音频失败: ' + err.message, 'error')
        } finally {
            setGeneratingRef(false)
        }
    }

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>🎙️ 编辑语音设计: {voiceName}</h2>
                    <button className="btn btn-ghost btn-sm" onClick={onClose}>✕</button>
                </div>
                <div className="modal-body">
                    <div className="form-group">
                        <label className="form-label">语音名称</label>
                        <input className="input" type="text" value={voiceName} disabled />
                    </div>

                    <div className="form-group">
                        <label className="form-label">TTS指令</label>
                        <textarea
                            className="textarea"
                            rows={5}
                            placeholder="TTS语音控制指令..."
                            value={ttsInstruction}
                            onChange={e => setTtsInstruction(e.target.value)}
                        />
                        <button
                            className="btn btn-secondary btn-sm mt-2"
                            disabled={generatingDesign}
                            onClick={async () => {
                                try {
                                    setGeneratingDesign(true)
                                    addToast('正在AI生成语音设计指令...', 'info')
                                    // The generate-designs endpoint generates for all, so we just inform user
                                    await generateVoiceDesigns(projectId)
                                    addToast('语音设计指令已生成，请刷新查看', 'success')
                                    onSaved()
                                } catch (err) {
                                    addToast('生成失败: ' + err.message, 'error')
                                } finally {
                                    setGeneratingDesign(false)
                                }
                            }}
                        >
                            {generatingDesign ? '🔄 生成中...' : '🤖 AI语音设计'}
                        </button>
                    </div>

                    <div className="form-group">
                        <label className="form-label">参考文本</label>
                        <textarea
                            className="textarea"
                            rows={3}
                            placeholder="参考文本（用于语音克隆）..."
                            value={referenceText}
                            onChange={e => setReferenceText(e.target.value)}
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">参考音频</label>
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 'var(--space-3)',
                            padding: 'var(--space-3)',
                            background: 'var(--bg-input)',
                            borderRadius: 'var(--radius-sm)',
                        }}>
                            <span className={`status-dot ${hasRefAudio ? 'generated' : 'not-generated'}`} />
                            <span className="text-sm">
                                {hasRefAudio ? '已生成' : '未生成'}
                            </span>
                            {hasRefAudio && (
                                <button className="btn btn-ghost btn-sm">▶ 播放</button>
                            )}
                            <button
                                className="btn btn-secondary btn-sm"
                                onClick={handleGenerateRefAudio}
                                disabled={generatingRef}
                            >
                                {generatingRef ? '🔄 生成中...' : (hasRefAudio ? '重新生成' : '生成参考音频')}
                            </button>
                        </div>
                    </div>
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
export default function VoiceDesign({ projectId }) {
    const addToast = useToast()
    const [designs, setDesigns] = useState([])
    const [characters, setCharacters] = useState([])
    const [loading, setLoading] = useState(true)
    const [generating, setGenerating] = useState(false)
    const [editDesign, setEditDesign] = useState(null)

    // Map character name → character
    const charMap = {}
    characters.forEach(c => { charMap[c.name] = c })

    const fetchData = useCallback(async () => {
        try {
            setLoading(true)
            const [vRes, cRes] = await Promise.all([
                getVoiceDesigns(projectId),
                getCharacters(projectId),
            ])
            setDesigns(vRes.data?.voice_designs || [])
            setCharacters(cRes.data?.characters || [])
        } catch (err) {
            addToast('加载数据失败: ' + err.message, 'error')
        } finally {
            setLoading(false)
        }
    }, [projectId])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    const handleGenerate = async () => {
        try {
            setGenerating(true)
            addToast('正在AI生成语音设计...', 'info')
            const res = await generateVoiceDesigns(projectId)
            setDesigns(res.data?.voice_designs || [])
            addToast('语音设计生成完成', 'success')
        } catch (err) {
            addToast('生成失败: ' + err.message, 'error')
        } finally {
            setGenerating(false)
        }
    }

    const handleGenerateAllRefAudio = async () => {
        try {
            addToast('正在生成所有参考音频...', 'info')
            await generateReferenceAudio(projectId)
            addToast('参考音频生成完成', 'success')
            fetchData()
        } catch (err) {
            addToast('生成参考音频失败: ' + err.message, 'error')
        }
    }

    // Build combined list: character + voice design
    const combinedList = characters.map(char => {
        const design = designs.find(d => d.name === char.voice_name)
        return { char, design }
    })

    if (loading) {
        return (
            <div className="loading-spinner">
                <div className="spinner" />
            </div>
        )
    }

    return (
        <>
            <div className="card">
                <div className="card-header">
                    <span className="card-title">🎙️ 语音设计</span>
                    <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                        <button
                            className="btn btn-primary btn-sm"
                            onClick={handleGenerate}
                            disabled={generating}
                        >
                            {generating ? '🔄 生成中...' : '🧠 AI语音设计'}
                        </button>
                        <button
                            className="btn btn-secondary btn-sm"
                            onClick={handleGenerateAllRefAudio}
                        >
                            🔊 生成所有参考音频
                        </button>
                    </div>
                </div>

                {combinedList.length === 0 ? (
                    <div className="empty-state">
                        <p>暂无角色，请先在"角色提取"步骤添加角色</p>
                    </div>
                ) : (
                    <table className="voice-table">
                        <thead>
                            <tr>
                                <th>角色</th>
                                <th>语音设计信息</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            {combinedList.map(({ char, design }) => {
                                const disabled = !char.requires_tts

                                return (
                                    <tr key={char.name} className={disabled ? 'disabled-row' : ''}>
                                        <td>
                                            <div className="font-semibold">{char.name}</div>

                                        </td>
                                        <td>
                                            {disabled ? (
                                                <span className="text-muted text-sm">该角色不需要语音设计</span>
                                            ) : design ? (
                                                <div>
                                                    <div className="text-sm" style={{ marginBottom: 4 }}>
                                                        <strong>语音名:</strong> {design.name}
                                                    </div>
                                                    <div className="tts-preview" style={{ whiteSpace: 'normal', maxWidth: 'none' }}>
                                                        <strong>音色控制指令:</strong>{' '}
                                                        {design.tts_instruction
                                                            ? (design.tts_instruction.length > 80
                                                                ? design.tts_instruction.substring(0, 80) + '...'
                                                                : design.tts_instruction)
                                                            : '未设置'}
                                                    </div>
                                                    <div className="text-xs mt-2" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                                                        <span className={`status-dot ${design.has_reference_audio ? 'generated' : 'not-generated'}`} />
                                                        <span>{design.has_reference_audio ? '参考音频已生成' : '参考音频未生成'}</span>
                                                        {design.has_reference_audio && (
                                                            <button className="btn btn-ghost btn-sm">▶ 播放</button>
                                                        )}
                                                    </div>
                                                </div>
                                            ) : (
                                                <span className="text-muted text-sm">未进行语音设计</span>
                                            )}
                                        </td>
                                        <td>
                                            <button
                                                className="btn btn-secondary btn-sm"
                                                onClick={() => setEditDesign(design || { name: char.voice_name, tts_instruction: '', reference_text: '', has_reference_audio: false })}
                                                disabled={disabled}
                                            >
                                                ✏️ 编辑
                                            </button>
                                        </td>
                                    </tr>
                                )
                            })}
                        </tbody>
                    </table>
                )}
            </div>

            {editDesign && (
                <VoiceEditModal
                    design={editDesign}
                    projectId={projectId}
                    onClose={() => setEditDesign(null)}
                    onSaved={fetchData}
                />
            )}
        </>
    )
}
