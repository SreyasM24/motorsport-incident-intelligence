import React from 'react';
import { HeroVideoBackground } from '../components/HeroVideoBackground';
import { 
  ArrowRight, 
  LayoutDashboard, 
  Activity, 
  ShieldCheck, 
  Scale, 
  Video,
  Bot,
  UserCheck,
  Radio,
  FileText,
  Binary,
  Layers,
  Cpu,
  Database,
  ExternalLink
} from 'lucide-react';

interface LandingViewProps {
  onNavigate: (view: string) => void;
}

export const LandingView: React.FC<LandingViewProps> = ({ onNavigate }) => {
  return (
    <div className="relative min-h-screen w-full bg-[#0a0a0b] text-[#e0e0e0] flex flex-col justify-between overflow-x-hidden selection:bg-red-600/30">
      {/* Hero Section with Fullscreen Background Video */}
      <section className="relative min-h-screen w-full flex flex-col justify-between overflow-hidden">
        {/* Full-viewport background video playing seamlessly */}
        <HeroVideoBackground />

        {/* Clean Top Navigation Bar — No fake dashboard buttons */}
        <header className="relative z-30 w-full px-6 sm:px-10 py-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-sm bg-red-600 flex items-center justify-center font-tech font-bold text-white text-sm tracking-wider">
              MII
            </div>
            <div>
              <div className="text-[9px] font-mono tracking-[0.25em] text-red-600 uppercase font-bold leading-tight">
                Motorsport
              </div>
              <div className="text-sm font-semibold tracking-tight text-white font-tech leading-none uppercase">
                INCIDENT INTELLIGENCE
              </div>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <button
              onClick={() => onNavigate('incidents')}
              className="text-xs font-mono text-white/70 hover:text-white transition-colors cursor-pointer uppercase tracking-wider"
            >
              Incidents
            </button>
            <button
              onClick={() => onNavigate('dashboard')}
              className="text-xs font-mono text-white/70 hover:text-white transition-colors cursor-pointer uppercase tracking-wider"
            >
              Dashboard
            </button>
            <button
              onClick={() => onNavigate('regulations')}
              className="text-xs font-mono text-white/70 hover:text-white transition-colors cursor-pointer uppercase tracking-wider hidden sm:inline-block"
            >
              Regulations
            </button>
            <button
              onClick={() => onNavigate('assistant')}
              className="text-xs font-mono text-white/70 hover:text-white transition-colors cursor-pointer uppercase tracking-wider hidden sm:inline-block"
            >
              AI Assistant
            </button>
          </div>
        </header>

        {/* Homepage Hero Core Content */}
        <main className="relative z-30 max-w-5xl mx-auto px-6 py-16 sm:py-24 flex flex-col items-center text-center my-auto">
          {/* Subtle Technical Pill */}
          <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-black/70 backdrop-blur-md border border-white/15 text-xs font-mono text-white/85 mb-8">
            <span className="w-2 h-2 rounded-full bg-red-600 animate-pulse" />
            <span className="tracking-widest uppercase text-[11px]">
              DECISION-SUPPORT & EVIDENCE-INTELLIGENCE PLATFORM
            </span>
          </div>

          {/* Large Typography */}
          <h1 className="text-4xl sm:text-6xl md:text-7xl font-light tracking-tight text-white font-tech uppercase leading-[0.95] mb-5">
            MOTORSPORT <br />
            <span className="text-white/90 font-normal">
              INCIDENT INTELLIGENCE
            </span>
          </h1>

          {/* Tagline */}
          <p className="text-lg sm:text-xl font-light text-white/95 max-w-2xl mb-3 tracking-wide">
            "Evidence intelligence for modern motorsport."
          </p>

          {/* Short Description */}
          <p className="text-sm sm:text-base text-white/60 max-w-xl mb-10 leading-relaxed font-sans">
            Reconstruct incidents. Surface evidence. Retrieve regulations. Assist human race stewards.
          </p>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto">
            <button
              onClick={() => onNavigate('incidents')}
              className="w-full sm:w-auto px-8 py-3.5 bg-red-600 hover:bg-red-700 text-white font-mono font-bold text-xs tracking-[0.2em] uppercase rounded-sm flex items-center justify-center gap-2 transition-all hover:shadow-[0_0_20px_rgba(225,6,0,0.4)] cursor-pointer"
            >
              <span>EXPLORE INCIDENTS</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => onNavigate('dashboard')}
              className="w-full sm:w-auto px-8 py-3.5 bg-black/60 hover:bg-white/10 backdrop-blur-md border border-white/20 hover:border-white/40 text-white font-mono font-bold text-xs tracking-[0.2em] uppercase rounded-sm flex items-center justify-center gap-2 transition-colors cursor-pointer"
            >
              <LayoutDashboard className="w-4 h-4 text-white/60" />
              <span>OPEN RACE DASHBOARD</span>
            </button>
          </div>

          {/* Core Philosophy Pill */}
          <div className="mt-10 flex items-center gap-2 text-xs font-mono text-white/60 bg-black/60 backdrop-blur-md px-4 py-1.5 rounded-full border border-white/10">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
            <span>AI-assisted • Evidence-driven • Human reviewed</span>
          </div>
        </main>

        {/* Hero Bottom Bar: Highlighting the Core Evidence Modules */}
        <div className="relative z-30 w-full border-t border-white/10 bg-[#0a0a0b]/85 backdrop-blur-md px-6 sm:px-10 py-4">
          <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-left w-full md:w-auto">
              <div className="flex items-center gap-3">
                <Activity className="w-4 h-4 text-red-500" />
                <div>
                  <div className="text-[9px] font-mono tracking-wider text-white/40 uppercase">HIGH-RATE</div>
                  <div className="text-xs font-bold font-tech text-white uppercase tracking-wider">TELEMETRY</div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Video className="w-4 h-4 text-cyan-400" />
                <div>
                  <div className="text-[9px] font-mono tracking-wider text-white/40 uppercase">SYNCHRONIZED</div>
                  <div className="text-xs font-bold font-tech text-white uppercase tracking-wider">VIDEO EVIDENCE</div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Scale className="w-4 h-4 text-yellow-500" />
                <div>
                  <div className="text-[9px] font-mono tracking-wider text-white/40 uppercase">CROSS-REFERENCED</div>
                  <div className="text-xs font-bold font-tech text-white uppercase tracking-wider">REGULATIONS</div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Bot className="w-4 h-4 text-purple-400" />
                <div>
                  <div className="text-[9px] font-mono tracking-wider text-white/40 uppercase">DETERMINISTIC</div>
                  <div className="text-xs font-bold font-tech text-white uppercase tracking-wider">AI ASSISTANT</div>
                </div>
              </div>
            </div>

            <div className="text-[11px] font-mono text-white/40 tracking-wider">
              FASTF1 25Hz • OPENF1 INGEST • FIA ISC APPENDIX L
            </div>
          </div>
        </div>
      </section>

      {/* Section 5 & 21: Visible Intelligence Pipeline Section */}
      <section className="relative z-20 bg-[#0d0d0f] border-t border-b border-white/10 py-16 px-6 sm:px-10">
        <div className="max-w-7xl mx-auto space-y-10">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <div className="text-[10px] font-mono tracking-[0.25em] text-red-600 uppercase font-bold mb-1">
                SYSTEM ARCHITECTURE & ENGINE PIPELINE
              </div>
              <h2 className="text-2xl sm:text-3xl font-light text-white font-tech uppercase tracking-wide">
                HOW INCIDENTS ARE RECONSTRUCTED
              </h2>
              <p className="text-xs font-sans text-white/50 mt-1 max-w-xl">
                The platform does not issue automatic penalties. It aggregates multi-source motorsport data into deterministic evidence for human race stewards.
              </p>
            </div>

            <div className="flex items-center gap-2 text-xs font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-sm">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>FastAPI Backend Architecture Ready</span>
            </div>
          </div>

          {/* Visual Pipeline Flow Chart */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-3">
            {[
              {
                step: '01',
                label: 'TELEMETRY',
                desc: 'FastF1 ECU & OpenF1 transponders',
                status: 'CONNECTED',
                statusColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
                icon: Activity,
              },
              {
                step: '02',
                label: 'VIDEO EVIDENCE',
                desc: 'Synchronized broadcast & onboard feeds',
                status: 'AVAILABLE',
                statusColor: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
                icon: Video,
              },
              {
                step: '03',
                label: 'INCIDENT RECONSTRUCTION',
                desc: 'Relative motion, closing speed & yaw response',
                status: 'AVAILABLE',
                statusColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
                icon: Binary,
              },
              {
                step: '04',
                label: 'EVIDENCE ANALYSIS',
                desc: 'Proximity metrics & uncertainty boundaries',
                status: 'AVAILABLE',
                statusColor: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
                icon: Layers,
              },
              {
                step: '05',
                label: 'REGULATIONS',
                desc: 'FIA Sporting Code semantic search',
                status: 'AVAILABLE',
                statusColor: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
                icon: Scale,
              },
              {
                step: '06',
                label: 'AI ASSISTANT',
                desc: 'Context-aware evidence synthesis',
                status: 'IN DEVELOPMENT',
                statusColor: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
                icon: Bot,
              },
              {
                step: '07',
                label: 'HUMAN REVIEW',
                desc: 'Final adjudication by appointed stewards',
                status: 'HUMAN IN THE LOOP',
                statusColor: 'text-red-400 bg-red-500/10 border-red-500/30',
                icon: UserCheck,
              },
            ].map((node, idx) => {
              const Icon = node.icon;
              return (
                <div
                  key={idx}
                  className="p-4 rounded-sm bg-[#0a0a0b] border border-white/10 flex flex-col justify-between hover:border-white/20 transition-colors group"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-mono text-white/30 uppercase font-bold">
                        STEP {node.step}
                      </span>
                      <Icon className="w-3.5 h-3.5 text-white/40 group-hover:text-white transition-colors" />
                    </div>
                    <div className="text-xs font-semibold text-white font-tech uppercase tracking-wider mb-1">
                      {node.label}
                    </div>
                    <p className="text-[11px] font-sans text-white/50 leading-relaxed">
                      {node.desc}
                    </p>
                  </div>

                  <div className="mt-4 pt-2 border-t border-white/5">
                    <span
                      className={`text-[9px] font-mono px-1.5 py-0.5 rounded-sm font-bold uppercase border inline-block ${node.statusColor}`}
                    >
                      {node.status}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Section 20: Data Sources Grid */}
      <section className="py-16 px-6 sm:px-10 bg-[#0a0a0b]">
        <div className="max-w-7xl mx-auto space-y-8">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div>
              <div className="text-[10px] font-mono tracking-[0.25em] text-red-600 uppercase font-bold mb-1">
                INTELLIGENCE INPUTS
              </div>
              <h2 className="text-2xl sm:text-3xl font-light text-white font-tech uppercase tracking-wide">
                OFFICIAL DATA SOURCES
              </h2>
              <p className="text-xs font-sans text-white/50 mt-1 max-w-xl">
                Real-time and post-session telemetry feeds aggregated to form a unified factual record.
              </p>
            </div>

            <div className="text-xs font-mono text-white/40">
              Deterministic Ingest Pipeline
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {[
              {
                name: 'FastF1',
                type: 'ECU & Telemetry Data',
                desc: '25Hz throttle, brake, speed, steering angle, gear, and engine RPM traces from car transponders.',
                icon: Cpu,
                status: 'CONNECTED',
              },
              {
                name: 'OpenF1',
                type: 'Live Timing & Car Positions',
                desc: 'High-frequency GPS intervals, mini-sectors, pit exit deltas, and official race control messages.',
                icon: Database,
                status: 'CONNECTED',
              },
              {
                name: 'Video Evidence',
                type: 'FOM Broadcast & Onboards',
                desc: 'Multi-angle synchronized visual feeds with sub-second alignment to telemetry timestamps.',
                icon: Video,
                status: 'AVAILABLE',
              },
              {
                name: 'FIA Regulations',
                type: 'Sporting Code & Precedents',
                desc: 'FIA Formula 1 Sporting Regulations, ISC Appendix L Chapter IV, and Circuit Director Notes.',
                icon: Scale,
                status: 'CONNECTED',
              },
              {
                name: 'AI Evidence Engine',
                type: 'Analysis & Synthesis',
                desc: 'Contextual anomaly detection, proximity delta calculations, and semantic regulatory retrieval.',
                icon: Bot,
                status: 'IN DEVELOPMENT',
              },
            ].map((src, i) => {
              const Icon = src.icon;
              return (
                <div
                  key={i}
                  className="bg-[#0d0d0f] border border-white/10 rounded-sm p-5 flex flex-col justify-between hover:border-white/20 transition-colors"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-bold text-white font-tech uppercase tracking-wider">
                        {src.name}
                      </span>
                      <Icon className="w-4 h-4 text-white/40" />
                    </div>
                    <div className="text-[10px] font-mono text-red-500 uppercase mb-2">
                      {src.type}
                    </div>
                    <p className="text-xs font-sans text-white/60 leading-relaxed">
                      {src.desc}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-[10px] font-mono">
                    <span className="text-white/40">Status</span>
                    <span className="text-emerald-400 font-bold">{src.status}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Section 22: Project Philosophy Banner */}
      <section className="py-16 px-6 sm:px-10 bg-[#0d0d0f] border-t border-b border-white/10">
        <div className="max-w-4xl mx-auto text-center space-y-5">
          <div className="text-[11px] font-mono tracking-[0.3em] text-red-600 uppercase font-bold">
            CORE PHILOSOPHY
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-light text-white font-tech uppercase tracking-tight">
            AI ASSISTS. EVIDENCE SUPPORTS. <br />
            <span className="text-red-500 font-normal">HUMANS DECIDE.</span>
          </h2>
          <p className="text-sm sm:text-base text-white/70 font-sans max-w-2xl mx-auto leading-relaxed">
            "Motorsport Incident Intelligence is designed as a decision-support system. It reconstructs incidents, surfaces evidence and connects observations with relevant regulations while keeping final judgement with human race stewards."
          </p>
          <div className="pt-2 flex flex-wrap items-center justify-center gap-4 text-xs font-mono text-white/40">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-600" />
              Never produces automated penalties
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-600" />
              Surfaces confidence and uncertainty
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-600" />
              Preserves steward sovereignty
            </span>
          </div>
        </div>
      </section>

      {/* Section 18: F1 Information & Reference Context */}
      <section className="py-14 px-6 sm:px-10 bg-[#0a0a0b]">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-4">
            <div>
              <div className="text-[10px] font-mono tracking-[0.2em] text-white/40 uppercase">
                FORMULA 1 REFERENCE DATA
              </div>
              <h3 className="text-lg font-light text-white font-tech uppercase tracking-wide">
                CHAMPIONSHIP BENCHMARKS & CONTEXT
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono bg-white/5 border border-white/10 px-2.5 py-1 rounded-sm text-white/60">
                STATIC REFERENCE (2024 REGULATION ERA)
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { label: 'CHAMPIONSHIP', val: 'FIA Formula 1' },
              { label: 'SEASON', val: '2024 World Tour' },
              { label: 'CONSTRUCTORS', val: '10 Teams' },
              { label: 'GRID DRIVERS', val: '20 Drivers' },
              { label: 'GRAND PRIX', val: '24 Rounds' },
              { label: 'SPRINT WEEKENDS', val: '6 Sprints' },
            ].map((fact, idx) => (
              <div key={idx} className="bg-[#0d0d0f] border border-white/10 rounded-sm p-3.5">
                <div className="text-[9px] font-mono text-white/40 uppercase tracking-widest mb-1">
                  {fact.label}
                </div>
                <div className="text-sm font-semibold text-white font-tech uppercase tracking-wide">
                  {fact.val}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Section 23: Clean Professional Engineering Footer */}
      <footer className="relative z-20 border-t border-white/10 bg-[#07090c] px-6 sm:px-10 py-10">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4 text-center sm:text-left">
            <div className="w-8 h-8 rounded-sm bg-red-600 flex items-center justify-center font-tech font-bold text-white text-xs mx-auto sm:mx-0">
              MII
            </div>
            <div>
              <div className="text-sm font-bold text-white font-tech tracking-wider uppercase">
                MOTORSPORT INCIDENT INTELLIGENCE
              </div>
              <div className="text-xs text-white/50 font-sans mt-0.5">
                AI-powered evidence intelligence for motorsport.
              </div>
            </div>
          </div>

          {/* Links */}
          <div className="flex flex-wrap items-center justify-center gap-6 text-xs font-mono text-white/60">
            <button
              onClick={() => onNavigate('dashboard')}
              className="hover:text-white transition-colors cursor-pointer uppercase tracking-wider"
            >
              Dashboard
            </button>
            <button
              onClick={() => onNavigate('incidents')}
              className="hover:text-white transition-colors cursor-pointer uppercase tracking-wider"
            >
              Incidents
            </button>
            <button
              onClick={() => onNavigate('regulations')}
              className="hover:text-white transition-colors cursor-pointer uppercase tracking-wider"
            >
              Regulations
            </button>
            <button
              onClick={() => onNavigate('assistant')}
              className="hover:text-white transition-colors cursor-pointer uppercase tracking-wider"
            >
              AI Assistant
            </button>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-white transition-colors flex items-center gap-1 uppercase tracking-wider"
            >
              <span>GitHub</span>
              <ExternalLink className="w-3 h-3 text-white/40" />
            </a>
          </div>

          {/* Status badge */}
          <div className="flex items-center gap-2 text-[10px] font-mono text-white/40 bg-white/5 px-3 py-1.5 rounded-sm border border-white/10">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>Open Source • Development Build</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
