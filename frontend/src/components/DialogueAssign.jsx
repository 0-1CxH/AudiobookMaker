import React, { useState, useEffect, useCallback, useRef } from 'react'
import {
    getDialogues,
    getCharacters,
    allocateDialogues,
    updateDialogue,
} from '../api.js'
import { useToast } from '../App.jsx'

// Color palette for character assignment
const CHAR_COLORS = [
    '#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6',
    '#ec4899', '#06b6d4', '#f97316', '#14b8a6', '#6366f1',
]

function getCharColor(idx) {
    return CHAR_COLORS[idx % CHAR_COLORS.length]
}

export default function DialogueAssign({ projectId }) {
    const addToast = useToast()
    const [segments, setSegments] = useState([])
    const [characters, setCharacters] = useState([])
    const [statistics, setStatistics] = useState({})
    const [loading, setLoading] = useState(true)
    const [allocating, setAllocating] = useState(false)
    const [currentPage, setCurrentPage] = useState(1)
    const [focusedSegmentIndex, setFocusedSegmentIndex] = useState(null)
    const [highlightedSegmentIndex, setHighlightedSegmentIndex] = useState(null)
    const segmentsPerPage = 50
    const highlightTimeoutRef = useRef(null)

    // Popover state
    const [popover, setPopover] = useState(null) // { segmentIndex, x, y }
    const popoverRef = useRef(null)

    // Build character → color map
    const charColorMap = {}
    characters.forEach((c, i) => {
        charColorMap[c.name] = getCharColor(i)
    })

    const fetchData = useCallback(async () => {
        try {
            setLoading(true)
            setCurrentPage(1)
            const [diagRes, charRes] = await Promise.all([
                getDialogues(projectId),
                getCharacters(projectId),
            ])
            setSegments(diagRes.data?.segments || [])
            setStatistics(diagRes.data?.statistics || {})
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

    // Close popover on outside click
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (popoverRef.current && !popoverRef.current.contains(e.target)) {
                setPopover(null)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    // Cleanup highlight timeout on unmount
    useEffect(() => {
        return () => {
            if (highlightTimeoutRef.current) {
                clearTimeout(highlightTimeoutRef.current)
            }
        }
    }, [])

    const handleAllocate = async () => {
        try {
            setAllocating(true)
            addToast('正在AI分配对话...', 'info')
            const res = await allocateDialogues(projectId)
            setSegments(res.data?.segments || [])
            addToast(`已分配 ${res.data?.allocated_count || 0} 条对话`, 'success')
            fetchData()
        } catch (err) {
            addToast('对话分配失败: ' + err.message, 'error')
        } finally {
            setAllocating(false)
        }
    }

    // Helper to check if a segment is unassigned (assignable but not assigned)
    const isUnassigned = (seg) => {
        return seg.tag !== 'DEFAULT' && seg.tag !== 'PLACEHOLDER' && !seg.allocated_speaker
    }

    // Find previous unassigned segment from current index
    const findPrevUnassigned = (currentIndex) => {
        // Find array index of current segment
        let startArrayIdx = -1
        if (currentIndex !== null) {
            startArrayIdx = segments.findIndex(s => s.index === currentIndex)
        }
        // If current not found or no current, start from the end
        let startIdx = startArrayIdx >= 0 ? startArrayIdx - 1 : segments.length - 1
        for (let i = startIdx; i >= 0; i--) {
            if (isUnassigned(segments[i])) {
                return segments[i]
            }
        }
        // Wrap around to the end
        for (let i = segments.length - 1; i > startIdx; i--) {
            if (isUnassigned(segments[i])) {
                return segments[i]
            }
        }
        return null
    }

    // Find next unassigned segment from current index
    const findNextUnassigned = (currentIndex) => {
        // Find array index of current segment
        let startArrayIdx = -1
        if (currentIndex !== null) {
            startArrayIdx = segments.findIndex(s => s.index === currentIndex)
        }
        // If current not found or no current, start from the beginning
        let startIdx = startArrayIdx >= 0 ? startArrayIdx + 1 : 0
        for (let i = startIdx; i < segments.length; i++) {
            if (isUnassigned(segments[i])) {
                return segments[i]
            }
        }
        // Wrap around to the beginning
        for (let i = 0; i < startIdx; i++) {
            if (isUnassigned(segments[i])) {
                return segments[i]
            }
        }
        return null
    }

    // Navigate to previous unassigned segment
    const navigateToPrevUnassigned = () => {
        const prevSeg = findPrevUnassigned(focusedSegmentIndex)
        if (prevSeg) {
            // Find array index of this segment
            const arrayIndex = segments.findIndex(s => s.index === prevSeg.index)
            if (arrayIndex >= 0) {
                // Calculate page containing this segment
                const page = Math.floor(arrayIndex / segmentsPerPage) + 1
                setCurrentPage(page)
                setFocusedSegmentIndex(prevSeg.index)
                // Scroll to element after render
                setTimeout(() => {
                    const elem = document.getElementById(`segment-${prevSeg.index}`)
                    if (elem) {
                        elem.scrollIntoView({ behavior: 'smooth', block: 'center' })
                        elem.focus()
                    }
                }, 100)
            }
        }
    }

    // Navigate to next unassigned segment
    const navigateToNextUnassigned = () => {
        const nextSeg = findNextUnassigned(focusedSegmentIndex)
        if (nextSeg) {
            // Find array index of this segment
            const arrayIndex = segments.findIndex(s => s.index === nextSeg.index)
            if (arrayIndex >= 0) {
                // Calculate page containing this segment
                const page = Math.floor(arrayIndex / segmentsPerPage) + 1
                setCurrentPage(page)
                setFocusedSegmentIndex(nextSeg.index)
                // Scroll to element after render
                setTimeout(() => {
                    const elem = document.getElementById(`segment-${nextSeg.index}`)
                    if (elem) {
                        elem.scrollIntoView({ behavior: 'smooth', block: 'center' })
                        elem.focus()
                    }
                }, 100)
            }
        }
    }

    const handleSegmentFocus = (segmentIndex) => {
        setFocusedSegmentIndex(segmentIndex)
        setHighlightedSegmentIndex(segmentIndex)

        // Clear previous timeout if exists
        if (highlightTimeoutRef.current) {
            clearTimeout(highlightTimeoutRef.current)
        }

        // Set timeout to clear highlight after 2 seconds
        highlightTimeoutRef.current = setTimeout(() => {
            setHighlightedSegmentIndex(null)
        }, 2000)
    }

    const handleSegmentClick = (seg, e) => {
        // 只允许点击非DEFAULT和非PLACEHOLDER的segment（即可分配的segment）
        // DEFAULT和PLACEHOLDER不可分配，不需要点击
        if (seg.tag === 'DEFAULT' || seg.tag === 'PLACEHOLDER') return

        const rect = e.currentTarget.getBoundingClientRect()
        handleSegmentFocus(seg.index)
        e.currentTarget.focus()
        setPopover({
            segmentIndex: seg.index,
            x: rect.left + rect.width / 2,
            y: rect.bottom + 4,
        })
    }

    const handleAssign = async (segmentIndex, speaker) => {
        setPopover(null)
        try {
            await updateDialogue(projectId, segmentIndex, speaker)
            // Update local state
            setSegments(prev => prev.map(s =>
                s.index === segmentIndex ? { ...s, allocated_speaker: speaker } : s
            ))
            addToast(`片段 #${segmentIndex} 已分配给 ${speaker}`, 'success')
        } catch (err) {
            addToast('分配失败: ' + err.message, 'error')
        }
    }

    if (loading) {
        return (
            <div className="loading-spinner">
                <div className="spinner" />
            </div>
        )
    }

    // Count assignments per character
    const assignCounts = {}
    segments.forEach(s => {
        if (s.allocated_speaker) {
            assignCounts[s.allocated_speaker] = (assignCounts[s.allocated_speaker] || 0) + 1
        }
    })

    // Check if there are any unassigned segments
    const hasUnassigned = (statistics.allocated_quotes || 0) < (statistics.total_quotes || 0)

    return (
        <div className="split-layout">
            {/* Left: Text with Assignment */}
            <div className="card">
                <div className="card-header">
                    <span className="card-title">📝 对话分配</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                        <button
                            className="btn btn-ghost btn-xs"
                            onClick={navigateToPrevUnassigned}
                            disabled={!hasUnassigned}
                            title="上一个未分配"
                        >
                            &lt;
                        </button>
                        <span className="text-xs text-muted">
                            {statistics.allocated_quotes || 0}/{statistics.total_quotes || 0} 已分配
                        </span>
                        <button
                            className="btn btn-ghost btn-xs"
                            onClick={navigateToNextUnassigned}
                            disabled={!hasUnassigned}
                            title="下一个未分配"
                        >
                            &gt;
                        </button>
                    </div>
                </div>
                <div style={{ maxHeight: 'calc(100vh - 280px)', overflowY: 'auto', position: 'relative'}}>
                    {(() => {
                        // 计算分页
                        const startIdx = (currentPage - 1) * segmentsPerPage
                        const endIdx = startIdx + segmentsPerPage
                        const paginatedSegments = segments.slice(startIdx, endIdx)

                        return paginatedSegments.map((seg) => {
                            const isPlaceholder = seg.tag === 'PLACEHOLDER'
                            const isDefault = seg.tag === 'DEFAULT'
                            const isNonAssignable = isPlaceholder || isDefault  // 不可分配的segment
                            const isAssignable = !isNonAssignable  // 可分配的segment（包括QUOTE和已分配角色名）
                            const isAssigned = isAssignable && seg.allocated_speaker
                            const speakerColor = isAssigned ? charColorMap[seg.allocated_speaker] : null

                            if (isPlaceholder && (seg.content === '\n' || seg.content.trim() === '')) {
                                return null
                            }

                            let tagClass = 'tag-default'
                            if (isPlaceholder) tagClass = 'tag-placeholder'
                            else if (isDefault) tagClass = 'tag-default'
                            else if (isAssignable && isAssigned) tagClass = 'tag-quote assigned'
                            else if (isAssignable) tagClass = 'tag-quote unassigned'

                            return (
                                <div
                                    key={seg.index}
                                    id={`segment-${seg.index}`}
                                    className={`segment-block ${tagClass}`}
                                    tabIndex={isAssignable ? 0 : -1}
                                    onClick={isAssignable ? (e) => handleSegmentClick(seg, e) : undefined}
                                    onFocus={() => handleSegmentFocus(seg.index)}
                                    style={{
                                        cursor: isAssignable ? 'pointer' : 'default',
                                        color: isNonAssignable ? 'var(--text-muted)' : 'var(--text-primary)',
                                        display: 'block',
                                        width: 'fit-content',
                                        ...(isAssigned && speakerColor
                                            ? {
                                                background: `${speakerColor}15`,
                                                borderLeftColor: speakerColor,
                                            }
                                            : {}),
                                        ...(seg.index === highlightedSegmentIndex
                                            ? {
                                                boxShadow: '0 0 0 2px rgba(255, 204, 0, 0.5)',
                                                backgroundColor: 'rgba(255, 204, 0, 0.1)',
                                                transition: 'box-shadow 0.3s ease, background-color 0.3s ease',
                                            }
                                            : {}),
                                    }}
                                >
                                    <span style={{ opacity: 0.3, fontSize: 'var(--font-size-xs)', marginRight: 8 }}>
                                        #{seg.index}
                                    </span>
                                    {seg.content}
                                    {isAssigned && (
                                        <span
                                            className="segment-label"
                                            style={{
                                                background: `${speakerColor}30`,
                                                color: speakerColor,
                                            }}
                                        >
                                            {seg.allocated_speaker}
                                        </span>
                                    )}
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

            {/* Popover for selecting speaker */}
            {popover && (
                <div
                    ref={popoverRef}
                    className="popover"
                    style={{
                        position: 'fixed',
                        left: Math.min(popover.x - 90, window.innerWidth - 200),
                        top: Math.min(popover.y, window.innerHeight - 300),
                    }}
                >
                    <div className="popover-title">分配说话人</div>
                    {characters.map((char, idx) => (
                        <div
                            key={char.name}
                            className="popover-item"
                            onClick={() => handleAssign(popover.segmentIndex, char.name)}
                        >
                            <span className="color-dot" style={{ background: getCharColor(idx) }} />
                            {char.name}
                        </div>
                    ))}
                </div>
            )}

            {/* Right: Character Panel */}
            <div className="card">
                <div className="card-header">
                    <span className="card-title">👥 角色列表</span>
                </div>

                <button
                    className="btn btn-primary btn-sm w-full mb-4"
                    onClick={handleAllocate}
                    disabled={allocating}
                >
                    {allocating ? '🔄 分配中...' : '🧠 AI对话分配'}
                </button>

                <div style={{ maxHeight: 'calc(100vh - 380px)', overflowY: 'auto' }}>
                    {characters.map((char, idx) => (
                        <div key={char.name} className="character-card">
                            <div className="character-card-header">
                                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                                    <span
                                        className="color-dot"
                                        style={{
                                            width: 14,
                                            height: 14,
                                            borderRadius: '50%',
                                            background: getCharColor(idx),
                                            display: 'inline-block',
                                            flexShrink: 0,
                                        }}
                                    />
                                    <span className="character-name">{char.name}</span>
                                </div>
                            </div>
                            <div className="character-meta">
                                <span>已分配: {assignCounts[char.name] || 0} 段</span>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Legend */}
                <div style={{ marginTop: 'var(--space-4)', padding: 'var(--space-3)', background: 'var(--bg-input)', borderRadius: 'var(--radius-sm)' }}>
                    <div className="text-xs text-muted" style={{ marginBottom: 'var(--space-2)' }}>颜色说明:</div>
                    <div className="text-xs text-muted">
                        <div>🔘 灰色: 旁白/占位符（不可分配）</div>
                        <div>⬜ 透明: 未分配的引语（可点击）</div>
                        <div>🟦 彩色: 已分配的引语</div>
                    </div>
                </div>
            </div>
        </div>
    )
}
