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

    const truncateProjectName = (name, maxLength = 35) => {
        if (name.length > maxLength) {
            return name.substring(0, maxLength) + '...'
        }
        return name
    }

    return (
        <>
            <nav className="nav-bar">
                <div className="nav-bar-inner">
                    {/* First Row: Back | Title | Save */}
                    <div className="nav-header-row">
                        <div className="nav-header-left">
                            <button className="btn btn-ghost btn-sm" onClick={handleBack}>
                                ↩ 返回项目列表
                            </button>
                        </div>
                        <div className="nav-header-center">
                            <div className="nav-project-title">
                                《{truncateProjectName(projectName)}》
                            </div>
                        </div>
                        <div className="nav-header-right">
                            <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={saving}>
                                {saving ? '保存中...' : '💾 保存项目'}
                            </button>
                        </div>
                    </div>

                    {/* Second Row: Navigation Steps + Controls Centered */}
                    <div className="nav-controls-row">
                        <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => onStepChange(Math.max(2, currentStep - 1))}
                            disabled={currentStep <= 2}
                        >
                            ◀ 上一步
                        </button>

                        {/* Step Indicators */}
                        <div className="nav-steps">
                            {STEPS.map((step, idx) => (
                                <React.Fragment key={step.num}>
                                    <div
                                        className={`nav-step ${getStepState(step.num)}`}
                                        onClick={() => {
                                            if (step.num === 1) {
                                                handleBack()
                                            } else if (step.num >= 2) {
                                                onStepChange(step.num)
                                            }
                                        }}
                                        style={{ cursor: step.num === 1 || step.num >= 2 ? 'pointer' : 'default' }}
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

                        <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => onStepChange(Math.min(5, currentStep + 1))}
                            disabled={currentStep >= 5}
                        >
                            下一步 ▶
                        </button>
                    </div>
                </div>
            </nav>

        </>
    )
}
