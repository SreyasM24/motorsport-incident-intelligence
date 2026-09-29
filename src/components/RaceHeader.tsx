import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Bell, 
  Menu, 
  Radio, 
  Clock, 
} from 'lucide-react';

interface RaceHeaderProps {
  onOpenSearch: () => void;
  onOpenMobileMenu: () => void;
  currentRaceName?: string;
  onSelectRace?: (raceId: string) => void;
}

export const RaceHeader: React.FC<RaceHeaderProps> = ({
  onOpenSearch,
  onOpenMobileMenu,
  currentRaceName = 'ITALIAN GRAND PRIX • RACE',
}) => {
  const [utcTime, setUtcTime] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(
        now.toISOString().substring(11, 19) + ' UTC'
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-14 border-b border-white/10 flex items-center justify-between px-6 md:px-8 bg-[#0a0a0b] sticky top-0 z-20">
      {/* Left: Mobile Toggle & Series/Session Metadata */}
      <div className="flex items-center gap-6">
        <button
          onClick={onOpenMobileMenu}
          className="md:hidden p-1.5 rounded text-white/40 hover:text-white hover:bg-white/5"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Series */}
        <div className="flex flex-col">
          <span className="text-[10px] text-white/40 uppercase tracking-widest leading-none font-mono">
            Series
          </span>
          <span className="text-xs font-semibold text-white tracking-wider font-tech mt-1">
            FORMULA 1
          </span>
        </div>

        <div className="h-6 w-px bg-white/10 hidden sm:block"></div>

        {/* Session */}
        <div className="hidden sm:flex flex-col">
          <span className="text-[10px] text-white/40 uppercase tracking-widest leading-none font-mono">
            Session
          </span>
          <span className="text-xs font-semibold text-white tracking-wider font-tech mt-1">
            {currentRaceName}
          </span>
        </div>
      </div>

      {/* Center/Right: Session Status & Actions */}
      <div className="flex items-center gap-4">
        {/* Status Badge */}
        <span className="hidden sm:inline-flex items-center gap-1.5 px-2 py-1 bg-emerald-500/10 text-emerald-500 text-[10px] font-bold tracking-widest border border-emerald-500/20 rounded-sm font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          ANALYSIS READY
        </span>

        {/* UTC Clock */}
        <div className="hidden lg:flex items-center gap-1.5 px-2 py-1 bg-white/5 border border-white/10 rounded-sm text-[10px] font-mono text-white/60">
          <Clock className="w-3 h-3 text-white/40" />
          <span>{utcTime || '14:14:52 UTC'}</span>
        </div>

        {/* Global Search Trigger */}
        <button
          onClick={onOpenSearch}
          className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-sm text-xs text-white/60 hover:text-white transition-all cursor-pointer"
        >
          <Search className="w-3.5 h-3.5 opacity-60" />
          <span className="hidden md:inline font-mono text-[10px] tracking-wider uppercase">Search evidence...</span>
          <kbd className="hidden md:inline text-[9px] font-mono bg-white/10 text-white/60 px-1 py-0.5 rounded-sm border border-white/10">
            ⌘K
          </kbd>
        </button>

        {/* Notifications */}
        <button 
          className="relative p-2 rounded text-white/40 hover:text-white hover:bg-white/5 transition-colors"
          title="Incident Alerts"
        >
          <Bell className="w-4 h-4 opacity-70" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-red-600"></span>
        </button>

        {/* Steward Profile Avatar */}
        <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-xs font-mono border border-white/10 text-white/80 select-none">
          S4
        </div>
      </div>
    </header>
  );
};
