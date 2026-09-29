import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { RaceHeader } from './components/RaceHeader';
import { GlobalSearchModal } from './components/GlobalSearchModal';
import { LandingView } from './views/LandingView';
import { DashboardView } from './views/DashboardView';
import { RacesView } from './views/RacesView';
import { IncidentsView } from './views/IncidentsView';
import { IncidentDetailView } from './views/IncidentDetailView';
import { AssistantView } from './views/AssistantView';
import { RegulationsView } from './views/RegulationsView';

export default function App() {
  const [currentView, setCurrentView] = useState<string>('landing');
  const [activeIncidentId, setActiveIncidentId] = useState<string>('INC-024');
  const [isMobileNavOpen, setIsMobileNavOpen] = useState<boolean>(false);
  const [isSearchOpen, setIsSearchOpen] = useState<boolean>(false);

  const handleNavigate = (view: string, id?: string) => {
    if (view.startsWith('incident-')) {
      const incId = id || view.replace('incident-', '');
      setActiveIncidentId(incId);
      setCurrentView('incident-detail');
    } else if (view === 'incident-detail') {
      if (id) setActiveIncidentId(id);
      setCurrentView('incident-detail');
    } else {
      if (id && view === 'assistant') {
        setActiveIncidentId(id);
      }
      setCurrentView(view);
    }
  };

  // When on Landing page, render full viewport cinematic hero
  if (currentView === 'landing') {
    return (
      <div className="min-h-screen bg-[#0a0a0b] text-[#e0e0e0]">
        <LandingView onNavigate={handleNavigate} />
        <GlobalSearchModal
          isOpen={isSearchOpen}
          onClose={() => setIsSearchOpen(false)}
          onNavigate={handleNavigate}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-[#e0e0e0] flex flex-col md:flex-row overflow-x-hidden font-sans selection:bg-red-600/30">
      {/* Persistent Sidebar on Desktop + Mobile Drawer */}
      <Sidebar
        currentView={currentView === 'incident-detail' ? 'incidents' : currentView}
        onNavigate={handleNavigate}
        mobileOpen={isMobileNavOpen}
        onCloseMobile={() => setIsMobileNavOpen(false)}
        onOpenSettings={() => setIsSearchOpen(true)}
      />

      {/* Main Operational Workstation Canvas */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#0a0a0b] telemetry-grid min-h-screen">
        {/* Global Race Header with time, live status, and search */}
        <RaceHeader
          onOpenSearch={() => setIsSearchOpen(true)}
          onOpenMobileMenu={() => setIsMobileNavOpen(true)}
          currentRaceName="Italian Grand Prix 2024 — Race"
          onSelectRace={() => handleNavigate('races')}
        />

        {/* Dynamic Operational View Area */}
        <main className="flex-1 overflow-y-auto">
          {currentView === 'dashboard' && (
            <DashboardView onNavigate={handleNavigate} />
          )}

          {currentView === 'races' && (
            <RacesView onNavigate={handleNavigate} />
          )}

          {currentView === 'incidents' && (
            <IncidentsView onNavigate={handleNavigate} />
          )}

          {currentView === 'incident-detail' && (
            <IncidentDetailView
              incidentId={activeIncidentId}
              onBack={() => handleNavigate('incidents')}
              onNavigate={handleNavigate}
            />
          )}

          {currentView === 'regulations' && (
            <RegulationsView onNavigate={handleNavigate} />
          )}

          {currentView === 'assistant' && (
            <AssistantView
              onNavigate={handleNavigate}
              preselectedIncidentId={activeIncidentId}
            />
          )}
        </main>
      </div>

      {/* Global Search Modal (Cmd+K) */}
      <GlobalSearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        onNavigate={handleNavigate}
      />
    </div>
  );
}
