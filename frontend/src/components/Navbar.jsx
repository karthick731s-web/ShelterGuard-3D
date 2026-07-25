import React, { useState, useEffect } from 'react';
import { 
  FiShield, 
  FiWifi, 
  FiBatteryCharging, 
  FiClock, 
  FiPlay, 
  FiAlertTriangle,
  FiCpu
} from 'react-icons/fi';
import axios from 'axios';

export default function Navbar({ statusData, onTriggerRun }) {
  const [time, setTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const isRunning = statusData?.is_running;

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
      {/* Brand Title */}
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/30 text-cyan-400 shadow-lg shadow-cyan-950/50">
          <FiShield className="w-6 h-6 animate-pulse-slow" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-bold text-lg tracking-wide text-white font-mono">
              3D LiDAR Shelter Inspection
            </h1>
            <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              COMMAND CENTER
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            Autonomous Structural Damage Assessment Platform
          </p>
        </div>
      </div>

      {/* Live Status Indicators */}
      <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
        {/* Robot Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800">
          <FiCpu className="text-cyan-400 w-4 h-4" />
          <span className="text-slate-400">ROBOT:</span>
          <span className="font-bold text-cyan-300">{statusData?.robot_id || 'TB3-01'}</span>
        </div>

        {/* Battery Indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800">
          <FiBatteryCharging className="text-emerald-400 w-4 h-4" />
          <span className="text-slate-400">BATTERY:</span>
          <span className="font-bold text-emerald-400">{statusData?.battery_pct ?? 98}%</span>
        </div>

        {/* Connection Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800">
          <span className={`w-2.5 h-2.5 rounded-full ${isRunning ? 'bg-amber-400 animate-ping' : 'bg-emerald-400'}`}></span>
          <FiWifi className="text-slate-400 w-3.5 h-3.5" />
          <span className="font-semibold text-slate-200">
            {isRunning ? 'INSPECTING...' : 'ONLINE'}
          </span>
        </div>

        {/* Clock */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-300">
          <FiClock className="text-blue-400 w-3.5 h-3.5" />
          <span>{time}</span>
        </div>

        {/* CTA Trigger Button */}
        <button
          onClick={onTriggerRun}
          disabled={isRunning}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition-all shadow-md ${
            isRunning
              ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
              : 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold border border-cyan-400/50 shadow-cyan-900/40 active:scale-95'
          }`}
        >
          <FiPlay className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
          <span>{isRunning ? 'Pipeline Active' : 'Start Inspection'}</span>
        </button>
      </div>
    </header>
  );
}
