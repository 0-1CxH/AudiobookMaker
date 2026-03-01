import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
    getAudioSegments,
    getAudioProgress,
    generateAudio,
    getAudioStatus,
    regenerateSegment,
    renderAudio,
    getOutputStatus,
    getDownloadUrl,
    getSegmentAudioUrl,
    cancelAudioGeneration,
} from '../api.js'
import { useToast } from '../App.jsx'

// ===== Segment Detail Modal =====
function SegmentDetailModal({ segment, projectId, onClose, onRegenerated }) {
    const addToast = useToast()
    const [regenerating, setRegenerating] = useState(false)
    const [isPlaying, setIsPlaying] = useState(false)
    const audioRef = React.useRef(null)

    const handleRegenerate = async () => {
        try {
            setRegenerating(true)
            await regenerateSegment(projectId, segment.index)
            addToast(`片段 #${segment.index} 正在重新生成`, 'success')
            onRegenerated()
        } catch (err) {
            addToast('重新生成失败: ' + err.message, 'error')
        } finally {
            setRegenerating(false)
        }
    }

    const handlePlayAudio = () => {
        try {
            if (audioRef.current) {
                if (isPlaying) {
                    audioRef.current.pause()
                    setIsPlaying(false)
                } else {
                    const audioUrl = getSegmentAudioUrl(projectId, segment.index)
                    if (audioRef.current.src !== audioUrl) {
                        audioRef.current.src = audioUrl
                    }
                    audioRef.current.play().then(() => {
                        setIsPlaying(true)
                    }).catch(err => {
                        addToast('播放音频失败: ' + err.message, 'error')
                        setIsPlaying(false)
                    })
                }
            }
        } catch (err) {
            addToast('播放音频失败: ' + err.message, 'error')
            setIsPlaying(false)
        }
    }

    React.useEffect(() => {
        return () => {
            if (audioRef.current) {
                audioRef.current.pause()
            }
        }
    }, [])

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 500 }}>
                <div className="modal-header">
                    <h2>片段 #{segment.index} 详细信息</h2>
                    <button className="btn btn-ghost btn-sm" onClick={onClose}>✕</button>
                </div>
                <div className="modal-body">
                    <div className="form-group">
                        <label className="form-label">内容</label>
                        <div style={{
                            background: 'var(--bg-input)',
                            padding: 'var(--space-3)',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: 'var(--font-size-sm)',
                            lineHeight: 1.7,
                        }}>
                            {segment.content}
                        </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
                        <div className="form-group">
                            <label className="form-label">分配角色</label>
                            <div className="text-sm">{segment.allocated_speaker || segment.tag}</div>
                        </div>
                        <div className="form-group">
                            <label className="form-label">生成状态</label>
                            <div className="text-sm" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                                <span className={`status-dot ${segment.has_audio ? 'generated' : 'not-generated'}`} />
                                {segment.has_audio ? '已生成' : '未生成'}
                            </div>
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-4)' }}>
                        {segment.has_audio && (
                            <button
                                className="btn btn-secondary btn-sm"
                                onClick={handlePlayAudio}
                                disabled={regenerating}
                            >
                                {isPlaying ? '⏸ 暂停' : '▶ 播放音频'}
                            </button>
                        )}
                        <button
                            className="btn btn-secondary btn-sm"
                            onClick={handleRegenerate}
                            disabled={regenerating}
                        >
                            {regenerating ? '🔄 重新生成中...' : '🔄 重新生成'}
                        </button>
                    </div>
                </div>
                <div className="modal-footer">
                    <button className="btn btn-ghost" onClick={onClose}>关闭</button>
                </div>
            </div>
            {/* Hidden audio element for playing segment audio */}
            <audio
                ref={audioRef}
                onEnded={() => setIsPlaying(false)}
                onPause={() => setIsPlaying(false)}
                onError={() => {
                    addToast('音频播放失败', 'error')
                    setIsPlaying(false)
                }}
                style={{ display: 'none' }}
            />
        </div>
    )
}

// ===== Render Complete Modal =====
function RenderCompleteModal({ projectId, outputStatus, onClose }) {
    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 440 }}>
                <div className="modal-header">
                    <h2>🎉 渲染完成</h2>
                    <button className="btn btn-ghost btn-sm" onClick={onClose}>✕</button>
                </div>
                <div className="modal-body text-center">
                    <div style={{ fontSize: 48, marginBottom: 'var(--space-4)' }}>✅</div>
                    <p style={{ fontSize: 'var(--font-size-lg)', fontWeight: 600, marginBottom: 'var(--space-4)' }}>
                        最终音频文件已生成！
                    </p>
                    {outputStatus?.file_info && (
                        <div className="text-sm text-muted" style={{ marginBottom: 'var(--space-4)' }}>
                            <div>文件大小: {(outputStatus.file_info.size / (1024 * 1024)).toFixed(1)} MB</div>
                        </div>
                    )}
                    <a
                        href={getDownloadUrl(projectId)}
                        className="btn btn-primary btn-lg"
                        download
                        style={{ textDecoration: 'none' }}
                    >
                        📥 下载文件
                    </a>
                </div>
                <div className="modal-footer">
                    <button className="btn btn-ghost" onClick={onClose}>关闭</button>
                </div>
            </div>
        </div>
    )
}

// ===== Main Component =====
export default function AudioGenerate({ projectId }) {
    const addToast = useToast()
    const [segments, setSegments] = useState([])
    const [progress, setProgress] = useState({ generated_count: 0, total_count: 0, progress_percentage: 0 })
    const [loading, setLoading] = useState(true)
    const [generating, setGenerating] = useState(false)
    const [rendering, setRendering] = useState(false)
    const [taskId, setTaskId] = useState(null)
    const [selectedSegment, setSelectedSegment] = useState(null)
    const [showRenderComplete, setShowRenderComplete] = useState(false)
    const [outputStatus, setOutputStatus] = useState(null)
    const [playingSegment, setPlayingSegment] = useState(null)
    const [currentPage, setCurrentPage] = useState(1)
    const [pageSize] = useState(20)
    const pollRef = useRef(null)
    const audioRef = useRef(null)

    const fetchData = useCallback(async () => {
        try {
            setLoading(true)
            const [segRes, progRes] = await Promise.all([
                getAudioSegments(projectId),
                getAudioProgress(projectId),
            ])
            const newSegments = segRes.data?.segments || []
            setSegments(newSegments)
            setProgress(progRes.data || { generated_count: 0, total_count: 0, progress_percentage: 0 })

            // 自动跳转到最后一个已生成片段所在页码（仅在初始加载时）
            if (newSegments.length > 0) {
                const lastGeneratedIndex = newSegments.reduce((lastIdx, seg, idx) => {
                    return seg.has_audio ? idx : lastIdx
                }, -1)

                if (lastGeneratedIndex >= 0) {
                    const targetPage = Math.ceil((lastGeneratedIndex + 1) / pageSize)
                    setCurrentPage(targetPage)
                }
            }
        } catch (err) {
            addToast('加载数据失败: ' + err.message, 'error')
        } finally {
            setLoading(false)
        }
    }, [projectId, pageSize])

    const refreshSegments = useCallback(async () => {
        try {
            const segRes = await getAudioSegments(projectId)
            const newSegments = segRes.data?.segments || []
            setSegments(newSegments)

            // 自动跳转到最后一个已生成片段所在页码
            if (newSegments.length > 0) {
                const lastGeneratedIndex = newSegments.reduce((lastIdx, seg, idx) => {
                    return seg.has_audio ? idx : lastIdx
                }, -1)

                if (lastGeneratedIndex >= 0) {
                    const targetPage = Math.ceil((lastGeneratedIndex + 1) / pageSize)
                    setCurrentPage(targetPage)
                }
            }
        } catch (err) {
            console.error('Failed to refresh segments:', err)
        }
    }, [projectId, pageSize])

    const handlePlaySegmentAudio = (segmentIndex) => {
        try {
            if (playingSegment === segmentIndex) {
                // Stop playing
                if (audioRef.current) {
                    audioRef.current.pause()
                }
                setPlayingSegment(null)
            } else {
                // Stop any currently playing audio
                if (audioRef.current) {
                    audioRef.current.pause()
                }

                const audioUrl = getSegmentAudioUrl(projectId, segmentIndex)
                if (audioRef.current) {
                    audioRef.current.src = audioUrl
                    audioRef.current.play().then(() => {
                        setPlayingSegment(segmentIndex)
                    }).catch(err => {
                        addToast('播放音频失败: ' + err.message, 'error')
                        setPlayingSegment(null)
                    })
                }
            }
        } catch (err) {
            addToast('播放音频失败: ' + err.message, 'error')
            setPlayingSegment(null)
        }
    }

    React.useEffect(() => {
        return () => {
            if (audioRef.current) {
                audioRef.current.pause()
            }
        }
    }, [])

    useEffect(() => {
        fetchData()
        return () => {
            if (pollRef.current) clearInterval(pollRef.current)
        }
    }, [fetchData])

    // Poll task status
    useEffect(() => {
        if (!taskId) return

        pollRef.current = setInterval(async () => {
            try {
                const res = await getAudioStatus(projectId, taskId)
                const status = res.data?.status

                if (status === 'completed') {
                    clearInterval(pollRef.current)
                    pollRef.current = null
                    setTaskId(null)
                    setGenerating(false)
                    addToast('音频生成完成！', 'success')
                    fetchData()
                } else if (status === 'failed') {
                    clearInterval(pollRef.current)
                    pollRef.current = null
                    setTaskId(null)
                    setGenerating(false)
                    addToast('音频生成失败: ' + (res.data?.message || '未知错误'), 'error')
                    fetchData()
                } else if (status === 'cancelled') {
                    clearInterval(pollRef.current)
                    pollRef.current = null
                    setTaskId(null)
                    setGenerating(false)
                    addToast('音频生成已取消', 'info')
                    fetchData()
                } else {
                    // Update progress with real-time data
                    const total = res.data?.progress?.total_count || 0
                    const processed = res.data?.progress?.generated_count || 0
                    const progressPct = res.data?.progress?.percentage || 0
                    const message = res.data?.message

                    // Update progress state
                    setProgress(prev => ({
                        ...prev,
                        generated_count: processed,
                        total_count: total,
                        progress_percentage: progressPct
                    }))

                    // Log progress for debugging
                    console.log(`Audio generation progress: ${processed}/${total} (${progressPct}%) - ${message || ''}`)

                    // Refresh segments list to show updated status
                    refreshSegments()
                }
            } catch (err) {
                console.error('Error polling audio status:', err)
                // Don't stop polling on occasional errors, but log them
            }
        }, 5000)

        return () => {
            if (pollRef.current) clearInterval(pollRef.current)
        }
    }, [taskId, projectId, refreshSegments])

    // 确保当前页码始终有效（当segments变化时）
    useEffect(() => {
        if (segments.length > 0) {
            const totalPages = Math.ceil(segments.length / pageSize)
            if (currentPage > totalPages) {
                setCurrentPage(totalPages)
            }
        } else {
            setCurrentPage(1)
        }
    }, [segments, currentPage, pageSize])

    const handleGenerate = async () => {
        try {
            setGenerating(true)
            addToast('正在生成音频...', 'info')
            const res = await generateAudio(projectId)
            if (res.data?.task_id) {
                setTaskId(res.data.task_id)
            } else {
                // Synchronous completion
                setGenerating(false)
                addToast('音频生成完成', 'success')
                fetchData()
            }
        } catch (err) {
            setGenerating(false)
            addToast('音频生成失败: ' + err.message, 'error')
        }
    }

    const handleCancel = async () => {
        try {
            if (!taskId) {
                addToast('没有正在运行的任务可取消', 'warning')
                return
            }

            addToast('正在取消音频生成...', 'info')
            await cancelAudioGeneration(projectId, taskId)

            // 清除轮询
            if (pollRef.current) {
                clearInterval(pollRef.current)
                pollRef.current = null
            }

            // 重置状态
            setTaskId(null)
            setGenerating(false)
            addToast('音频生成已取消', 'success')

            // 刷新数据以显示当前状态
            fetchData()
        } catch (err) {
            addToast('取消失败: ' + err.message, 'error')
        }
    }

    const handleRender = async () => {
        try {
            setRendering(true)
            addToast('正在渲染最终音频...', 'info')
            await renderAudio(projectId)
            const statusRes = await getOutputStatus(projectId)
            setOutputStatus(statusRes.data)
            setShowRenderComplete(true)
            addToast('最终音频渲染完成！', 'success')
        } catch (err) {
            addToast('渲染失败: ' + err.message, 'error')
        } finally {
            setRendering(false)
        }
    }

    const pct = progress.progress_percentage || 0
    const isComplete = pct >= 100 || (progress.generated_count > 0 && progress.generated_count === progress.total_count)

    // 分页相关计算
    const totalPages = Math.ceil(segments.length / pageSize)
    const startIdx = (currentPage - 1) * pageSize
    const endIdx = Math.min(startIdx + pageSize, segments.length)
    const currentPageSegments = segments.slice(startIdx, endIdx)


    if (loading) {
        return (
            <div className="loading-spinner">
                <div className="spinner" />
            </div>
        )
    }

    return (
        <>
            <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
                <div className="card-header">
                    <span className="card-title">🎵 音频生成</span>
                </div>

                {/* Progress Bar */}
                <div style={{ marginBottom: 'var(--space-5)' }}>
                    <div className="progress-bar-container">
                        <div
                            className="progress-bar-fill"
                            style={{ width: `${isComplete ? 100 : pct}%` }}
                        />
                    </div>
                    <div className="progress-info">
                        <span>{progress.generated_count}/{progress.total_count} 片段已生成</span>
                        <span>{isComplete ? 100 : Math.round(pct)}%</span>
                    </div>
                </div>

                {/* Action Buttons */}
                <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
                    <button
                        className="btn btn-primary"
                        onClick={handleGenerate}
                        disabled={generating}
                    >
                        {generating ? '🔄 生成中...' : '🔊 AI音频生成'}
                    </button>
                    {generating && (
                        <button
                            className="btn btn-warning"
                            onClick={handleCancel}
                            disabled={!taskId}
                        >
                            ⏹️ 停止生成
                        </button>
                    )}
                    <button
                        className="btn btn-success"
                        onClick={handleRender}
                        disabled={rendering || !isComplete}
                    >
                        {rendering ? '🔄 渲染中...' : '🎬 渲染最终音频'}
                    </button>
                    {!isComplete && (
                        <span className="text-xs text-muted" style={{ alignSelf: 'center' }}>
                            进度达到100%后可渲染最终音频
                        </span>
                    )}
                </div>
            </div>

            {/* Segments List */}
            <div className="card">
                <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="card-title">📋 文本片段状态</span>
                    {totalPages > 1 && (
                        <div className="pagination-container" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
                            <div className="pagination-info text-sm text-muted">
                                第 {currentPage}/{totalPages} 页，共 {segments.length} 个片段
                            </div>
                            <div className="pagination-controls" style={{ display: 'flex', gap: 'var(--space-2)' }}>
                                <button
                                    className="btn btn-ghost btn-sm"
                                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                                    disabled={currentPage === 1}
                                >
                                    上一页
                                </button>
                                <button
                                    className="btn btn-ghost btn-sm"
                                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                                    disabled={currentPage === totalPages}
                                >
                                    下一页
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                <div className="audio-segments-list">
                    {currentPageSegments.map((seg) => {
                        const isGenerated = seg.has_audio

                        return (
                            <div
                                key={seg.index}
                                className={`audio-segment-item ${isGenerated ? 'generated' : 'not-generated'}`}
                                onClick={() => setSelectedSegment(seg)}
                            >
                                <span className="text-xs" style={{ opacity: 0.5 }}>#{seg.index}</span>
                                <span className="truncate">
                                    {seg.content.length > 50 ? seg.content.substring(0, 50) + '...' : seg.content}
                                </span>
                                <span className="text-xs">{seg.allocated_speaker || seg.tag}</span>
                                <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                                    <span className={`status-dot ${isGenerated ? 'generated' : 'not-generated'}`} />
                                    <span className="text-xs">{isGenerated ? '已生成' : '未生成'}</span>
                                </span>
                                <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                                    {isGenerated && (
                                        <button
                                            className="btn btn-ghost btn-sm"
                                            onClick={(e) => {
                                                e.stopPropagation()
                                                handlePlaySegmentAudio(seg.index)
                                            }}
                                        >
                                            {playingSegment === seg.index ? '⏸' : '▶'}
                                        </button>
                                    )}
                                    <button
                                        className="btn btn-ghost btn-sm"
                                        onClick={async (e) => {
                                            e.stopPropagation()
                                            try {
                                                await regenerateSegment(projectId, seg.index)
                                                addToast(`片段 #${seg.index} 正在重新生成`, 'info')
                                                setTimeout(fetchData, 2000)
                                            } catch (err) {
                                                addToast('重新生成失败: ' + err.message, 'error')
                                            }
                                        }}
                                    >
                                        🔄
                                    </button>
                                </div>
                            </div>
                        )
                    })}
                </div>

                {/* Legend */}
                <div className="text-xs text-muted mt-4" style={{ display: 'flex', gap: 'var(--space-4)' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <span className="status-dot generated" /> 已生成（黑色文字）
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <span className="status-dot not-generated" /> 未生成（灰色文字）
                    </span>
                </div>

            </div>

            {/* Segment Detail Modal */}
            {selectedSegment && (
                <SegmentDetailModal
                    segment={selectedSegment}
                    projectId={projectId}
                    onClose={() => setSelectedSegment(null)}
                    onRegenerated={() => {
                        setSelectedSegment(null)
                        setTimeout(fetchData, 2000)
                    }}
                />
            )}

            {/* Render Complete Modal */}
            {showRenderComplete && (
                <RenderCompleteModal
                    projectId={projectId}
                    outputStatus={outputStatus}
                    onClose={() => setShowRenderComplete(false)}
                />
            )}

            {/* Hidden audio element for playing segment audio in list */}
            <audio
                ref={audioRef}
                onEnded={() => setPlayingSegment(null)}
                onPause={() => setPlayingSegment(null)}
                onError={() => {
                    addToast('音频播放失败', 'error')
                    setPlayingSegment(null)
                }}
                style={{ display: 'none' }}
            />
        </>
    )
}
