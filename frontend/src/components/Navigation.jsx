import React, { useState } from 'react'
import { saveProject } from '../api.js'
import { useToast } from '../App.jsx'

const STEPS = [
    { num: 1, label: '项目选择', completed: true },
    { num: 2, label: '角色提取' },
    { num: 3, label: '对话分配' },
    { num: 4, label: '语音设计' },
    { num: 5, label: '音频生成' },
]

export default function Navigation({ projectName, projectId, currentStep, onStepChange, onBack }) {
    const addToast = useToast()
    const [saving, setSaving] = useState(false)

    const handleSave = async () => {
        try {
            setSaving(true)
            await saveProject(projectId)
            addToast('项目已保存', 'success')
        } catch (err) {
            addToast('保存失败: ' + err.message, 'error')
        } finally {
            setSaving(false)
        }
    }

    const handleBack = () => {
        if (confirm('返回项目列表？当前修改将在后端自动保存。')) {
            onBack()
        }
    }

    const getStepState = (stepNum) => {
        if (stepNum < currentStep) return 'completed'
        if (stepNum === currentStep) return 'active'
        return ''
    }

    return (
        <>
            <nav className="nav-bar">
                <div className="nav-bar-inner">
                    {/* Project Title */}
                    <div className="nav-project-title">
                        📖 项目: {projectName}
                    </div>

                    {/* Step Indicators */}
                    <div className="nav-steps">
                        {STEPS.map((step, idx) => (
                            <React.Fragment key={step.num}>
                                <div
                                    className={`nav-step ${getStepState(step.num)}`}
                                    onClick={() => step.num >= 2 && onStepChange(step.num)}
                                    style={{ cursor: step.num >= 2 ? 'pointer' : 'default' }}
                                >
                                    <span className="nav-step-icon">
                                        {getStepState(step.num) === 'completed' ? '✓' : step.num}
                                    </span>
                                    <span className="nav-step-label">{step.label}</span>
                                </div>
                                {idx < STEPS.length - 1 && <span className="nav-step-arrow">→</span>}
                            </React.Fragment>
                        ))}
                    </div>

                    {/* Action Buttons */}
                    <div className="nav-actions">
                        <button className="btn btn-secondary btn-sm" onClick={handleSave} disabled={saving}>
                            {saving ? '保存中...' : '💾 保存项目'}
                        </button>
                        <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => onStepChange(Math.max(2, currentStep - 1))}
                            disabled={currentStep <= 2}
                        >
                            ◀ 上一步
                        </button>
                        <button
                            className="btn btn-primary btn-sm"
                            onClick={() => onStepChange(Math.min(5, currentStep + 1))}
                            disabled={currentStep >= 5}
                        >
                            下一步 ▶
                        </button>
                        <button className="btn btn-ghost btn-sm" onClick={handleBack}>
                            ↩ 返回项目列表
                        </button>
                    </div>
                </div>
            </nav>

        </>
    )
}
