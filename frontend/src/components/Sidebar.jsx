import React from 'react';
import { 
  FiGrid, 
  FiNavigation, 
  FiDisc, 
  FiBox, 
  FiAlertTriangle, 
  FiFileText, 
  FiTerminal, 
  FiGitCommit, 
  FiInfo,
  FiActivity
} from 'react-icons/fi';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: FiGrid, badge: 'Live' },
  { id: 'robot', label: 'Robot Telemetry', icon: FiNavigation },
  { id: 'lidar', label: '360° LiDAR', icon: FiDisc },
  { id: 'pointcloud', label: 'Point Cloud', icon: FiBox, badge: '3D' },
  { id: 'damage', label: 'Damage Detection', icon: FiAlertTriangle, badgeColor: 'text-amber-400 border-amber-500/30' },
  { id: 'report', label: 'Inspection Report', icon: FiFileText },
  { id: 'terminal', label: 'Live Terminal', icon: FiTerminal },
  { id: 'workflow', label: 'Workflow', icon: FiGitCommit },
  { id: 'about', label: 'About System', icon: FiInfo },
];

export default function Sidebar({ activeTab, setActiveTab, statusData, damageCount }) {
  return (
    <aside className="w-64 shrink-0 glass-panel border-r border-slate-800/80 flex flex-col justify-between hidden md:flex min-h-[calc(100vh-65px)] sticky top-[65px]">
      {/* Navigation Links */}
      <div className="p-4 space-y-1.5">
        <div className="px-3 py-2 text-[11px] font-mono font-semibold tracking-wider text-slate-500 uppercase">
          Command Controls
        </div>

        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-mono text-xs transition-all group ${
                isActive
                  ? 'bg-gradient-to-r from-cyan-500/20 to-blue-600/10 text-cyan-300 border border-cyan-500/30 font-semibold shadow-lg shadow-cyan-950/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 transition-transform group-hover:scale-110 ${
                  isActive ? 'text-cyan-400' : 'text-slate-500 group-hover:text-cyan-400'
                }`} />
                <span>{item.label}</span>
              </div>

              {/* Badges */}
              {item.id === 'damage' && damageCount > 0 && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-red-500/20 text-red-400 border border-red-500/30 animate-pulse">
                  {damageCount}
                </span>
              )}
              {item.badge && item.id !== 'damage' && (
                <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase border bg-cyan-500/10 text-cyan-400 border-cyan-500/30`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* System Quick Status Widget */}
      <div className="p-4 m-3 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-950 border border-slate-800/80 space-y-3 font-mono text-xs">
        <div className="flex items-center justify-between text-slate-400">
          <div className="flex items-center gap-2">
            <FiActivity className="text-cyan-400 animate-pulse" />
            <span className="font-semibold text-slate-300">System Telemetry</span>
          </div>
          <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/30 font-bold">
            READY
          </span>
        </div>

        <div className="space-y-1.5 text-[11px]">
          <div className="flex justify-between">
            <span className="text-slate-500">Robot Model:</span>
            <span className="text-cyan-300 font-bold">TurtleBot3 Waffle</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Sensor:</span>
            <span className="text-slate-300">3D 360° LiDAR</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">ROS 2 Humble:</span>
            <span className="text-emerald-400 font-semibold">Active</span>
          </div>
        </div>

        <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
          <span>Lat: 0.12ms</span>
          <span>FPS: 60.0</span>
        </div>
      </div>
    </aside>
  );
}
