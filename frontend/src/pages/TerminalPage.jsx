import React from 'react';
import TerminalWidget from '../components/TerminalWidget';
import { FiTerminal } from 'react-icons/fi';

export default function TerminalPage({ logs, isRunning, onTriggerRun }) {
  return (
    <div className="space-y-6 font-mono">
      {/* Header */}
      <div className="glass-panel p-6 rounded-2xl border border-cyan-500/30 flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FiTerminal className="text-cyan-400" />
            Live System Log Terminal Stream
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-Time Output Stream from Python & ROS2 Autonomous Nodes
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          ROS2 Stream Active
        </span>
      </div>

      {/* Terminal Widget */}
      <div className="h-[70vh]">
        <TerminalWidget 
          logs={logs} 
          isRunning={isRunning} 
          onTriggerRun={onTriggerRun} 
        />
      </div>
    </div>
  );
}
