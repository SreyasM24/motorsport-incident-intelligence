import React, { useState } from 'react';
import { UnresolvedQuestion, QuestionStatus } from '../lib/types';
import {
  HelpCircle,
  CheckCircle2,
  Clock,
  Archive,
  Plus,
  Send,
  ShieldCheck,
  Tag,
  AlertCircle,
} from 'lucide-react';

interface UnresolvedQuestionsPanelProps {
  questions: UnresolvedQuestion[];
  candidateId: string;
  onCreateQuestion: (
    question: string,
    evidenceIds?: string[],
    reviewerNote?: string
  ) => Promise<void>;
  onUpdateQuestion: (
    questionId: string,
    status?: QuestionStatus,
    reviewerNote?: string
  ) => Promise<void>;
}

export const UnresolvedQuestionsPanel: React.FC<UnresolvedQuestionsPanelProps> = ({
  questions,
  candidateId,
  onCreateQuestion,
  onUpdateQuestion,
}) => {
  const [showNewForm, setShowNewForm] = useState(false);
  const [newQuestionText, setNewQuestionText] = useState('');
  const [newEvidenceIds, setNewEvidenceIds] = useState('');
  const [newReviewerNote, setNewReviewerNote] = useState('');
  const [isSubmittingNew, setIsSubmittingNew] = useState(false);

  const [resolutionNotes, setResolutionNotes] = useState<Record<string, string>>({});
  const [isUpdating, setIsUpdating] = useState<Record<string, boolean>>({});

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newQuestionText.trim()) return;
    setIsSubmittingNew(true);
    try {
      const eIds = newEvidenceIds
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      await onCreateQuestion(newQuestionText, eIds, newReviewerNote);
      setNewQuestionText('');
      setNewEvidenceIds('');
      setNewReviewerNote('');
      setShowNewForm(false);
    } finally {
      setIsSubmittingNew(false);
    }
  };

  const handleStatusUpdate = async (questionId: string, status: QuestionStatus) => {
    const note = resolutionNotes[questionId];
    setIsUpdating((prev) => ({ ...prev, [questionId]: true }));
    try {
      await onUpdateQuestion(questionId, status, note);
      setResolutionNotes((prev) => ({ ...prev, [questionId]: '' }));
    } finally {
      setIsUpdating((prev) => ({ ...prev, [questionId]: false }));
    }
  };

  const getStatusBadge = (status: QuestionStatus) => {
    switch (status) {
      case 'RESOLVED':
        return (
          <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
            <CheckCircle2 className="w-2.5 h-2.5" />
            RESOLVED
          </span>
        );
      case 'DEFERRED':
        return (
          <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] font-bold uppercase tracking-wider bg-white/10 text-white/60 border border-white/20 flex items-center gap-1">
            <Archive className="w-2.5 h-2.5" />
            DEFERRED
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
            <Clock className="w-2.5 h-2.5" />
            OPEN
          </span>
        );
    }
  };

  return (
    <div className="space-y-4 bg-[#0d0d0f] border border-white/10 rounded-sm p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-4">
        <div>
          <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech flex items-center gap-2">
            <span className="w-2 h-2 bg-red-600 rounded-full"></span>
            UNRESOLVED INVESTIGATION QUESTIONS
          </div>
          <div className="text-[10px] font-mono text-white/40 mt-0.5">
            Structured steward inquiry registry • Track factual gaps and evidentiary uncertainties
          </div>
        </div>

        <button
          onClick={() => setShowNewForm(!showNewForm)}
          className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white text-[11px] font-mono font-bold uppercase tracking-wider rounded-xs transition-colors cursor-pointer flex items-center gap-1.5 shrink-0"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Log Investigation Question</span>
        </button>
      </div>

      {/* New Question Form */}
      {showNewForm && (
        <form
          onSubmit={handleCreate}
          className="bg-[#0a0a0b] border border-red-600/30 rounded-sm p-4 space-y-3 font-mono text-xs"
        >
          <div className="text-[10px] font-bold uppercase tracking-wider text-red-400">
            Open Factual Inquiry
          </div>

          <div>
            <label className="block text-[10px] text-white/40 uppercase tracking-wider mb-1">
              Factual or Technical Question *
            </label>
            <input
              type="text"
              required
              value={newQuestionText}
              onChange={(e) => setNewQuestionText(e.target.value)}
              placeholder="e.g. Camera coverage does not establish rear-wheel overlap at turn apex..."
              className="w-full bg-[#121214] border border-white/10 focus:border-red-600 rounded-xs px-3 py-2 text-xs text-white outline-none"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] text-white/40 uppercase tracking-wider mb-1">
                Related Evidence IDs (Comma Separated)
              </label>
              <input
                type="text"
                value={newEvidenceIds}
                onChange={(e) => setNewEvidenceIds(e.target.value)}
                placeholder="e.g. EV-TEL-RAW, EV-CV-TRACK-01"
                className="w-full bg-[#121214] border border-white/10 focus:border-red-600 rounded-xs px-3 py-2 text-xs text-white outline-none"
              />
            </div>

            <div>
              <label className="block text-[10px] text-white/40 uppercase tracking-wider mb-1">
                Initial Investigation Note
              </label>
              <input
                type="text"
                value={newReviewerNote}
                onChange={(e) => setNewReviewerNote(e.target.value)}
                placeholder="e.g. Request secondary trackside camera timecode alignment"
                className="w-full bg-[#121214] border border-white/10 focus:border-red-600 rounded-xs px-3 py-2 text-xs text-white outline-none"
              />
            </div>
          </div>

          <div className="flex items-center gap-2 pt-1">
            <button
              type="submit"
              disabled={isSubmittingNew}
              className="px-4 py-1.5 bg-red-600 hover:bg-red-500 text-white text-[11px] font-bold uppercase tracking-wider rounded-xs transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
            >
              <span>{isSubmittingNew ? 'Saving...' : 'Submit Question'}</span>
              <Send className="w-3 h-3" />
            </button>
            <button
              type="button"
              onClick={() => setShowNewForm(false)}
              className="px-3 py-1.5 bg-white/5 hover:bg-white/10 text-white/60 text-[11px] uppercase rounded-xs cursor-pointer"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Questions List */}
      <div className="space-y-3 pt-1">
        {questions.length === 0 ? (
          <div className="p-6 text-center text-xs font-mono text-white/40 bg-[#0a0a0b] border border-white/5 rounded-sm">
            Zero unresolved investigation questions logged for this candidate.
          </div>
        ) : (
          questions.map((q) => {
            const qId = q.id;
            return (
              <div
                key={qId}
                className="bg-[#0a0a0b] border border-white/10 rounded-sm p-4 space-y-3 font-mono text-xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white tracking-wide">
                      {q.question}
                    </span>
                  </div>
                  <div>{getStatusBadge(q.status)}</div>
                </div>

                {q.evidenceIds && q.evidenceIds.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                    <span className="text-[10px] text-white/40 uppercase">Related Evidence:</span>
                    {q.evidenceIds.map((eid, eIdx) => (
                      <span
                        key={eIdx}
                        className="text-[9px] bg-white/5 border border-white/10 px-2 py-0.5 rounded-xs text-white/70"
                      >
                        {eid}
                      </span>
                    ))}
                  </div>
                )}

                {q.reviewerNote && (
                  <div className="text-[11px] text-white/80 bg-[#08080a] border border-white/5 p-2.5 rounded-xs leading-relaxed">
                    <span className="text-white/40 font-bold uppercase text-[9px] block mb-0.5">
                      Steward Finding / Note:
                    </span>
                    {q.reviewerNote}
                  </div>
                )}

                {/* Resolution Action Row */}
                <div className="bg-[#121216] border border-white/10 p-2.5 rounded-xs flex flex-col md:flex-row md:items-center gap-2">
                  <input
                    type="text"
                    value={resolutionNotes[qId] || ''}
                    onChange={(e) =>
                      setResolutionNotes((prev) => ({ ...prev, [qId]: e.target.value }))
                    }
                    placeholder="Append resolution findings or rationale..."
                    className="flex-1 bg-[#09090b] border border-white/10 focus:border-amber-500 text-xs px-3 py-1.5 rounded-xs text-white placeholder:text-white/30 outline-none"
                  />

                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      type="button"
                      disabled={isUpdating[qId]}
                      onClick={() => handleStatusUpdate(qId, 'RESOLVED')}
                      className="px-3 py-1.5 bg-emerald-600/80 hover:bg-emerald-500 text-white text-[10px] font-bold uppercase tracking-wider rounded-xs cursor-pointer flex items-center gap-1"
                    >
                      <CheckCircle2 className="w-3 h-3" />
                      <span>Resolve</span>
                    </button>

                    <button
                      type="button"
                      disabled={isUpdating[qId]}
                      onClick={() => handleStatusUpdate(qId, 'DEFERRED')}
                      className="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white/80 text-[10px] font-bold uppercase tracking-wider rounded-xs cursor-pointer flex items-center gap-1"
                    >
                      <Archive className="w-3 h-3" />
                      <span>Defer</span>
                    </button>

                    {q.status !== 'OPEN' && (
                      <button
                        type="button"
                        disabled={isUpdating[qId]}
                        onClick={() => handleStatusUpdate(qId, 'OPEN')}
                        className="px-2.5 py-1.5 bg-amber-600/20 hover:bg-amber-600/40 text-amber-300 text-[10px] uppercase rounded-xs cursor-pointer"
                      >
                        Reopen
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
