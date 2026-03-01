import React, { useState, useCallback, createContext, useContext } from 'react'
import ProjectList from './components/ProjectList.jsx'
import Navigation from './components/Navigation.jsx'
import CharacterExtract from './components/CharacterExtract.jsx'
import DialogueAssign from './components/DialogueAssign.jsx'
import VoiceDesign from './components/VoiceDesign.jsx'
import AudioGenerate from './components/AudioGenerate.jsx'
import Toast from './components/Toast.jsx'

// ===== Toast Context =====
const ToastContext = createContext()

export function useToast() {
    return useContext(ToastContext)
}

function ToastProvider({ children }) {
    const [toasts, setToasts] = useState([])

    const addToast = useCallback((message, type = 'info') => {
        const id = Date.now() + Math.random()
        setToasts(prev => [...prev, { id, message, type }])
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id))
        }, 4000)
    }, [])

    const removeToast = useCallback((id) => {
        setToasts(prev => prev.filter(t => t.id !== id))
    }, [])

    return (
        <ToastContext.Provider value={addToast}>
            {children}
            <div className="toast-container">
                {toasts.map(t => (
                    <Toast key={t.id} message={t.message} type={t.type} onClose={() => removeToast(t.id)} />
                ))}
            </div>
        </ToastContext.Provider>
    )
}

// ===== Main App =====
export default function App() {
    // State to manage navigation
    const [currentPage, setCurrentPage] = useState('projects') // 'projects' | 'workflow'
    const [projectId, setProjectId] = useState(null)
    const [projectName, setProjectName] = useState('')
    const [currentStep, setCurrentStep] = useState(2) // 2-5 for workflow steps

    const handleProjectSelect = useCallback((id, name) => {
        setProjectId(id)
        setProjectName(name)
        setCurrentStep(2)
        setCurrentPage('workflow')
    }, [])

    const handleBackToProjects = useCallback(() => {
        setCurrentPage('projects')
        setProjectId(null)
        setProjectName('')
    }, [])

    const handleStepChange = useCallback((step) => {
        if (step >= 2 && step <= 5) {
            setCurrentStep(step)
        }
    }, [])

    const renderWorkflowPage = () => {
        switch (currentStep) {
            case 2:
                return <CharacterExtract projectId={projectId} />
            case 3:
                return <DialogueAssign projectId={projectId} />
            case 4:
                return <VoiceDesign projectId={projectId} />
            case 5:
                return <AudioGenerate projectId={projectId} />
            default:
                return <CharacterExtract projectId={projectId} />
        }
    }

    return (
        <ToastProvider>
            {currentPage === 'projects' ? (
                <ProjectList onSelectProject={handleProjectSelect} />
            ) : (
                <>
                    <Navigation
                        projectName={projectName}
                        projectId={projectId}
                        currentStep={currentStep}
                        onStepChange={handleStepChange}
                        onBack={handleBackToProjects}
                    />
                    <div className="page-container">
                        {renderWorkflowPage()}
                    </div>
                </>
            )}
        </ToastProvider>
    )
}
