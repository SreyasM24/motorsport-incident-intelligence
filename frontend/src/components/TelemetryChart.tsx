import React, { useState } from 'react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  ReferenceLine,
  ReferenceArea
} from 'recharts';
import { TelemetryPoint } from '../lib/types';
import { 
  Activity, 
  Gauge, 
  Compass, 
  TrendingDown
} from 'lucide-react';

interface TelemetryChartProps {
  data: TelemetryPoint[];
  driverA?: string;
  driverB?: string;
  currentTime?: string;
  onTimeSelect?: (timestamp: string) => void;
}

export const TelemetryChart: React.FC<TelemetryChartProps> = ({
  data,
  driverA = 'VER',
  driverB = 'HAM',
  currentTime,
  onTimeSelect,
}) => {
  const [driverMode, setDriverMode] = useState<'BOTH' | 'A' | 'B'>('BOTH');
  const [activeChannel, setActiveChannel] = useState<'ALL' | 'SPEED' | 'PEDALS' | 'GAP_SPEED' | 'ACCEL'>('ALL');
  const [hoveredPoint, setHoveredPoint] = useState<TelemetryPoint | null>(data[25] || data[0]);

  const colorA = '#E10600'; // VER Trace (High-contrast red from theme)
  const colorB = '#4444FF'; // HAM Trace (High-contrast blue from theme)

  const activeDataPoint = hoveredPoint || data[25] || data[0];

  const handleMouseMove = (state: any) => {
    if (state && state.activePayload && state.activePayload.length > 0) {
      const point = state.activePayload[0].payload as TelemetryPoint;
      setHoveredPoint(point);
      if (onTimeSelect && point.timestamp) {
        onTimeSelect(point.timestamp);
      }
    }
  };

  return (
    <div className="bg-[#0d0d0f] border border-white/10 rounded-sm overflow-hidden">
      {/* Header & Controls */}
      <div className="p-4 md:p-6 border-b border-white/10 bg-[#0a0a0b] flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Activity className="w-4 h-4 text-red-600" />
          <div>
            <div className="text-xs font-bold text-white tracking-[0.2em] font-tech uppercase">
              SYNCHRONIZED TELEMETRY EVIDENCE
            </div>
            <div className="text-[10px] font-mono text-white/40 mt-0.5">
              FastF1 ECU CAN-Bus Ingest • 25 Hz Precision
            </div>
          </div>
        </div>

        {/* View mode & Driver Filter Controls */}
        <div className="flex items-center gap-3">
          {/* Driver Toggle */}
          <div className="flex items-center bg-[#0a0a0b] border border-white/10 rounded-sm p-0.5 text-[11px] font-mono">
            <button
              onClick={() => setDriverMode('BOTH')}
              className={`px-2.5 py-1 rounded-sm transition-colors ${
                driverMode === 'BOTH' ? 'bg-white/10 text-white font-bold' : 'text-white/40 hover:text-white'
              }`}
            >
              Both Cars
            </button>
            <button
              onClick={() => setDriverMode('A')}
              className={`px-2.5 py-1 rounded-sm transition-colors flex items-center gap-1.5 ${
                driverMode === 'A' ? 'bg-white/10 text-white font-bold' : 'text-white/40 hover:text-white'
              }`}
            >
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: colorA }} />
              {driverA} #1
            </button>
            <button
              onClick={() => setDriverMode('B')}
              className={`px-2.5 py-1 rounded-sm transition-colors flex items-center gap-1.5 ${
                driverMode === 'B' ? 'bg-white/10 text-white font-bold' : 'text-white/40 hover:text-white'
              }`}
            >
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: colorB }} />
              {driverB} #44
            </button>
          </div>

          {/* Channel Selectors */}
          <div className="hidden lg:flex items-center bg-[#0a0a0b] border border-white/10 rounded-sm p-0.5 text-[11px] font-mono">
            {(['ALL', 'SPEED', 'PEDALS', 'GAP_SPEED', 'ACCEL'] as const).map((channel) => (
              <button
                key={channel}
                onClick={() => setActiveChannel(channel)}
                className={`px-2.5 py-1 rounded-sm uppercase tracking-wider text-[10px] transition-colors ${
                  activeChannel === channel
                    ? 'bg-white/15 text-white font-semibold'
                    : 'text-white/40 hover:text-white'
                }`}
              >
                {channel === 'ALL' ? 'All Channels' : channel.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Real-time Telemetry Readout & Summary Metrics (Matches Design Mockup) */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 bg-[#0a0a0b]/60 border-b border-white/10">
        <div className="bg-white/5 rounded-sm p-3 flex flex-col justify-center">
          <span className="text-[10px] text-white/40 uppercase font-mono mb-1">Delta-V</span>
          <span className="font-mono text-xl text-white">
            {(activeDataPoint.speedA - activeDataPoint.speedB).toFixed(1)} <span className="text-xs opacity-50">km/h</span>
          </span>
        </div>

        <div className="bg-white/5 rounded-sm p-3 flex flex-col justify-center">
          <span className="text-[10px] text-white/40 uppercase font-mono mb-1">Min Gap</span>
          <span className="font-mono text-xl text-white">
            {activeDataPoint.gapMeters.toFixed(2)} <span className="text-xs opacity-50">m</span>
          </span>
        </div>

        <div className="bg-white/5 rounded-sm p-3 flex flex-col justify-center">
          <span className="text-[10px] text-white/40 uppercase font-mono mb-1">Impact Prob</span>
          <span className="font-mono text-xl text-white">
            12 <span className="text-xs opacity-50">%</span>
          </span>
        </div>

        <div className="bg-white/5 rounded-sm p-3 flex flex-col justify-center border border-red-600/20">
          <span className="text-[10px] text-red-500 uppercase font-mono mb-1 font-bold">Relative Motion</span>
          <span className="font-mono text-xl text-red-500 font-bold">CRITICAL</span>
        </div>
      </div>

      {/* Telemetry Charts Body */}
      <div className="p-6 space-y-6">
        {/* CHART 1: SPEED TRACE */}
        {(activeChannel === 'ALL' || activeChannel === 'SPEED') && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[11px] font-mono text-white/40 px-1">
              <span className="flex items-center gap-1.5 font-semibold text-white/90">
                <Gauge className="w-3.5 h-3.5 text-white/40" />
                VELOCITY (KM/H)
              </span>
              <div className="flex items-center gap-4 text-[10px]">
                {(driverMode === 'BOTH' || driverMode === 'A') && (
                  <span className="flex items-center gap-1" style={{ color: colorA }}>
                    ■ VER #1 ({activeDataPoint.speedA} km/h)
                  </span>
                )}
                {(driverMode === 'BOTH' || driverMode === 'B') && (
                  <span className="flex items-center gap-1" style={{ color: colorB }}>
                    ■ HAM #44 ({activeDataPoint.speedB} km/h)
                  </span>
                )}
              </div>
            </div>
            <div className="h-36 w-full bg-white/5 border border-white/5 rounded-sm p-2 relative">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} onMouseMove={handleMouseMove} margin={{ top: 12, right: 12, left: -20, bottom: 0 }}>
                  <XAxis dataKey="timestamp" hide />
                  <YAxis domain={[100, 360]} stroke="#52525b" fontSize={10} tickFormatter={(v) => `${v}`} />
                  <ReferenceArea {...({ x1: "13:42:18.1", x2: "13:42:18.8", fill: "#eab308", fillOpacity: 0.12 } as any)} />
                  <ReferenceLine x="13:42:18.4" stroke="#eab308" strokeDasharray="3 3" />
                  {(driverMode === 'BOTH' || driverMode === 'A') && (
                    <Line type="monotone" dataKey="speedA" stroke={colorA} strokeWidth={2} dot={false} isAnimationActive={false} />
                  )}
                  {(driverMode === 'BOTH' || driverMode === 'B') && (
                    <Line type="monotone" dataKey="speedB" stroke={colorB} strokeWidth={2} strokeDasharray="4 2" dot={false} isAnimationActive={false} />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* CHART 2: THROTTLE & BRAKE PEDALS */}
        {(activeChannel === 'ALL' || activeChannel === 'PEDALS') && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[11px] font-mono text-white/40 px-1">
              <span className="text-white/90 font-semibold">
                BRAKING & THROTTLE INPUT (%)
              </span>
              <div className="flex items-center gap-3 text-[10px]">
                <span className="text-white/40">Solid = Throttle, Dashed = Brake</span>
              </div>
            </div>
            <div className="h-32 w-full bg-white/5 border border-white/5 rounded-sm p-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} onMouseMove={handleMouseMove} margin={{ top: 12, right: 12, left: -20, bottom: 0 }}>
                  <XAxis dataKey="timestamp" hide />
                  <YAxis domain={[0, 100]} stroke="#52525b" fontSize={10} tickFormatter={(v) => `${v}%`} />
                  <ReferenceLine x="13:42:18.4" stroke="#eab308" strokeDasharray="3 3" />
                  {(driverMode === 'BOTH' || driverMode === 'A') && (
                    <>
                      <Line type="monotone" dataKey="throttleA" stroke={colorA} strokeWidth={1.8} dot={false} isAnimationActive={false} />
                      <Line type="monotone" dataKey="brakeA" stroke={colorA} strokeDasharray="4 2" strokeWidth={1.8} dot={false} isAnimationActive={false} />
                    </>
                  )}
                  {(driverMode === 'BOTH' || driverMode === 'B') && (
                    <>
                      <Line type="monotone" dataKey="throttleB" stroke={colorB} strokeWidth={1.8} dot={false} isAnimationActive={false} />
                      <Line type="monotone" dataKey="brakeB" stroke={colorB} strokeDasharray="4 2" strokeWidth={1.8} dot={false} isAnimationActive={false} />
                    </>
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* CHART 3: GAP DISTANCE & CLOSING SPEED */}
        {(activeChannel === 'ALL' || activeChannel === 'GAP_SPEED') && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[11px] font-mono text-white/40 px-1">
              <span className="flex items-center gap-1.5 font-semibold text-white/90">
                <TrendingDown className="w-3.5 h-3.5 text-red-500" />
                INTERACTION GAP (m) & CLOSING VELOCITY (m/s)
              </span>
              <div className="flex items-center gap-3 text-[10px]">
                <span className="text-amber-400">■ Distance (Min 1.82m)</span>
                <span className="text-cyan-400">■ Closing Speed (+8.42 m/s peak)</span>
              </div>
            </div>
            <div className="h-32 w-full bg-white/5 border border-white/5 rounded-sm p-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} onMouseMove={handleMouseMove} margin={{ top: 12, right: 12, left: -20, bottom: 0 }}>
                  <XAxis dataKey="timestamp" hide />
                  <YAxis yAxisId="left" domain={[0, 16]} stroke="#52525b" fontSize={10} tickFormatter={(v) => `${v}m`} />
                  <YAxis yAxisId="right" orientation="right" domain={[-5, 12]} stroke="#52525b" fontSize={10} tickFormatter={(v) => `${v}m/s`} />
                  <ReferenceLine yAxisId="left" y={2.0} stroke="#dc2626" strokeDasharray="3 3" label={{ value: '2.0m Proximity Threshold', fill: '#dc2626', fontSize: 9 }} />
                  <ReferenceLine yAxisId="left" x="13:42:18.4" stroke="#eab308" />
                  <Line yAxisId="left" type="monotone" dataKey="gapMeters" stroke="#f59e0b" strokeWidth={2} dot={false} isAnimationActive={false} />
                  <Line yAxisId="right" type="monotone" dataKey="closingSpeedMs" stroke="#06b6d4" strokeWidth={1.8} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* CHART 4: STEERING & ACCELERATION (G) */}
        {(activeChannel === 'ALL' || activeChannel === 'ACCEL') && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[11px] font-mono text-white/40 px-1">
              <span className="flex items-center gap-1.5 font-semibold text-white/90">
                <Compass className="w-3.5 h-3.5 text-purple-400" />
                STEERING ANGLE (deg) & LATERAL ACCELERATION (G)
              </span>
              <div className="text-[10px] font-mono text-white/40">
                Synchronized 25Hz Time X-Axis
              </div>
            </div>
            <div className="h-32 w-full bg-white/5 border border-white/5 rounded-sm p-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} onMouseMove={handleMouseMove} margin={{ top: 12, right: 12, left: -20, bottom: 20 }}>
                  <XAxis dataKey="timestamp" stroke="#52525b" fontSize={10} tickMargin={6} />
                  <YAxis domain={[-35, 35]} stroke="#52525b" fontSize={10} tickFormatter={(v) => `${v}°`} />
                  <ReferenceLine x="13:42:18.4" stroke="#eab308" strokeDasharray="3 3" />
                  {(driverMode === 'BOTH' || driverMode === 'A') && (
                    <Line type="monotone" dataKey="steerA" stroke={colorA} strokeWidth={1.8} dot={false} isAnimationActive={false} />
                  )}
                  {(driverMode === 'BOTH' || driverMode === 'B') && (
                    <Line type="monotone" dataKey="steerB" stroke={colorB} strokeWidth={1.8} strokeDasharray="4 2" dot={false} isAnimationActive={false} />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
