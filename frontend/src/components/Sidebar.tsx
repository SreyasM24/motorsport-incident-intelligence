import React from 'react';
import { 
  LayoutDashboard, 
  Flag, 
  AlertTriangle, 
  BookOpen, 
  Bot, 
  Settings, 
  X, 
  Activity,
  Zap
} from 'lucide-react';

interface SidebarProps {
  currentView: string;
  onNavigate: (view: string) => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
  onOpenSettings?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentView,
  onNavigate,
  mobileOpen,
  onCloseMobile,
  onOpenSettings,
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'races', label: 'Races', icon: Flag },
    { id: 'incidents', label: 'Incidents', icon: AlertTriangle },
    { id: 'regulations', label: 'Regulations', icon: BookOpen },
    { id: 'assistant', label: 'AI Steward Assistant', icon: Bot },
  ];

  const handleItemClick = (id: string) => {
    onNavigate(id);
    onCloseMobile();
  };

  const content = (
    <div className="flex flex-col h-full bg-[#0d0d0f] border-r border-white/10 select-none">
      {/* Brand Header */}
      <div 
        onClick={() => handleItemClick('landing')}
        className="p-6 border-b border-white/5 cursor-pointer group transition-colors hover:bg-white/[0.02]"
      >
        <div className="flex items-start justify-between">
          <div>
            <div className="text-xs tracking-[0.3em] font-bold text-red-600 font-tech uppercase">
              MII
            </div>
            <div className="text-sm font-bold tracking-tight mt-1 leading-tight text-white font-tech">
              MOTORSPORT<br />INCIDENT<br />INTELLIGENCE
            </div>
          </div>
          {mobileOpen && (
            <button 
              onClick={onCloseMobile}
              className="md:hidden p-1 text-white/40 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
        <div className="text-[10px] text-white/40 mt-3 font-mono flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>FastF1 25Hz Engine • Live Ingest</span>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 py-4">
        <div className="px-6 py-2 text-[10px] uppercase tracking-widest text-white/30 mb-2 font-mono">
          Intelligence
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => handleItemClick(item.id)}
              className={`w-full flex items-center px-6 py-2.5 text-xs font-medium gap-3 transition-colors text-left ${
                isActive
                  ? 'border-r-2 border-red-600 bg-white/5 text-white font-semibold'
                  : 'text-white/60 hover:text-white hover:bg-white/5'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-red-500' : 'opacity-70'}`} />
              <span className="tracking-wide flex-1">{item.label}</span>
              {item.id === 'incidents' && (
                <span className="text-[9px] font-mono bg-red-600/10 text-red-500 px-1.5 py-0.5 rounded border border-red-600/20 font-bold">
                  3 REVIEW
                </span>
              )}
              {item.id === 'assistant' && (
                <span className="text-[9px] font-mono text-red-500 font-bold">
                  AI
                </span>
              )}
            </button>
          );
        })}

        <div className="pt-4 mt-4 border-t border-white/5">
          <div className="px-6 py-2 text-[10px] uppercase tracking-widest text-white/30 mb-1 font-mono">
            Active Investigation
          </div>
          <button
            onClick={() => handleItemClick('incident-INC-024')}
            className={`w-full flex items-center justify-between px-6 py-2 text-xs transition-colors text-left ${
              currentView === 'incident-INC-024'
                ? 'border-r-2 border-red-600 bg-white/5 text-white'
                : 'text-white/60 hover:text-white hover:bg-white/5'
            }`}
          >
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-yellow-500"></span>
              <span className="font-mono text-[11px] font-bold text-white">INC-024</span>
              <span className="text-[10px] text-white/40 font-mono">Lap 31 T4</span>
            </div>
            <span className="text-[9px] font-mono bg-white/10 text-white/80 px-1.5 py-0.5 rounded">
              VER / HAM
            </span>
          </button>
        </div>
      </nav>

      {/* System Status & Footer */}
      <div className="p-6 mt-auto border-t border-white/5 bg-[#0a0a0b]/50">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
          <span className="text-[10px] uppercase tracking-wider text-white/60 font-mono">Telemetry Live</span>
        </div>
        <div className="flex items-center gap-2 mb-3">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
          <span className="text-[10px] uppercase tracking-wider text-white/60 font-mono">Backend Connected</span>
        </div>

        <div className="flex items-center justify-between pt-3 border-t border-white/5 text-white/40">
          <button 
            onClick={onOpenSettings}
            className="flex items-center gap-2 hover:text-white transition-colors"
          >
            <Settings className="w-3.5 h-3.5" />
            <span className="text-[10px] font-mono uppercase tracking-wider">Preferences</span>
          </button>
          <span className="text-[9px] font-mono text-white/30">v1.2.0</span>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className="hidden md:block w-56 h-screen sticky top-0 flex-shrink-0 z-30">
        {content}
      </aside>

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div 
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 md:hidden"
          onClick={onCloseMobile}
        >
          <div 
            className="w-64 h-full bg-[#0d0d0f]"
            onClick={(e) => e.stopPropagation()}
          >
            {content}
          </div>
        </div>
      )}
    </>
  );
};
