import React, { useState } from 'react';
import { 
  Bot, 
  Send, 
  Sparkles, 
  ArrowRight, 
  ShieldCheck, 
  Activity,
  Video,
  Scale,
  Compass,
  AlertTriangle,
  FileText
} from 'lucide-react';
import { AssistantMessage } from '../lib/types';
import { askAssistant } from '../lib/api';

interface AssistantViewProps {
  onNavigate: (view: string, id?: string) => void;
  preselectedIncidentId?: string;
}

export const AssistantView: React.FC<AssistantViewProps> = ({
  onNavigate,
  preselectedIncidentId = 'INC-024',
}) => {
  const [messages, setMessages] = useState<AssistantMessage[]>([
    {
      id: 'msg-init',
      sender: 'assistant',
      timestamp: '13:42:25',
      text: "AI Steward Assistant active. I analyze synchronized telemetry, video alignment, trajectory models, and FIA regulations to surface factual evidence for human race stewards. I do not decide penalties or assign guilt.\n\nSelect an incident query below or type your inquiry.",
      evidenceChips: [
        { label: 'TELEMETRY: FastF1 ECU 25Hz', type: 'telemetry' },
        { label: 'VIDEO: World Feed T4 (Pending Sync)', type: 'timeline' },
        { label: 'REGULATION: FIA Sporting Code Art 33.4', type: 'regulation' },
      ],
      suggestedFollowUps: [
        'Why was this incident flagged?',
        'What changed in the telemetry?',
        'Which regulations may be relevant?',
        'What evidence supports this assessment?',
        'What evidence is missing?',
      ],
    },
  ]);

  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  // Exact Section 16 Example Questions
  const exampleQuestions = [
    'Why was this incident flagged?',
    'What changed in the telemetry?',
    'Which regulations may be relevant?',
    'What evidence supports this assessment?',
    'What evidence is missing?',
  ];

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || input;
    if (!query.trim()) return;

    const userMsg: AssistantMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setIsTyping(true);

    try {
      const botReply = await askAssistant(query, preselectedIncidentId);
      setMessages((prev) => [...prev, botReply]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-${Date.now() + 1}`,
          sender: 'assistant',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
          text: `Assistant query service error: ${e.message || 'Service unreachable'}.`,
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };


  return (
    <div className="p-6 md:p-8 space-y-4 max-w-5xl mx-auto h-[calc(100vh-5rem)] flex flex-col">
      {/* Header (Section 16 Specification) */}
      <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shrink-0">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-sm bg-white/5 border border-white/10 flex items-center justify-center text-red-600">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] font-mono tracking-[0.2em] text-red-600 uppercase font-bold">
              AI STEWARD ASSISTANT
            </div>
            <h1 className="text-xl font-light tracking-tight text-white font-tech uppercase">
              EVIDENCE INTELLIGENCE & REGULATORY RETRIEVAL
            </h1>
            <p className="text-xs font-sans text-white/50 mt-0.5">
              "Ask questions about incidents, telemetry, evidence and regulations."
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-[10px] font-mono text-white/60 bg-white/5 px-3 py-1.5 rounded-sm border border-white/10">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
          <span className="uppercase tracking-wider">Decision Support Only • Stewards Decide</span>
        </div>
      </div>

      {/* Suggested Example Prompts Row */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 shrink-0 scrollbar-none">
        <span className="text-[10px] font-mono text-white/40 uppercase whitespace-nowrap">
          Example Inquiries:
        </span>
        {exampleQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(q)}
            className="px-3 py-1 rounded-sm bg-white/5 hover:bg-white/10 border border-white/10 text-white/80 hover:text-white text-[11px] font-mono whitespace-nowrap transition-colors cursor-pointer"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Chat Messages Log */}
      <div className="flex-1 bg-[#0d0d0f] border border-white/10 rounded-sm p-6 overflow-y-auto space-y-4 font-mono text-xs">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div
              key={msg.id}
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
            >
              <div className="flex items-center gap-2 mb-1.5 text-[10px] text-white/40 uppercase tracking-wider">
                <span>{isUser ? 'Steward Inquiry' : 'AI Steward Assistant'}</span>
                <span>•</span>
                <span>{msg.timestamp}</span>
              </div>

              <div
                className={`max-w-2xl p-5 rounded-sm leading-relaxed whitespace-pre-wrap ${
                  isUser
                    ? 'bg-white/10 text-white border border-white/15'
                    : 'bg-black/60 text-white/90 border border-white/10'
                }`}
              >
                <div className="font-sans text-xs leading-relaxed text-white/90">
                  {msg.text}
                </div>

                {/* Evidence Chips (Section 16 Specification) */}
                {msg.evidenceChips && msg.evidenceChips.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-white/10 flex flex-wrap gap-2">
                    {msg.evidenceChips.map((chip, i) => (
                      <span
                        key={i}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-sm bg-white/5 border border-white/10 text-[10px] font-mono font-bold text-white/80"
                      >
                        {chip.type === 'telemetry' && <Activity className="w-3 h-3 text-red-500" />}
                        {chip.type === 'timeline' && <Video className="w-3 h-3 text-cyan-400" />}
                        {chip.type === 'regulation' && <Scale className="w-3 h-3 text-yellow-500" />}
                        {chip.type === 'response' && <AlertTriangle className="w-3 h-3 text-emerald-400" />}
                        <span>{chip.label}</span>
                      </span>
                    ))}
                  </div>
                )}

                {/* Evidence Links */}
                {msg.evidenceLinks && msg.evidenceLinks.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {msg.evidenceLinks.map((link, idx) => (
                      <button
                        key={idx}
                        onClick={() => onNavigate(link.targetView, link.incidentId)}
                        className="inline-flex items-center gap-1.5 text-[10px] font-mono text-red-500 hover:text-red-400 bg-red-600/10 hover:bg-red-600/20 border border-red-600/30 px-2.5 py-1 rounded-sm uppercase tracking-wider transition-colors cursor-pointer"
                      >
                        <span>{link.label}</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    ))}
                  </div>
                )}

                {/* Follow up suggestions */}
                {msg.suggestedFollowUps && msg.suggestedFollowUps.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-white/5 flex flex-wrap items-center gap-2">
                    <span className="text-[10px] font-mono text-white/40">Suggested:</span>
                    {msg.suggestedFollowUps.map((q, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSend(q)}
                        className="text-[10px] font-mono text-white/60 hover:text-white underline decoration-white/20 transition-colors cursor-pointer"
                      >
                        "{q}"
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isTyping && (
          <div className="flex items-center gap-2 text-white/40 font-mono text-xs p-2">
            <span className="w-2 h-2 rounded-full bg-red-600 animate-ping" />
            <span>Analyzing FastF1 telemetry & retrieving relevant FIA regulations...</span>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-center gap-3 shrink-0"
      >
        <div className="relative flex-1">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask questions about incidents, telemetry, evidence and regulations..."
            className="w-full bg-[#0d0d0f] border border-white/10 focus:border-red-600 rounded-sm px-4 py-3.5 text-xs text-white placeholder:text-white/30 outline-none font-mono transition-colors"
          />
        </div>

        <button
          type="submit"
          disabled={!input.trim()}
          className="bg-red-600 hover:bg-red-700 disabled:opacity-40 disabled:hover:bg-red-600 text-white font-mono font-bold text-xs uppercase tracking-wider px-6 py-3.5 rounded-sm flex items-center gap-2 transition-colors cursor-pointer"
        >
          <span>Submit</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
};
