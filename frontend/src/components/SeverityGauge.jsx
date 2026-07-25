import React from 'react';
import { motion } from 'framer-motion';
import { FiShield, FiAlertTriangle, FiAlertOctagon, FiCheckCircle } from 'react-icons/fi';

export default function SeverityGauge({ score = 86.8, riskLevel = "CRITICAL", factors }) {
  // Normalize score between 0 and 100
  const normalizedScore = Math.min(Math.max(score, 0), 100);
  
  // Calculate SVG arc parameters
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  // Semi-circle gauge (180 degrees)
  const strokeDashoffset = circumference - (normalizedScore / 100) * (circumference * 0.75);

  const getRiskDetails = (score, riskStr) => {
    const level = (riskStr || '').toUpperCase();
    if (score >= 80 || level === 'CRITICAL') {
      return {
        label: 'CRITICAL',
        color: 'text-red-500',
        stroke: '#ef4444',
        glow: 'glow-red',
        bg: 'bg-red-500/10 border-red-500/30 text-red-400',
        icon: FiAlertOctagon,
        desc: 'Imminent collapse hazard detected. Prohibit entry.'
      };
    } else if (score >= 60 || level === 'HIGH') {
      return {
        label: 'HIGH',
        color: 'text-orange-500',
        stroke: '#f97316',
        glow: 'glow-amber',
        bg: 'bg-orange-500/10 border-orange-500/30 text-orange-400',
        icon: FiAlertTriangle,
        desc: 'Major structural damage detected. Restrict access.'
      };
    } else if (score >= 40 || level === 'MEDIUM') {
      return {
        label: 'MEDIUM',
        color: 'text-yellow-400',
        stroke: '#eab308',
        glow: 'glow-amber',
        bg: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-300',
        icon: FiAlertTriangle,
        desc: 'Moderate deformation. Secondary inspection recommended.'
      };
    } else if (score >= 20 || level === 'LOW') {
      return {
        label: 'LOW',
        color: 'text-emerald-400',
        stroke: '#10b981',
        glow: 'glow-emerald',
        bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300',
        icon: FiCheckCircle,
        desc: 'Minor cosmetic cracks. Structure stable.'
      };
    } else {
      return {
        label: 'SAFE',
        color: 'text-cyan-400',
        stroke: '#06b6d4',
        glow: 'glow-cyan',
        bg: 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300',
        icon: FiShield,
        desc: 'No significant structural anomalies found.'
      };
    }
  };

  const risk = getRiskDetails(normalizedScore, riskLevel);
  const RiskIcon = risk.icon;

  return (
    <div className="flex flex-col items-center justify-between h-full space-y-4">
      {/* Semi-circular Circular Gauge */}
      <div className="relative w-48 h-48 flex items-center justify-center">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 180 180">
          {/* Outer track */}
          <circle
            cx="90"
            cy="90"
            r={radius}
            className="stroke-slate-800"
            strokeWidth="14"
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * 0.25}
            strokeLinecap="round"
          />
          {/* Animated Gauge arc */}
          <motion.circle
            cx="90"
            cy="90"
            r={radius}
            stroke={risk.stroke}
            strokeWidth="14"
            fill="transparent"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            strokeLinecap="round"
          />
        </svg>

        {/* Center Content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <motion.span 
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.3 }}
            className={`text-4xl font-extrabold font-mono tracking-tight ${risk.color}`}
          >
            {normalizedScore.toFixed(1)}
          </motion.span>
          <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 mt-1">
            Structural Index / 100
          </span>
          <div className={`mt-2 flex items-center gap-1.5 px-3 py-1 rounded-full border font-mono text-xs font-bold ${risk.bg}`}>
            <RiskIcon className="w-3.5 h-3.5" />
            <span>{risk.label}</span>
          </div>
        </div>
      </div>

      {/* Risk Range Indicators */}
      <div className="w-full flex items-center justify-between px-2 text-[10px] font-mono text-slate-400">
        <span className={normalizedScore < 20 ? 'text-cyan-400 font-bold' : ''}>SAFE</span>
        <span className={normalizedScore >= 20 && normalizedScore < 40 ? 'text-emerald-400 font-bold' : ''}>LOW</span>
        <span className={normalizedScore >= 40 && normalizedScore < 60 ? 'text-yellow-400 font-bold' : ''}>MED</span>
        <span className={normalizedScore >= 60 && normalizedScore < 80 ? 'text-orange-400 font-bold' : ''}>HIGH</span>
        <span className={normalizedScore >= 80 ? 'text-red-400 font-bold' : ''}>CRITICAL</span>
      </div>

      {/* Factors Breakdown */}
      {factors && (
        <div className="w-full pt-2 border-t border-slate-800/80 grid grid-cols-2 gap-2 text-xs font-mono">
          <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800">
            <span className="text-slate-500 text-[10px] block">Type Severity</span>
            <span className="text-cyan-300 font-bold">{factors.type_score || 60.0} pts</span>
          </div>
          <div className="bg-slate-900/60 p-2 rounded-lg border border-slate-800">
            <span className="text-slate-500 text-[10px] block">Debris Extent</span>
            <span className="text-amber-300 font-bold">{factors.extent_penalty || 15.0} pts</span>
          </div>
        </div>
      )}
    </div>
  );
}
