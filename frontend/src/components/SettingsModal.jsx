import React, { useState } from 'react'
import { updateProjectSettings } from '../api.js'
import { useToast } from '../App.jsx'

export default function SettingsModal({ projectId, onClose }) {
    const addToast = useToast()
    const [saving, setSaving] = useState(false)

    const [settings, setSettings] = useState({
        split_format: 'line',
        quote_format: 'auto',
        context_window: 10,
        default_duration: 0.2,
        line_break_duration: 0.5,
        sentence_margin_duration: 0.3,
        design_model_path: './workspace/design_model',
        clone_model_path: './workspace/clone_model',
        use_flash_attention: false,
    })

    const handleChange = (key, value) => {
        setSettings(prev => ({ ...prev, [key]: value }))
    }

    const handleSave = async () => {
        try {
            setSaving(true)
            await updateProjectSettings(projectId, settings)
            addToast('设置已保存', 'success')
            onClose()
        } catch (err) {
            addToast('保存设置失败: ' + err.message, 'error')
        } finally {
            setSaving(false)
        }
    }

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 640 }}>
                <div className="modal-header">
                    <h2>⚙️ 项目设置</h2>
                    <button className="btn btn-ghost btn-sm" onClick={onClose}>✕</button>
                </div>
                <div className="modal-body">
                    {/* Text Processing */}
                    <div className="settings-section">
                        <h3>文本处理设置</h3>
                        <div className="settings-grid">
                            <div className="form-group">
                                <label className="form-label">分割方式</label>
                                <select
                                    className="select"
                                    value={settings.split_format}
                                    onChange={e => handleChange('split_format', e.target.value)}
                                >
                                    <option value="line">按行分割</option>
                                    <option value="sentence">按句子分割</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label">引语检测</label>
                                <select
                                    className="select"
                                    value={settings.quote_format}
                                    onChange={e => handleChange('quote_format', e.target.value)}
                                >
                                    <option value="auto">自动检测</option>
                                    <option value="manual">手动标记</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <label className="form-label">上下文窗口大小</label>
                                <input
                                    className="input"
                                    type="number"
                                    min={1}
                                    max={50}
                                    value={settings.context_window}
                                    onChange={e => handleChange('context_window', parseInt(e.target.value) || 10)}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Audio Settings */}
                    <div className="settings-section">
                        <h3>音频设置</h3>
                        <div className="settings-grid">
                            <div className="form-group">
                                <label className="form-label">默认空白时长 (秒)</label>
                                <input
                                    className="input"
                                    type="number"
                                    step="0.1"
                                    min={0}
                                    value={settings.default_duration}
                                    onChange={e => handleChange('default_duration', parseFloat(e.target.value) || 0.2)}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">换行停顿时长 (秒)</label>
                                <input
                                    className="input"
                                    type="number"
                                    step="0.1"
                                    min={0}
                                    value={settings.line_break_duration}
                                    onChange={e => handleChange('line_break_duration', parseFloat(e.target.value) || 0.5)}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">句间停顿时长 (秒)</label>
                                <input
                                    className="input"
                                    type="number"
                                    step="0.1"
                                    min={0}
                                    value={settings.sentence_margin_duration}
                                    onChange={e => handleChange('sentence_margin_duration', parseFloat(e.target.value) || 0.3)}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Model Paths */}
                    <div className="settings-section">
                        <h3>TTS模型路径</h3>
                        <div className="form-group">
                            <label className="form-label">设计模型路径</label>
                            <input
                                className="input"
                                type="text"
                                value={settings.design_model_path}
                                onChange={e => handleChange('design_model_path', e.target.value)}
                            />
                        </div>
                        <div className="form-group">
                            <label className="form-label">克隆模型路径</label>
                            <input
                                className="input"
                                type="text"
                                value={settings.clone_model_path}
                                onChange={e => handleChange('clone_model_path', e.target.value)}
                            />
                        </div>
                        <div className="form-group">
                            <label className="checkbox-group">
                                <input
                                    type="checkbox"
                                    checked={settings.use_flash_attention}
                                    onChange={e => handleChange('use_flash_attention', e.target.checked)}
                                />
                                <span>使用 Flash Attention 加速</span>
                            </label>
                        </div>
                    </div>

                    <p className="text-xs text-muted" style={{ marginTop: 'var(--space-2)' }}>
                        ⚠️ 更改部分设置可能需要重新处理文本或重新生成音频
                    </p>
                </div>
                <div className="modal-footer">
                    <button className="btn btn-ghost" onClick={onClose}>取消</button>
                    <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                        {saving ? '保存中...' : '保存设置'}
                    </button>
                </div>
            </div>
        </div>
    )
}
