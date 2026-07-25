import React from 'react';
import { motion } from 'framer-motion';
import { FiAlertTriangle, FiAlertOctagon, FiCheckCircle, FiCrosshair, FiMapPin, FiLayers } from 'react-icons/fi';
import ImageWithFallback from '../components/ImageWithFallback';

export default function DamagePage({ damageSummary }) {
  const summary = damageSummary || {
    total_count: 29,
    total_area_m2: 18.4,
    damage_types: ["Collapsed Section", "Leaning Wall", "Large Hole / Void"],
    instances: [
      {
        type: "Collapsed Section",
        location_xyz: [2.0, 1.0, 1.1],
        extent_m: 1.3,
        confidence: 0.85,
        description: "North-west wall section collapse detected at (2.00, 1.00, 1.10). Wall fragmented and debris distributed over 1.3m."
      },
      {
        type: "Leaning Wall",
        location_xyz: [3.0, -0.79, 0.65],
        extent_m: 15.81,
        confidence: 1.0,
        description: "East Wall region shows tilt of 18.4° from vertical. Immediate structural assessment required."
      },
      {
        type: "Large Hole / Void",
        location_xyz: [2.56, 3.35, 0.0],
        extent_m: 14.52,
        confidence: 1.0,
        description: "Significant floor void detected in main shelter bay."
      }
    ]
  };

  const getDamageBadge = (type) => {
    if (type.includes('Collapse')) {
      return { label: 'CRITICAL', color: 'bg-red-500/10 border-red-500/30 text-red-400', icon: FiAlertOctagon };
    } else if (type.includes('Leaning') || type.includes('Hole')) {
      return { label: 'HIGH', color: 'bg-orange-500/10 border-orange-500/30 text-orange-400', icon: FiAlertTriangle };
    } else if (type.includes('Roof')) {
      return { label: 'MEDIUM', color: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-300', icon: FiAlertTriangle };
    } else {
      return { label: 'LOW', color: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300', icon: FiCheckCircle };
    }
  };

  return (
    <div className="space-y-6 font-mono">
      {/* Header */}
      <div className="glass-panel p-6 rounded-2xl border border-cyan-500/30 flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FiAlertTriangle className="text-amber-400" />
            Structural Damage Detection & Spatial Heatmap
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            LiDAR Point Displacement & Normal Vector Deviation Analysis
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-bold bg-red-500/20 text-red-400 border border-red-500/30 animate-pulse">
          {summary.total_count || 29} ANOMALIES DETECTED
        </span>
      </div>

      {/* Grid of Heatmap & Damage Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Heatmap Image */}
        <div className="lg:col-span-2 glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <FiLayers className="text-cyan-400" />
            Damage Heatmap Spatial Distribution (`damage_heatmap.png`)
          </h3>

          <div className="h-80 w-full overflow-hidden rounded-xl">
            <ImageWithFallback
              src="/api/images/damage_heatmap.png"
              alt="Damage Heatmap"
              title="Spatial Structural Damage Heatmap"
              fallbackType="heatmap"
              className="h-full w-full"
            />
          </div>
        </div>

        {/* Quick Stats */}
        <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <FiCrosshair className="text-cyan-400" />
            Inspection Metrics
          </h3>

          <div className="space-y-3">
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-xs">Total Damaged Area</span>
              <div className="text-2xl font-bold text-red-400">{summary.total_area_m2 || 18.4} m²</div>
              <span className="text-[10px] text-slate-400">Shelter Coverage Penalty</span>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-xs">Max Wall Tilt</span>
              <div className="text-2xl font-bold text-orange-400">18.4° Tilt</div>
              <span className="text-[10px] text-slate-400">East Wall Alignment</span>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-xs">Detection Confidence</span>
              <div className="text-2xl font-bold text-cyan-300">95.0%</div>
              <span className="text-[10px] text-slate-400">Multi-ray LiDAR Consensus</span>
            </div>
          </div>
        </div>

      </div>

      {/* Detailed Instances Table */}
      <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <FiMapPin className="text-cyan-400" />
          Detected Structural Damage Instances
        </h3>

        <div className="space-y-3">
          {(summary.instances || []).map((inst, idx) => {
            const badge = getDamageBadge(inst.type);
            const Icon = badge.icon;
            return (
              <div key={idx} className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${badge.color}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="font-bold text-white text-sm">{inst.type}</h4>
                      <p className="text-[11px] text-cyan-400">
                        Coordinates: X: {inst.location_xyz[0]}m, Y: {inst.location_xyz[1]}m, Z: {inst.location_xyz[2]}m
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 text-xs">
                    <span className="text-slate-400">Extent: <strong className="text-white">{inst.extent_m}m</strong></span>
                    <span className="text-slate-400">Confidence: <strong className="text-cyan-300">{(inst.confidence * 100).toFixed(0)}%</strong></span>
                    <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${badge.color}`}>
                      {badge.label}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 pl-11">
                  {inst.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
