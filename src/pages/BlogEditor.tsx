import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
    FileText, Loader2, CheckCircle, XCircle, MessageSquare, 
    Send, Edit2, Save, X, Plus, ChevronLeft, AlertCircle 
} from 'lucide-react';
import { BlogDocumentService, BlogDocumentWithVersions, BlogFeedback } from '../services/blogDocumentApi';
import { TaskService, Task, AgentService } from '../services/api';
import ReactMarkdown from 'react-markdown';

const BlogEditor = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState<BlogDocumentWithVersions | null>(null);
    const [generatingOutline, setGeneratingOutline] = useState(false);
    const [generatingDraft, setGeneratingDraft] = useState(false);
    const generatingOutlineRef = useRef(false);
    const generatingDraftRef = useRef(false);
    const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);
    const [feedbackOpen, setFeedbackOpen] = useState(false);
    const [newFeedback, setNewFeedback] = useState({ scope: 'global' as 'global' | 'section', comment: '', sectionId: '' });
    const [selectedSectionForFeedback, setSelectedSectionForFeedback] = useState<string | null>(null);
    const [editingSection, setEditingSection] = useState<string | null>(null);
    const [sectionEditValue, setSectionEditValue] = useState('');
    const [useRAG, setUseRAG] = useState(true);
    const prevDataRef = useRef<BlogDocumentWithVersions | null>(null);

    const checkInProgressTasks = useCallback(async (documentId: string) => {
        try {
            // Get blog agent ID
            const agents = await AgentService.getAll();
            const blogAgent = agents.find(a => a.type === 'blog');
            if (!blogAgent) return;

            // Check for pending/processing tasks for this document
            const { tasks: processingTasks } = await TaskService.getAll({
                agentId: blogAgent.id,
                status: 'processing',
                limit: 20
            });

            // Also check pending tasks
            const { tasks: pendingTasks } = await TaskService.getAll({
                agentId: blogAgent.id,
                status: 'pending',
                limit: 20
            });

            const allTasks = [...processingTasks, ...pendingTasks];
            let foundOutlineTask = false;
            let foundDraftTask = false;

            // Check if there's a task for this document
            for (const task of allTasks) {
                if (task.action === 'generate_outline_v2' || task.action === 'generate_draft_v2') {
                    const taskInput = task.input as any;
                    if (taskInput?.document_id === documentId) {
                        if (task.action === 'generate_outline_v2' && (task.status === 'pending' || task.status === 'processing')) {
                            foundOutlineTask = true;
                            if (!generatingOutlineRef.current) {
                                generatingOutlineRef.current = true;
                                setGeneratingOutline(true);
                                setStatusMessage({ type: 'info', message: 'Generating outline... This may take a moment.' });
                            }
                        }
                        if (task.action === 'generate_draft_v2' && (task.status === 'pending' || task.status === 'processing')) {
                            foundDraftTask = true;
                            if (!generatingDraftRef.current) {
                                generatingDraftRef.current = true;
                                setGeneratingDraft(true);
                                setStatusMessage({ type: 'info', message: 'Generating draft... This may take a moment.' });
                            }
                        }
                    }
                }
            }

            // If we expected a task but didn't find it, check if output exists via ref
            const currentData = prevDataRef.current;
            if (!foundOutlineTask && currentData?.outline) {
                // Outline exists, so generation completed
                generatingOutlineRef.current = false;
                setGeneratingOutline(false);
            }
            if (!foundDraftTask && currentData?.draft) {
                // Draft exists, so generation completed
                generatingDraftRef.current = false;
                setGeneratingDraft(false);
            }
        } catch (err) {
            console.error('Failed to check in-progress tasks:', err);
            // Don't show error to user, just log it
        }
    }, []); // No dependencies - use refs and functional updates

    const fetchDocument = useCallback(async (isInitialLoad = false) => {
        if (!id) return;
        try {
            // Only set loading on initial load, not on polls
            if (isInitialLoad) {
                setLoading(true);
                // Check for in-progress tasks when loading for the first time
                await checkInProgressTasks(id);
            }
            const doc = await BlogDocumentService.getById(id);
            const prevData = prevDataRef.current;
            prevDataRef.current = doc;
            setData(doc);
            
            // Clear generating states when outline/draft appears
            if (isInitialLoad) {
                setLoading(false);
            } else {
                // On polling: check if generation completed
                if (generatingOutlineRef.current && doc.outline && (!prevData?.outline || prevData.outline.id !== doc.outline.id)) {
                    generatingOutlineRef.current = false;
                    setGeneratingOutline(false);
                    setStatusMessage({ type: 'success', message: 'Outline generated successfully!' });
                    setTimeout(() => setStatusMessage(null), 3000);
                }
                if (generatingDraftRef.current && doc.draft && (!prevData?.draft || prevData.draft.id !== doc.draft.id)) {
                    generatingDraftRef.current = false;
                    setGeneratingDraft(false);
                    setStatusMessage({ type: 'success', message: 'Draft generated successfully!' });
                    setTimeout(() => setStatusMessage(null), 3000);
                }
            }
        } catch (err) {
            console.error('Failed to fetch document:', err);
            if (generatingOutlineRef.current) {
                generatingOutlineRef.current = false;
                setGeneratingOutline(false);
                setStatusMessage({ type: 'error', message: 'Failed to generate outline' });
                setTimeout(() => setStatusMessage(null), 5000);
            }
            if (generatingDraftRef.current) {
                generatingDraftRef.current = false;
                setGeneratingDraft(false);
                setStatusMessage({ type: 'error', message: 'Failed to generate draft' });
                setTimeout(() => setStatusMessage(null), 5000);
            }
        } finally {
            if (isInitialLoad) {
                setLoading(false);
            }
        }
    }, [id, checkInProgressTasks]); // Removed generatingOutline/generatingDraft from deps

    useEffect(() => {
        if (!id) return;
        
        let isMounted = true;
        let documentInterval: NodeJS.Timeout | null = null;
        let taskCheckInterval: NodeJS.Timeout | null = null;
        
        // Initial load with loading state
        fetchDocument(true);
        
        // Poll for updates without loading state (silent refresh)
        documentInterval = setInterval(async () => {
            if (isMounted) {
                await fetchDocument(false);
            }
        }, 5000); // Poll document every 5 seconds
        
        // Separate interval for checking task status (less frequent, only when generating)
        taskCheckInterval = setInterval(async () => {
            if (isMounted && id) {
                // Only check if we think something is generating (to reduce API calls)
                const currentData = prevDataRef.current;
                const shouldCheck = 
                    (!currentData?.outline && generatingOutlineRef.current) ||
                    (!currentData?.draft && generatingDraftRef.current);
                
                if (shouldCheck) {
                    await checkInProgressTasks(id);
                }
            }
        }, 10000); // Check tasks every 10 seconds
        
        return () => {
            isMounted = false;
            if (documentInterval) clearInterval(documentInterval);
            if (taskCheckInterval) clearInterval(taskCheckInterval);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [id]); // Only depend on id - fetchDocument and checkInProgressTasks are stable callbacks

    const handleGenerateOutline = async () => {
        if (!id || generatingOutline) return; // Prevent duplicate clicks
        try {
            generatingOutlineRef.current = true;
            setGeneratingOutline(true);
            setStatusMessage({ type: 'info', message: 'Generating outline... This may take a moment.' });
            await BlogDocumentService.generateOutline(id, { useRAG });
            // Poll for completion - fetchDocument will detect when outline appears
            setTimeout(() => fetchDocument(false), 2000);
        } catch (err) {
            console.error('Failed to generate outline:', err);
            generatingOutlineRef.current = false;
            setGeneratingOutline(false);
            setStatusMessage({ type: 'error', message: 'Failed to generate outline. Please try again.' });
            setTimeout(() => setStatusMessage(null), 5000);
        }
    };

    const handleApproveOutline = async () => {
        if (!id || !data?.outline) return;
        try {
            await BlogDocumentService.updateOutlineStatus(id, data.outline.id, 'approved');
            fetchDocument();
        } catch (err) {
            console.error('Failed to approve outline:', err);
            alert('Failed to approve outline');
        }
    };

    const handleGenerateDraft = async () => {
        if (!id || generatingDraft) return; // Prevent duplicate clicks
        try {
            generatingDraftRef.current = true;
            setGeneratingDraft(true);
            setStatusMessage({ type: 'info', message: 'Generating draft... This may take a moment.' });
            await BlogDocumentService.generateDraft(id, { useRAG });
            // Poll for completion - fetchDocument will detect when draft appears
            setTimeout(() => fetchDocument(false), 2000);
        } catch (err) {
            console.error('Failed to generate draft:', err);
            generatingDraftRef.current = false;
            setGeneratingDraft(false);
            setStatusMessage({ type: 'error', message: 'Failed to generate draft. Please try again.' });
            setTimeout(() => setStatusMessage(null), 5000);
        }
    };

    const handleAddFeedback = async () => {
        if (!id || !newFeedback.comment.trim()) return;
        if (!data?.outline && !data?.draft) return;

        const targetVersionId = data.outline?.id || data.draft?.id;
        if (!targetVersionId) return;

        try {
            const targetType = data.outline ? 'outline' : 'draft';
            await BlogDocumentService.addFeedback(id, {
                targetType,
                targetVersionId,
                scope: newFeedback.scope,
                targetSectionId: newFeedback.scope === 'section' ? newFeedback.sectionId : undefined,
                comment: newFeedback.comment,
            });
            setNewFeedback({ scope: 'global', comment: '', sectionId: '' });
            setSelectedSectionForFeedback(null);
            setFeedbackOpen(false);
            setStatusMessage({ type: 'success', message: 'Feedback added successfully!' });
            setTimeout(() => setStatusMessage(null), 3000);
            fetchDocument();
        } catch (err) {
            console.error('Failed to add feedback:', err);
            setStatusMessage({ type: 'error', message: 'Failed to add feedback. Please try again.' });
            setTimeout(() => setStatusMessage(null), 5000);
        }
    };

    const handleEditSection = (sectionIndex: number, subsectionIndex?: number) => {
        if (!data?.outline) return;
        const section = data.outline.structure.outline[sectionIndex];
        const target = subsectionIndex !== undefined 
            ? section.subsections?.[subsectionIndex]
            : section;
        
        if (target) {
            const key = subsectionIndex !== undefined 
                ? `section-${sectionIndex}-subsection-${subsectionIndex}`
                : `section-${sectionIndex}`;
            setEditingSection(key);
            setSectionEditValue(target.heading);
        }
    };

    const handleSaveSection = async () => {
        if (!data?.outline || !editingSection || !id) return;
        
        const [type, sectionIdx, subType, subIdx] = editingSection.split('-');
        const sectionIndex = parseInt(sectionIdx);
        const isSubsection = subType === 'subsection';
        const subsectionIndex = isSubsection ? parseInt(subIdx) : undefined;
        
        // Create updated structure
        const updatedStructure = JSON.parse(JSON.stringify(data.outline.structure));
        
        if (isSubsection && subsectionIndex !== undefined) {
            // Update subsection heading
            if (updatedStructure.outline[sectionIndex]?.subsections?.[subsectionIndex]) {
                updatedStructure.outline[sectionIndex].subsections[subsectionIndex].heading = sectionEditValue;
            }
        } else {
            // Update section heading
            if (updatedStructure.outline[sectionIndex]) {
                updatedStructure.outline[sectionIndex].heading = sectionEditValue;
            }
        }
        
        try {
            await BlogDocumentService.updateOutlineStructure(id, data.outline.id, updatedStructure);
            setEditingSection(null);
            setStatusMessage({ type: 'success', message: 'Heading updated successfully!' });
            setTimeout(() => setStatusMessage(null), 3000);
            fetchDocument(); // Refresh to get latest
        } catch (err) {
            console.error('Failed to save heading:', err);
            setStatusMessage({ type: 'error', message: 'Failed to save heading. Please try again.' });
            setTimeout(() => setStatusMessage(null), 5000);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
        );
    }

    if (!data) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                    <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                    <p className="text-gray-400">Document not found</p>
                    <button
                        onClick={() => navigate('/blog')}
                        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                        Back to Blog Agent
                    </button>
                </div>
            </div>
        );
    }

    const { document, outline, draft, outlineFeedback, draftFeedback } = data;
    const canGenerateDraft = outline?.status === 'approved';

    return (
        <div className="h-full flex flex-col min-h-0">
            {/* Toolbar */}
            <div className="bg-gray-900 border border-gray-800 p-4 rounded-xl shrink-0">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => navigate('/blog')}
                            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                        >
                            <ChevronLeft className="w-5 h-5 text-gray-400" />
                        </button>
                        <div>
                            <div className="text-lg font-semibold text-white">{document.topic}</div>
                            <div className="flex items-center gap-2 mt-1">
                                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400">
                                    {document.brand}
                                </span>
                                <span className="text-xs text-gray-500">{document.targetAudience}</span>
                                <span className="text-xs text-gray-500">•</span>
                                <span className="text-xs text-gray-500">{document.intent}</span>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <label className="flex items-center gap-2 text-sm text-gray-400">
                            <input
                                type="checkbox"
                                checked={useRAG}
                                onChange={(e) => setUseRAG(e.target.checked)}
                                className="w-4 h-4 rounded border-gray-700 bg-gray-800 text-blue-600"
                            />
                            Use RAG
                        </label>
                    </div>
                </div>
                {/* Status Message */}
                {statusMessage && (
                    <div className={`mt-3 px-4 py-2 rounded-lg flex items-center gap-2 ${
                        statusMessage.type === 'success' ? 'bg-green-500/10 border border-green-500/20 text-green-400' :
                        statusMessage.type === 'error' ? 'bg-red-500/10 border border-red-500/20 text-red-400' :
                        'bg-blue-500/10 border border-blue-500/20 text-blue-400'
                    }`}>
                        {statusMessage.type === 'info' && <Loader2 className="w-4 h-4 animate-spin" />}
                        {statusMessage.type === 'success' && <CheckCircle className="w-4 h-4" />}
                        {statusMessage.type === 'error' && <XCircle className="w-4 h-4" />}
                        <span className="text-sm">{statusMessage.message}</span>
                        <button
                            onClick={() => setStatusMessage(null)}
                            className="ml-auto p-1 hover:bg-gray-800/50 rounded"
                        >
                            <X className="w-3 h-3" />
                        </button>
                    </div>
                )}
            </div>

            {/* Main Content - Split Pane */}
            <div className="flex-1 flex overflow-hidden min-h-0 mt-4">
                {/* Left Panel - Outline */}
                <div className="w-1/2 border-r border-gray-800 flex flex-col">
                    <div className="bg-gray-900 border-b border-gray-800 p-4 shrink-0">
                        <div className="flex items-center justify-between">
                            <h2 className="text-lg font-bold text-white">Outline</h2>
                            <div className="flex items-center gap-2">
                                {outline && (
                                    <span className={`text-xs px-2 py-1 rounded-full ${
                                        outline.status === 'approved' ? 'bg-green-500/10 text-green-400' :
                                        outline.status === 'reviewed' ? 'bg-yellow-500/10 text-yellow-400' :
                                        'bg-gray-500/10 text-gray-400'
                                    }`}>
                                        {outline.status}
                                    </span>
                                )}
                                {!outline && (
                                    <button
                                        onClick={handleGenerateOutline}
                                        disabled={generatingOutline}
                                        className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-all"
                                    >
                                        {generatingOutline ? (
                                            <>
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                                Generating...
                                            </>
                                        ) : (
                                            <>
                                                <Plus className="w-4 h-4" />
                                                Generate Outline
                                            </>
                                        )}
                                    </button>
                                )}
                                {outline && outline.status !== 'approved' && (
                                    <>
                                        <button
                                            onClick={() => {
                                                setSelectedSectionForFeedback(null);
                                                setNewFeedback({ scope: 'global', comment: '', sectionId: '' });
                                                setFeedbackOpen(true);
                                            }}
                                            className="px-3 py-1.5 text-sm bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 flex items-center gap-2"
                                            title="Add global feedback"
                                        >
                                            <MessageSquare className="w-4 h-4" />
                                            Add Feedback
                                        </button>
                                        <button
                                            onClick={handleApproveOutline}
                                            className="px-3 py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
                                        >
                                            <CheckCircle className="w-4 h-4" />
                                            Approve
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4">
                        {outline ? (
                            <div className="space-y-4">
                                <div className="text-xl font-bold text-white mb-4">{outline.structure.title}</div>
                                {outline.structure.outline.map((section, sectionIndex) => (
                                    <div key={sectionIndex} className="bg-gray-900 rounded-lg p-4 border border-gray-800">
                                        <div className="flex items-start justify-between mb-2">
                                            <h2 className="text-lg font-semibold text-white">
                                                {editingSection === `section-${sectionIndex}` ? (
                                                    <input
                                                        type="text"
                                                        value={sectionEditValue}
                                                        onChange={(e) => setSectionEditValue(e.target.value)}
                                                        onBlur={handleSaveSection}
                                                        className="bg-gray-800 text-white px-2 py-1 rounded"
                                                        autoFocus
                                                    />
                                                ) : (
                                                    <span onClick={() => handleEditSection(sectionIndex)} className="cursor-pointer hover:text-blue-400">
                                                        {section.heading}
                                                    </span>
                                                )}
                                            </h2>
                                            <button
                                                onClick={() => {
                                                    setSelectedSectionForFeedback(`section-${sectionIndex}`);
                                                    setNewFeedback({ scope: 'section', comment: '', sectionId: `section-${sectionIndex}` });
                                                    setFeedbackOpen(true);
                                                }}
                                                className="p-1 hover:bg-gray-800 rounded transition-colors"
                                                title="Add feedback for this section"
                                            >
                                                <MessageSquare className="w-4 h-4 text-gray-400 hover:text-blue-400" />
                                            </button>
                                        </div>
                                        <p className="text-sm text-gray-400 mb-2">{section.intent}</p>
                                        {section.subsections && section.subsections.map((subsection, subIndex) => (
                                            <div key={subIndex} className="ml-4 mt-2 p-2 bg-gray-800/50 rounded">
                                                <h3 className="text-sm font-medium text-gray-300">{subsection.heading}</h3>
                                                <p className="text-xs text-gray-500">{subsection.intent}</p>
                                            </div>
                                        ))}
                                        {/* Show feedback for this section - inline */}
                                        {outlineFeedback?.filter(fb => 
                                            fb.scope === 'section' && fb.targetSectionId === `section-${sectionIndex}`
                                        ).map(fb => (
                                            <div key={fb.id} className="mt-2 p-2 bg-blue-500/10 border-l-2 border-blue-500/50 rounded-r text-sm">
                                                <div className="flex items-start gap-2">
                                                    <MessageSquare className="w-3 h-3 text-blue-400 mt-0.5 flex-shrink-0" />
                                                    <span className="text-blue-300">{fb.comment}</span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ))}
                                {/* Global feedback - collapsible section */}
                                {outlineFeedback && outlineFeedback.filter(fb => fb.scope === 'global').length > 0 && (
                                    <div className="mt-6 pt-4 border-t border-gray-800">
                                        <div className="flex items-center gap-2 mb-2">
                                            <MessageSquare className="w-4 h-4 text-yellow-400" />
                                            <h3 className="text-sm font-semibold text-yellow-400">Global Feedback</h3>
                                            <span className="text-xs text-gray-500">
                                                ({outlineFeedback.filter(fb => fb.scope === 'global').length})
                                            </span>
                                        </div>
                                        <div className="space-y-2">
                                            {outlineFeedback.filter(fb => fb.scope === 'global').map(fb => (
                                                <div key={fb.id} className="p-3 bg-yellow-500/10 border-l-2 border-yellow-500/50 rounded-r text-sm">
                                                    <span className="text-yellow-300">{fb.comment}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="flex items-center justify-center h-full text-gray-500">
                                <div className="text-center">
                                    <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                                    <p>No outline yet. Generate one to get started.</p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Panel - Draft */}
                <div className="w-1/2 flex flex-col">
                    <div className="bg-gray-900 border-b border-gray-800 p-4 shrink-0">
                        <div className="flex items-center justify-between">
                            <h2 className="text-lg font-bold text-white">Draft</h2>
                            {canGenerateDraft && !draft && (
                                <button
                                    onClick={handleGenerateDraft}
                                    disabled={generatingDraft}
                                    className="px-3 py-1.5 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-all"
                                >
                                    {generatingDraft ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            Generating...
                                        </>
                                    ) : (
                                        <>
                                            <Plus className="w-4 h-4" />
                                            Generate Draft
                                        </>
                                    )}
                                </button>
                            )}
                            {draft && (
                                <span className={`text-xs px-2 py-1 rounded-full ${
                                    draft.status === 'approved' ? 'bg-green-500/10 text-green-400' :
                                    draft.status === 'reviewed' ? 'bg-yellow-500/10 text-yellow-400' :
                                    'bg-gray-500/10 text-gray-400'
                                }`}>
                                    {draft.status}
                                </span>
                            )}
                        </div>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4">
                        {draft ? (
                            <div className="space-y-4">
                                <div className="prose prose-invert max-w-none">
                                    <ReactMarkdown>{draft.content}</ReactMarkdown>
                                </div>
                                {draft.metaDescription && (
                                    <div className="mt-4 p-3 bg-gray-900 rounded border border-gray-800">
                                        <p className="text-sm text-gray-400 mb-1">Meta Description:</p>
                                        <p className="text-sm text-white">{draft.metaDescription}</p>
                                    </div>
                                )}
                                <div className="flex items-center gap-4 text-xs text-gray-500">
                                    {draft.wordCount && <span>Words: {draft.wordCount}</span>}
                                    {draft.estimatedReadingTime && <span>Reading time: {draft.estimatedReadingTime} min</span>}
                                </div>
                                {/* Draft feedback */}
                                {draftFeedback?.map(fb => (
                                    <div key={fb.id} className={`p-3 rounded text-sm ${
                                        fb.scope === 'global' 
                                            ? 'bg-yellow-500/10 border border-yellow-500/20 text-yellow-400'
                                            : 'bg-blue-500/10 border border-blue-500/20 text-blue-400'
                                    }`}>
                                        <strong>{fb.scope === 'global' ? 'Global' : 'Section'} Feedback:</strong> {fb.comment}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="flex items-center justify-center h-full text-gray-500">
                                <div className="text-center">
                                    <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                                    {canGenerateDraft ? (
                                        <p>Click "Generate Draft" to create content from the approved outline.</p>
                                    ) : (
                                        <p>Approve the outline first to generate a draft.</p>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Feedback Modal */}
            {feedbackOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-gray-900 rounded-lg p-6 w-full max-w-md border border-gray-800">
                            <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-bold text-white">Add Feedback</h3>
                            <button
                                onClick={() => {
                                    setFeedbackOpen(false);
                                    setNewFeedback({ scope: 'global', comment: '', sectionId: '' });
                                    setSelectedSectionForFeedback(null);
                                }}
                                className="p-1 hover:bg-gray-800 rounded"
                            >
                                <X className="w-5 h-5 text-gray-400" />
                            </button>
                        </div>
                        {selectedSectionForFeedback && (
                            <div className="mb-4 p-2 bg-blue-500/10 border border-blue-500/20 rounded text-sm text-blue-400">
                                <span className="font-medium">Section:</span> {selectedSectionForFeedback}
                            </div>
                        )}
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Scope</label>
                                <select
                                    value={newFeedback.scope}
                                    onChange={(e) => {
                                        const newScope = e.target.value as 'global' | 'section';
                                        setNewFeedback({ 
                                            ...newFeedback, 
                                            scope: newScope,
                                            sectionId: newScope === 'section' && selectedSectionForFeedback 
                                                ? selectedSectionForFeedback 
                                                : ''
                                        });
                                    }}
                                    className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2 text-white"
                                >
                                    <option value="global">Global</option>
                                    <option value="section">Section</option>
                                </select>
                            </div>
                            {newFeedback.scope === 'section' && (
                                <div>
                                    <label className="block text-sm text-gray-400 mb-2">Section ID</label>
                                    <input
                                        type="text"
                                        value={newFeedback.sectionId}
                                        onChange={(e) => setNewFeedback({ ...newFeedback, sectionId: e.target.value })}
                                        placeholder="e.g., section-0"
                                        className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2 text-white"
                                    />
                                </div>
                            )}
                            <div>
                                <label className="block text-sm text-gray-400 mb-2">Comment</label>
                                <textarea
                                    value={newFeedback.comment}
                                    onChange={(e) => setNewFeedback({ ...newFeedback, comment: e.target.value })}
                                    rows={4}
                                    className="w-full bg-gray-800 border border-gray-700 rounded-lg p-2 text-white"
                                    placeholder="Enter your feedback..."
                                />
                            </div>
                            <button
                                onClick={handleAddFeedback}
                                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2"
                            >
                                <Send className="w-4 h-4" />
                                Add Feedback
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default BlogEditor;
