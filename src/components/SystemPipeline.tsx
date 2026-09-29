import React from 'react';

export const SystemPipeline: React.FC = () => {
  const stages = [
    { name: 'FastF1 Ingest', status: 'COMPLETED', latency: '24ms' },
    { name: 'Telemetry Processing', status: 'COMPLETED', latency: '38ms' },
    { name: 'Incident Reconstruction', status: 'COMPLETED', latency: '82ms' },
    { name: 'Evidence Analysis', status: 'COMPLETED', latency: '45ms' },
    { name: 'Regulation Retrieval', status: 'COMPLETED', latency: '12ms' },
    { name: 'Human Steward Review', status: 'IN_PROGRESS', latency: 'Active' },
  ];

  return (
    <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="text-xs font-bold text-white tracking-[0.2em] font-tech uppercase">
          EVIDENCE PROCESSING PIPELINE
        </div>
        <div className="text-[10px] font-mono text-emerald-500 flex items-center gap-1.5 font-semibold">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          REAL-TIME PIPELINE ACTIVE
        </div>
      </div>

      {/* Pipeline Grid / Flow */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {stages.map((stage, idx) => {
          const isHuman = stage.status === 'IN_PROGRESS';
          return (
            <div 
              key={idx}
              className={`p-3 rounded-sm border flex flex-col justify-between ${
                isHuman 
                  ? 'bg-red-600/10 border-red-600/40 text-white' 
                  : 'bg-white/5 border-white/10 text-white/80'
              }`}
            >
              <div>
                <div className="text-[9px] font-mono text-white/40 uppercase tracking-widest mb-1 font-bold">
                  STAGE 0{idx + 1}
                </div>
                <div className="text-xs font-semibold font-tech uppercase tracking-wide leading-tight">
                  {stage.name}
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-white/5 flex items-center justify-between text-[10px] font-mono">
                <span className={isHuman ? 'text-red-500 font-bold animate-pulse' : 'text-emerald-500'}>
                  {isHuman ? '● AWAITING' : '✓ DONE'}
                </span>
                <span className="text-white/40">{stage.latency}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
