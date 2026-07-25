import React from 'react';
import { motion } from 'framer-motion';
import { FiInfo, FiCpu, FiLayers, FiServer, FiCheckCircle, FiShield, FiCode } from 'react-icons/fi';

export default function AboutPage() {
  const techStack = [
    { name: 'React 18 & Vite', category: 'Frontend Framework', desc: 'Fast client UI rendering with HMR' },
    { name: 'Tailwind CSS', category: 'Styling Engine', desc: 'Custom glassmorphic dark design system' },
    { name: 'Framer Motion', category: 'Animations', desc: 'Hardware accelerated UI transitions' },
    { name: 'Three.js', category: '3D Point Cloud Graphics', desc: 'Interactive 3D point cloud rendering' },
    { name: 'ROS2 Humble', category: 'Robotics Core', desc: 'Robot navigation & 3D LiDAR point node' },
    { name: 'Flask & CORS', category: 'Backend API Server', desc: 'REST server exposing telemetry & reports' },
    { name: 'Open3D & NumPy', category: 'Point Processing', desc: '3D cloud filtering & damage detection' },
  ];

  const apiEndpoints = [
    { method: 'GET', path: '/api/status', desc: 'Returns robot status, battery, position, & execution state' },
    { method: 'GET', path: '/api/inspection', desc: 'Returns full inspection summary JSON & damage arrays' },
    { method: 'GET', path: '/api/report', desc: 'Returns raw TXT inspection report file text' },
    { method: 'GET', path: '/api/logs', desc: 'Returns live system log stream entries' },
    { method: 'GET', path: '/api/images/<file>', desc: 'Serves generated point cloud, map, & heatmap PNGs' },
    { method: 'POST', path: '/api/run-inspection', desc: 'Triggers live pipeline worker process thread' },
  ];

  return (
    <div className="space-y-6 font-mono">
      {/* Header */}
      <div className="glass-panel p-6 rounded-2xl border border-cyan-500/30 flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FiInfo className="text-cyan-400" />
            About 3D LiDAR Shelter Inspection System
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Disaster Response Command Center Architecture & Technical Specifications
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
          v1.0.0 RELEASE
        </span>
      </div>

      {/* Grid of Tech Stack & System Specs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Tech Stack */}
        <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <FiCode className="text-cyan-400" />
            Full Tech Stack Architecture
          </h3>

          <div className="space-y-2.5">
            {techStack.map((tech, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex justify-between items-center text-xs">
                <div>
                  <h4 className="font-bold text-white">{tech.name}</h4>
                  <p className="text-[11px] text-slate-400">{tech.desc}</p>
                </div>
                <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 text-[10px] font-bold">
                  {tech.category}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* API Server Endpoints */}
        <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <FiServer className="text-cyan-400" />
            Backend REST API Endpoints (`server.py`)
          </h3>

          <div className="space-y-2.5">
            {apiEndpoints.map((ep, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex justify-between items-center text-xs">
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      ep.method === 'POST' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    }`}>
                      {ep.method}
                    </span>
                    <code className="text-cyan-300 font-bold">{ep.path}</code>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">{ep.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
