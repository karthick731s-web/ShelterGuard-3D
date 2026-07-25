import React, { useEffect, useRef, useState } from 'react';
import { FiTerminal, FiPlay, FiTrash2, FiSearch, FiCheck, FiCornerDownRight } from 'react-icons/fi';
import axios from 'axios';

export default function TerminalWidget({ logs = [], isRunning, onTriggerRun }) {
  const [autoScroll, setAutoScroll] = useState(true);
  const [filterText, setFilterText] = useState('');
  const terminalEndRef = useRef(null);

  // Auto scroll logic
  useEffect(() => {
    if (autoScroll && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  // Default initial log sequence if logs array is empty
  const logList = logs.length > 0 ? logs : [
    "2026-07-25 14:00:00 | INFO | [SYSTEM] 3D LiDAR Shelter Damage Inspection Node initialized.",
    "2026-07-25 14:00:01 | INFO | [ROBOT] TurtleBot3 (TB3-01) connected on /cmd_vel.",
    "2026-07-25 14:00:02 | INFO | [NAV2] Costmap loaded. Goal coordinate set to Shelter Bay A-4.",
    "2026-07-25 14:00:04 | INFO | [LIDAR] 360° Laser Scan active. Scanning 360 rays @ 10 Hz.",
    "2026-07-25 14:00:06 | INFO | [POINTCLOUD] Accumulated 202,322 valid 3D points.",
    "2026-07-25 14:00:08 | WARN | [MAPPING] Structural irregularity detected at (X: 2.0, Y: 1.0, Z: 1.1).",
    "2026-07-25 14:00:10 | ERROR| [DAMAGE] Structural Collapse detected! Area: 18.4 m² | Tilt: 18.4°",
    "2026-07-25 14:00:12 | WARN | [SEVERITY] Calculated Score: 86.8 / 100 -> Risk: CRITICAL",
    "2026-07-25 14:00:14 | SUCCESS | [REPORT] inspection_report.txt and inspection_summary.json saved."
  ];

  const filteredLogs = logList.filter(log =>
    log.toLowerCase().includes(filterText.toLowerCase())
  );

  const getLogStyle = (line) => {
    if (line.includes('ERROR') || line.includes('CRITICAL') || line.includes('Collapse')) {
      return 'text-red-400 font-semibold bg-red-950/20 px-1 py-0.5 rounded';
    } else if (line.includes('WARN') || line.includes('Tilt')) {
      return 'text-amber-300 font-semibold';
    } else if (line.includes('SUCCESS') || line.includes('Completed') || line.includes('saved')) {
      return 'text-emerald-400 font-bold';
    } else if (line.includes('INFO')) {
      return 'text-cyan-300';
    } else {
      return 'text-slate-300';
    }
  };

  return (
    <div className="glass-panel rounded-2xl border border-slate-800 flex flex-col h-full overflow-hidden shadow-2xl">
      {/* Header Bar */}
      <div className="px-5 py-3 border-b border-slate-800 bg-slate-950/80 flex flex-wrap items-center justify-between gap-3 font-mono">
        <div className="flex items-center gap-2 text-cyan-400">
          <FiTerminal className="w-4 h-4" />
          <span className="text-xs font-bold text-white tracking-wider uppercase">Live Telemetry Terminal</span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
            /api/logs
          </span>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3 text-xs">
          {/* Search Input */}
          <div className="relative flex items-center">
            <FiSearch className="absolute left-2.5 text-slate-500 w-3.5 h-3.5" />
            <input
              type="text"
              placeholder="Filter logs..."
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              className="pl-8 pr-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 text-xs font-mono"
            />
          </div>

          {/* Auto scroll checkbox */}
          <label className="flex items-center gap-1.5 cursor-pointer text-slate-400 hover:text-slate-200">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="rounded bg-slate-900 border-slate-800 text-cyan-500 focus:ring-0"
            />
            <span className="text-[11px]">Auto-scroll</span>
          </label>

          {/* Trigger Button */}
          {onTriggerRun && (
            <button
              onClick={onTriggerRun}
              disabled={isRunning}
              className="px-3 py-1 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold transition flex items-center gap-1 text-xs"
            >
              <FiPlay className="w-3 h-3" />
              <span>Run System</span>
            </button>
          )}
        </div>
      </div>

      {/* Terminal Viewport */}
      <div className="flex-1 p-4 bg-[#050811] font-mono text-xs overflow-y-auto space-y-1.5 min-h-[300px] max-h-[500px]">
        {filteredLogs.map((line, idx) => (
          <div key={idx} className="flex items-start gap-2 leading-relaxed hover:bg-slate-900/40 px-1 py-0.5 rounded">
            <span className="text-slate-600 select-none text-[10px] w-6 shrink-0 text-right">
              {idx + 1}
            </span>
            <FiCornerDownRight className="w-3 h-3 text-slate-600 shrink-0 mt-0.5" />
            <span className={getLogStyle(line)}>
              {line}
            </span>
          </div>
        ))}
        {/* Scroll Anchor */}
        <div ref={terminalEndRef} />
      </div>

      {/* Status Bar */}
      <div className="px-4 py-2 border-t border-slate-900 bg-slate-950 text-[11px] font-mono text-slate-500 flex justify-between items-center">
        <span>Log Stream: <strong className="text-cyan-400">{filteredLogs.length} Lines</strong></span>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-slate-400">ROS2 Topic Listener Active</span>
        </div>
      </div>
    </div>
  );
}
