import React from 'react';
import { motion } from 'framer-motion';
import { FiDisc, FiRadio, FiLayers, FiBarChart2, FiCheckCircle } from 'react-icons/fi';

export default function LidarPage({ scanStats }) {
  const stats = scanStats || { total_scans: 8, total_points: 202322, valid_points: 199926 };

  const scanPasses = [
    { pass: 1, height: '0.2m (Floor)', points: 25100, valid: 24800 },
    { pass: 2, height: '0.6m (Lower Wall)', points: 26400, valid: 26100 },
    { pass: 3, height: '1.0m (Mid Wall)', points: 24900, valid: 24650 },
    { pass: 4, height: '1.4m (Upper Wall)', points: 25800, valid: 25500 },
    { pass: 5, height: '1.8m (Roof Base)', points: 25200, valid: 24900 },
    { pass: 6, height: '2.2m (Ceiling)', points: 24800, valid: 24500 },
    { pass: 7, height: '2.6m (Apex)', points: 25122, valid: 24856 },
    { pass: 8, height: '3.0m (Top Inspection)', points: 25000, valid: 24620 },
  ];

  return (
    <div className="space-y-6 font-mono">
      {/* Header */}
      <div className="glass-panel p-6 rounded-2xl border border-cyan-500/30 flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FiDisc className="text-cyan-400 animate-spin-slow" />
            360° 3D LiDAR Scanner Telemetry
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Multilayer Laser Range Finder • 360 Rays per Pass @ 10 Hz Scanning Rate
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
          360° FOV ACTIVE
        </span>
      </div>

      {/* Grid Specs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card p-4 rounded-xl border border-slate-800">
          <span className="text-slate-500 text-xs">Laser Ray Count</span>
          <div className="text-2xl font-bold text-cyan-300">360 Rays / Pass</div>
          <span className="text-[10px] text-slate-400">Angular Res: 1.0°</span>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800">
          <span className="text-slate-500 text-xs">Total Scan Passes</span>
          <div className="text-2xl font-bold text-slate-100">{stats.total_scans || 8} Multi-Passes</div>
          <span className="text-[10px] text-slate-400">Z-Range: 0.2m to 3.0m</span>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800">
          <span className="text-slate-500 text-xs">Scan Frequency</span>
          <div className="text-2xl font-bold text-emerald-400">10.0 Hz</div>
          <span className="text-[10px] text-slate-400">Time per revolution: 100ms</span>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800">
          <span className="text-slate-500 text-xs">Valid Point Ratio</span>
          <div className="text-2xl font-bold text-cyan-400">98.8%</div>
          <span className="text-[10px] text-slate-400">199,926 / 202,322 Valid</span>
        </div>
      </div>

      {/* Table of Scan Passes */}
      <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <FiLayers className="text-cyan-400" />
          Multi-Pass Elevation Scan Statistics
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="py-2.5 px-3">Pass #</th>
                <th className="py-2.5 px-3">Elevation Level</th>
                <th className="py-2.5 px-3">Total Points Captured</th>
                <th className="py-2.5 px-3">Filtered Valid Points</th>
                <th className="py-2.5 px-3">Pass Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              {scanPasses.map((p) => (
                <tr key={p.pass} className="hover:bg-slate-900/40 transition">
                  <td className="py-2.5 px-3 font-bold text-cyan-300">Pass 0{p.pass}</td>
                  <td className="py-2.5 px-3">{p.height}</td>
                  <td className="py-2.5 px-3">{p.points.toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-emerald-400 font-bold">{p.valid.toLocaleString()}</td>
                  <td className="py-2.5 px-3">
                    <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold">
                      SUCCESS
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
