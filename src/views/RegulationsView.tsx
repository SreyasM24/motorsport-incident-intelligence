import React, { useState, useEffect } from 'react';
import { getRegulations } from '../lib/api';
import { RelevantRegulation } from '../lib/types';
import { MOCK_REGULATION_LIBRARY } from '../lib/mockData';
import { Search, ExternalLink, Scale, ChevronDown, ChevronUp } from 'lucide-react';

interface RegulationsViewProps {
  onNavigate: (view: string, id?: string) => void;
}

export const RegulationsView: React.FC<RegulationsViewProps> = ({ onNavigate }) => {
  const [search, setSearch] = useState('');
  const [selectedSeries, setSelectedSeries] = useState<string>('Formula 1');
  const [selectedSeason, setSelectedSeason] = useState<string>('2024');
  const [selectedDoc, setSelectedDoc] = useState<string>('ALL');
  const [selectedArticle, setSelectedArticle] = useState<string>('ALL');
  const [expandedArticleId, setExpandedArticleId] = useState<string | null>(null);
  const [regulations, setRegulations] = useState<RelevantRegulation[]>(MOCK_REGULATION_LIBRARY);

  useEffect(() => {
    getRegulations(search).then((data) => {
      if (data && data.length > 0) {
        setRegulations(data);
      }
    });
  }, [search]);

  const filtered = regulations.filter((r) => {
    const matchesSearch =
      r.article.toLowerCase().includes(search.toLowerCase()) ||
      r.title.toLowerCase().includes(search.toLowerCase()) ||
      (r.whyRelevant && r.whyRelevant.toLowerCase().includes(search.toLowerCase())) ||
      (r.matchReason && r.matchReason.toLowerCase().includes(search.toLowerCase()));
    const matchesDoc = selectedDoc === 'ALL' || r.document.includes(selectedDoc);
    const matchesArticle = selectedArticle === 'ALL' || r.article.includes(selectedArticle);
    return matchesSearch && matchesDoc && matchesArticle;
  });

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6 md:p-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="text-[10px] font-mono tracking-[0.2em] text-red-600 uppercase font-bold mb-1">
            FIA GOVERNANCE & SPORTING CODE
          </div>
          <h1 className="text-2xl sm:text-3xl font-light tracking-tight text-white font-tech uppercase">
            REGULATIONS REPOSITORY
          </h1>
          <p className="text-xs font-sans text-white/50 mt-1 max-w-2xl">
            FIA Sporting Regulations, International Sporting Code Appendix L, and Event Notes indexed for incident context retrieval.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono bg-white/10 text-white/80 border border-white/10 px-3 py-1.5 rounded-sm uppercase tracking-wider">
            FIA 2024 SPORTING CODE
          </span>
        </div>
      </div>

      {/* Mandatory Sample / Placeholder Data Notice (Section 10 Requirement) */}
      <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-sm flex items-center justify-between text-xs font-mono text-amber-300">
        <div className="flex items-center gap-2">
          <Scale className="w-4 h-4 shrink-0 text-amber-400" />
          <span>SAMPLE / PLACEHOLDER DATA: Regulations are cross-referenced for algorithmic decision support only. Official decisions reference the ratified FIA Statutes.</span>
        </div>
      </div>

      {/* Filter Controls (Section 10 Exact Specifications: Search, Series, Season, Document, Article) */}
      <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-5 space-y-4">
        {/* Search */}
        <div className="relative w-full">
          <Search className="w-4 h-4 text-white/40 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search regulation titles, keywords (overtaking, crowding, track limits), or article numbers..."
            className="w-full bg-[#0a0a0b] border border-white/10 focus:border-red-600 rounded-sm pl-10 pr-3 py-2 text-xs text-white placeholder:text-white/30 outline-none font-mono transition-colors"
          />
        </div>

        {/* Series, Season, Document, Article Filters */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
          {/* Series */}
          <div>
            <label className="text-[10px] text-white/40 uppercase tracking-wider block mb-1">
              Series
            </label>
            <select
              value={selectedSeries}
              onChange={(e) => setSelectedSeries(e.target.value)}
              className="w-full bg-[#0a0a0b] border border-white/10 rounded-sm px-2.5 py-1.5 text-white outline-none focus:border-red-600 cursor-pointer"
            >
              <option value="Formula 1">Formula 1 (FIA F1)</option>
              <option value="Formula 2">Formula 2 (FIA F2)</option>
              <option value="WEC">World Endurance (WEC)</option>
            </select>
          </div>

          {/* Season */}
          <div>
            <label className="text-[10px] text-white/40 uppercase tracking-wider block mb-1">
              Season
            </label>
            <select
              value={selectedSeason}
              onChange={(e) => setSelectedSeason(e.target.value)}
              className="w-full bg-[#0a0a0b] border border-white/10 rounded-sm px-2.5 py-1.5 text-white outline-none focus:border-red-600 cursor-pointer"
            >
              <option value="2024">2024 Championship</option>
              <option value="2023">2023 Championship</option>
            </select>
          </div>

          {/* Document */}
          <div>
            <label className="text-[10px] text-white/40 uppercase tracking-wider block mb-1">
              Document
            </label>
            <select
              value={selectedDoc}
              onChange={(e) => setSelectedDoc(e.target.value)}
              className="w-full bg-[#0a0a0b] border border-white/10 rounded-sm px-2.5 py-1.5 text-white outline-none focus:border-red-600 cursor-pointer"
            >
              <option value="ALL">All Documents</option>
              <option value="Sporting">FIA Sporting Regulations</option>
              <option value="Appendix L">ISC Appendix L (Driving Code)</option>
            </select>
          </div>

          {/* Article */}
          <div>
            <label className="text-[10px] text-white/40 uppercase tracking-wider block mb-1">
              Article Filter
            </label>
            <select
              value={selectedArticle}
              onChange={(e) => setSelectedArticle(e.target.value)}
              className="w-full bg-[#0a0a0b] border border-white/10 rounded-sm px-2.5 py-1.5 text-white outline-none focus:border-red-600 cursor-pointer"
            >
              <option value="ALL">All Articles</option>
              <option value="33.4">Article 33.4</option>
              <option value="33.3">Article 33.3</option>
              <option value="2(b)">Appendix L Art 2(b)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Regulation Results (Section 10 Exact Specifications) */}
      <div className="space-y-4">
        {filtered.map((reg) => {
          const isExpanded = expandedArticleId === reg.id;
          return (
            <div
              key={reg.id}
              className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6 hover:border-white/20 transition-colors space-y-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-3">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold font-mono text-red-500 bg-white/5 px-2.5 py-1 rounded-sm border border-white/10 uppercase">
                    {reg.article}
                  </span>
                  <h2 className="text-sm font-semibold text-white font-tech uppercase tracking-wide">
                    {reg.title}
                  </h2>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-[10px] font-mono text-white/40">
                    {reg.document}
                  </span>
                  <button
                    onClick={() => setExpandedArticleId(isExpanded ? null : reg.id)}
                    className="px-3 py-1 bg-white/5 hover:bg-red-600 hover:text-white border border-white/10 text-white/80 text-[10px] font-mono font-bold uppercase rounded-sm transition-colors cursor-pointer"
                  >
                    VIEW ARTICLE
                  </button>
                </div>
              </div>

              {/* Short relevance/context */}
              <div className="p-3.5 rounded-sm bg-white/5 border border-white/5">
                <div className="text-[10px] font-mono text-white/40 uppercase tracking-wider mb-1">
                  RELEVANCE CONTEXT
                </div>
                <p className="text-white/85 font-sans text-xs leading-relaxed">
                  {reg.whyRelevant}
                </p>
              </div>

              {/* Expanded Context */}
              {isExpanded && (
                <div className="p-4 rounded-sm bg-[#0a0a0b] border border-white/10 space-y-3">
                  <div className="text-[9px] font-mono text-white/40 uppercase tracking-wider">
                    SAMPLE / PLACEHOLDER TEXT EXCERPT (OFFICIAL RULEBOOK REFERENCE)
                  </div>
                  <div className="text-xs text-white/70 italic font-sans border-l-2 border-red-600 pl-3">
                    "{reg.regulationTextPlaceholder}"
                  </div>
                  <div className="text-[10px] font-mono text-white/40 pt-1">
                    System Correlation Key: <span className="text-white/80">{reg.matchReason}</span>
                  </div>
                </div>
              )}

              {/* Source & Metadata */}
              <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-[10px] font-mono text-white/40">
                <div>
                  <span className="font-bold">SOURCE: </span>
                  <span className="text-white/70">{reg.source}</span>
                </div>
                <div className="text-white/30 italic">
                  SAMPLE / PLACEHOLDER DATA
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
