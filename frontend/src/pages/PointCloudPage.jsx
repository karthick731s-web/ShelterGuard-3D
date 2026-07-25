import React from 'react';
import { motion } from 'framer-motion';
import { FiBox, FiMaximize2, FiLayers, FiDatabase, FiCheckCircle } from 'react-icons/fi';
import ImageWithFallback from '../components/ImageWithFallback';

export default function PointCloudPage({ scanStats, onOpen3D }) {
  const stats = scanStats || { total_points: 202322, valid_points: 199926 };

  return (
    <div className="space-y-6 font-mono">
      {/* Header */}
      <div className="glass-panel p-6 rounded-2xl border border-cyan-500/30 flex flex-wrap justify-between items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FiBox className="text-cyan-400" />
            3D Point Cloud Processing & Filtering
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Open3D Point Cloud Filtering • Outlier Removal & Normal Estimation
          </p>
        </div>

        <button
          onClick={onOpen3D}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs flex items-center gap-2 shadow-xl shadow-cyan-950/50 transition active:scale-95"
        >
          <FiMaximize2 className="w-4 h-4" />
          <span>Launch Fullscreen 3D View</span>
        </button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card p-4 rounded-xl border border-slate-800">
          <span className="text-slate-500 text-xs">Total Captured Points</span>
          <div className="text-2xl font-bold text-cyan-300">{(stats.total_points || 202322).toLocaleString()}</div>
          <span className="text-[10px] text-slate-400 font-mono">Raw Scan Array</span>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800">
          <span className="text-slate-500 text-xs">Filtered Valid Points</span>
          <div className="text-2xl font-bold text-emerald-400">{(stats.valid_points || 199926).toLocaleString()}</div>
          <span className="text-[10px] text-slate-400 font-mono">Statistical Outlier Removed</span>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800">
          <span className="text-slate-500 text-xs">Voxel Grid Resolution</span>
          <div className="text-2xl font-bold text-slate-100">0.05 m</div>
          <span className="text-[10px] text-cyan-400 font-mono">5cm Sub-sampling</span>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800">
          <span className="text-slate-500 text-xs">Point Density</span>
          <div className="text-2xl font-bold text-amber-300">1,420 pts/m³</div>
          <span className="text-[10px] text-slate-400 font-mono">High Precision Range</span>
        </div>
      </div>

      {/* Main Image & Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <FiLayers className="text-cyan-400" />
            Rendered 3D Point Cloud Visualizer
          </h3>

          <div className="h-80 w-full overflow-hidden rounded-xl">
            <ImageWithFallback
              src="/api/images/point_cloud.png"
              alt="3D Point Cloud Preview"
              title="3D Point Cloud Field"
              fallbackType="pointcloud"
              className="h-full w-full"
            />
          </div>
        </div>

        <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <FiDatabase className="text-cyan-400" />
            Processing Pipeline
          </h3>

          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <span className="text-cyan-400 font-bold">Step 1: Point Acquisition</span>
              <p className="text-slate-400 text-[11px]">8 rotational scan passes combined into unified XYZ point matrix.</p>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <span className="text-cyan-400 font-bold">Step 2: Noise Reduction</span>
              <p className="text-slate-400 text-[11px]">SOR (Statistical Outlier Removal) filtered 2,396 noise points.</p>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <span className="text-cyan-400 font-bold">Step 3: Surface Reconstruction</span>
              <p className="text-slate-400 text-[11px]">Calculated normal vectors for wall inclination and void detection.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
