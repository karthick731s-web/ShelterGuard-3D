import React from 'react';
import { motion } from 'framer-motion';
import { 
  FiCpu, 
  FiBatteryCharging, 
  FiNavigation, 
  FiDisc, 
  FiBox, 
  FiMap, 
  FiAlertTriangle, 
  FiCheckCircle, 
  FiActivity, 
  FiPlay, 
  FiArrowRight, 
  FiMaximize2,
  FiZap,
  FiTrendingUp,
  FiCheck
} from 'react-icons/fi';
import SeverityGauge from '../components/SeverityGauge';
import ImageWithFallback from '../components/ImageWithFallback';

export default function DashboardPage({ 
  inspectionData, 
  statusData, 
  onOpen3D, 
  onTriggerRun 
}) {
  const data = inspectionData || {};
  const severity = data.severity || { score: 86.8, risk_level: 'CRITICAL' };
  const damageSummary = data.damage_summary || { total_count: 29, total_area_m2: 18.4 };
  const instances = damageSummary.instances || [];
  const navStats = data.navigation_stats || { battery_pct: 98, distance_m: 31.1 };
  const scanStats = data.scan_stats || { total_scans: 8, total_points: 202322 };
  const isRunning = statusData?.is_running;

  // Damage categories with color mapping
  const damageItems = [
    { type: 'Collapsed Section', severity: 'CRITICAL', color: 'bg-red-500/10 border-red-500/30 text-red-400', badge: 'Red', count: '13 pts' },
    { type: 'Leaning Wall (18.4°)', severity: 'HIGH', color: 'bg-orange-500/10 border-orange-500/30 text-orange-400', badge: 'Orange', count: ' tilting' },
    { type: 'Large Hole / Void', severity: 'HIGH', color: 'bg-orange-500/10 border-orange-500/30 text-orange-400', badge: 'Orange', count: '14.5m²' },
    { type: 'Roof Sag & Cracks', severity: 'MEDIUM', color: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-300', badge: 'Yellow', count: '2.1m' },
    { type: 'Surface Fracture', severity: 'LOW', color: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300', badge: 'Green', count: 'Minor' },
  ];

  // Pipeline workflow steps for timeline
  const pipelineSteps = [
    { title: 'Robot Navigation', status: isRunning ? 'active' : 'completed', time: '14:00:01' },
    { title: 'LiDAR Scan', status: isRunning ? 'active' : 'completed', time: '14:00:04' },
    { title: 'Point Cloud', status: isRunning ? 'active' : 'completed', time: '14:00:06' },
    { title: 'Environment Mapping', status: isRunning ? 'active' : 'completed', time: '14:00:08' },
    { title: 'Damage Detection', status: isRunning ? 'active' : 'completed', time: '14:00:10' },
    { title: 'Severity Classification', status: isRunning ? 'active' : 'completed', time: '14:00:12' },
    { title: 'Inspection Report', status: isRunning ? 'active' : 'completed', time: '14:00:14' },
  ];

  return (
    <div className="space-y-6">
      
      {/* Top Banner Alert / Trigger CTA */}
      <div className="glass-panel p-6 rounded-2xl border border-cyan-500/30 bg-gradient-to-r from-slate-900/90 via-slate-900/95 to-slate-950 flex flex-wrap items-center justify-between gap-6 shadow-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping"></span>
            <h2 className="text-xl font-bold font-mono text-white tracking-wide">
              Disaster Response Command Center Dashboard
            </h2>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            Autonomous 3D LiDAR Structural Integrity Evaluation System • Shelter Target: <span className="text-cyan-300 font-bold">{data.shelter_id || 'SH-001'}</span>
          </p>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={onOpen3D}
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/30 text-xs font-mono font-bold flex items-center gap-2 transition shadow-lg"
          >
            <FiBox className="w-4 h-4 text-cyan-400" />
            <span>Launch Interactive 3D View</span>
          </button>

          <button
            onClick={onTriggerRun}
            disabled={isRunning}
            className={`px-5 py-2.5 rounded-xl font-mono text-xs font-bold flex items-center gap-2 transition shadow-xl ${
              isRunning
                ? 'bg-slate-800 text-slate-500 border border-slate-700 cursor-not-allowed'
                : 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 border border-cyan-400/40 shadow-cyan-900/40 active:scale-95'
            }`}
          >
            <FiPlay className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
            <span>{isRunning ? 'Pipeline Running...' : 'Execute Live Pipeline'}</span>
          </button>
        </div>
      </div>

      {/* Grid of 7 Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

        {/* CARD 1: Robot Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="glass-card p-5 rounded-2xl flex flex-col justify-between space-y-4"
        >
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2.5 text-cyan-400">
              <FiCpu className="w-5 h-5" />
              <h3 className="font-bold font-mono text-sm text-white">Card 1 • Robot Status</h3>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              CONNECTED
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs font-mono">
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-[10px]">Robot ID</span>
              <p className="text-cyan-300 font-bold text-sm mt-0.5">{data.robot_id || 'TB3-01'}</p>
            </div>
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-[10px]">Battery Level</span>
              <p className="text-emerald-400 font-bold text-sm mt-0.5 flex items-center gap-1">
                <FiBatteryCharging className="w-4 h-4 inline" /> {navStats.battery_pct ?? 98}%
              </p>
            </div>
          </div>

          <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800 space-y-2 font-mono text-xs">
            <div className="flex justify-between text-slate-400">
              <span>Current Position:</span>
              <span className="text-slate-200 font-bold">X: 6.75m | Y: 5.25m | θ: 90°</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Nav Distance:</span>
              <span className="text-cyan-300 font-bold">{navStats.distance_m || 31.1} m</span>
            </div>

            {/* Navigation Progress Bar */}
            <div className="pt-2">
              <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                <span>Navigation Progress</span>
                <span className="text-cyan-400 font-bold">{isRunning ? statusData?.navigation_progress || 45 : 100}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${isRunning ? statusData?.navigation_progress || 45 : 100}%` }}
                  transition={{ duration: 0.8 }}
                />
              </div>
            </div>
          </div>
        </motion.div>

        {/* CARD 2: LiDAR 360° Scan Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="glass-card p-5 rounded-2xl flex flex-col justify-between space-y-4"
        >
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2.5 text-cyan-400">
              <FiDisc className="w-5 h-5 animate-spin-slow" />
              <h3 className="font-bold font-mono text-sm text-white">Card 2 • LiDAR 360° Scan</h3>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              SCANNING
            </span>
          </div>

          {/* Animated Polar Radar Beam Widget */}
          <div className="relative w-28 h-28 mx-auto flex items-center justify-center">
            <div className="absolute inset-0 rounded-full border border-cyan-500/30"></div>
            <div className="absolute inset-2 rounded-full border border-cyan-500/20"></div>
            <div className="absolute inset-6 rounded-full border border-cyan-500/10"></div>
            <div className="absolute w-full h-0.5 bg-cyan-500/20"></div>
            <div className="absolute h-full w-0.5 bg-cyan-500/20"></div>
            
            {/* Sweep radar beam */}
            <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-cyan-500/30 via-transparent to-transparent animate-radar-sweep"></div>
            <span className="text-[10px] font-mono font-bold text-cyan-300 z-10 bg-slate-900/80 px-1.5 py-0.5 rounded">
              360° FOV
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center font-mono text-xs">
            <div className="bg-slate-900/80 p-2 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-[10px] block">Rays</span>
              <strong className="text-cyan-300">360 Rays</strong>
            </div>
            <div className="bg-slate-900/80 p-2 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-[10px] block">Passes</span>
              <strong className="text-slate-200">{scanStats.total_scans || 8} Passes</strong>
            </div>
            <div className="bg-slate-900/80 p-2 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-[10px] block">Frequency</span>
              <strong className="text-emerald-400">10 Hz</strong>
            </div>
          </div>
        </motion.div>

        {/* CARD 3: Point Cloud Display */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="glass-card p-5 rounded-2xl flex flex-col justify-between space-y-3"
        >
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2.5 text-cyan-400">
              <FiBox className="w-5 h-5" />
              <h3 className="font-bold font-mono text-sm text-white">Card 3 • Point Cloud</h3>
            </div>
            <span className="text-xs font-mono text-slate-400">3D Density</span>
          </div>

          {/* Render Preview Image */}
          <div className="h-32 w-full overflow-hidden rounded-xl">
            <ImageWithFallback
              src="/api/images/point_cloud.png"
              alt="3D Point Cloud Preview"
              title="3D Point Cloud Field"
              fallbackType="pointcloud"
              className="h-full w-full"
            />
          </div>

          <div className="flex justify-between items-center text-xs font-mono bg-slate-900/80 p-2.5 rounded-xl border border-slate-800">
            <div>
              <span className="text-slate-500 text-[10px] block">Total Points</span>
              <strong className="text-cyan-300 text-sm">{(scanStats.total_points || 202322).toLocaleString()}</strong>
            </div>
            <div className="text-right">
              <span className="text-slate-500 text-[10px] block">Point Density</span>
              <strong className="text-slate-200">1,420 pts/m³</strong>
            </div>
          </div>

          <button
            onClick={onOpen3D}
            className="w-full py-2 rounded-xl bg-gradient-to-r from-cyan-500/20 to-blue-600/20 hover:from-cyan-500/30 hover:to-blue-600/30 border border-cyan-500/40 text-cyan-300 font-mono text-xs font-bold flex items-center justify-center gap-2 transition"
          >
            <FiMaximize2 className="w-4 h-4" />
            <span>Open 3D View</span>
          </button>
        </motion.div>

        {/* CARD 4: Environment Map */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="glass-card p-5 rounded-2xl flex flex-col justify-between space-y-3"
        >
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2.5 text-cyan-400">
              <FiMap className="w-5 h-5" />
              <h3 className="font-bold font-mono text-sm text-white">Card 4 • Environment Map</h3>
            </div>
            <span className="text-xs font-mono text-slate-400">Occupancy Grid</span>
          </div>

          {/* Render Preview Map Image */}
          <div className="h-32 w-full overflow-hidden rounded-xl">
            <ImageWithFallback
              src="/api/images/environment_map.png"
              alt="Environment Map"
              title="2D/3D Occupancy Grid Map"
              fallbackType="map"
              className="h-full w-full"
            />
          </div>

          <div className="grid grid-cols-3 gap-2 text-center font-mono text-xs">
            <div className="bg-slate-900/80 p-2 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-[10px] block">Coverage</span>
              <strong className="text-emerald-400">94.2%</strong>
            </div>
            <div className="bg-slate-900/80 p-2 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-[10px] block">Mapped Area</span>
              <strong className="text-cyan-300">48.5 m²</strong>
            </div>
            <div className="bg-slate-900/80 p-2 rounded-xl border border-slate-800">
              <span className="text-slate-500 text-[10px] block">Occupancy</span>
              <strong className="text-slate-200">12.4%</strong>
            </div>
          </div>
        </motion.div>

        {/* CARD 5: Damage Detection */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.4 }}
          className="glass-card p-5 rounded-2xl flex flex-col justify-between space-y-3"
        >
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2.5 text-cyan-400">
              <FiAlertTriangle className="w-5 h-5 text-amber-400" />
              <h3 className="font-bold font-mono text-sm text-white">Card 5 • Damage Detection</h3>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-500/20 text-red-400 border border-red-500/30">
              {damageSummary.total_count || 29} Anomalies
            </span>
          </div>

          {/* List of Detected Damage Types */}
          <div className="space-y-2 font-mono text-xs max-h-48 overflow-y-auto pr-1">
            {damageItems.map((item, idx) => (
              <div key={idx} className={`p-2.5 rounded-xl border flex items-center justify-between ${item.color}`}>
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-current"></span>
                  <span className="font-bold">{item.type}</span>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded bg-slate-950/60 border border-current/20">
                  {item.severity}
                </span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* CARD 6: Severity Score Gauge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.5 }}
          className="glass-card p-5 rounded-2xl flex flex-col justify-between space-y-3"
        >
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center gap-2.5 text-cyan-400">
              <FiZap className="w-5 h-5 text-red-400" />
              <h3 className="font-bold font-mono text-sm text-white">Card 6 • Severity Score</h3>
            </div>
            <span className="text-xs font-mono text-slate-400">0 - 100 Gauge</span>
          </div>

          <SeverityGauge 
            score={severity.score || 86.8} 
            riskLevel={severity.risk_level || 'CRITICAL'} 
            factors={severity.factor_breakdown}
          />
        </motion.div>

      </div>

      {/* CARD 7: Inspection Timeline (Full Width) */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.6 }}
        className="glass-card p-6 rounded-2xl space-y-4"
      >
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <FiActivity className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold font-mono text-base text-white">Card 7 • Inspection Pipeline Timeline</h3>
              <p className="text-xs text-slate-400 font-mono">
                End-to-End Autonomous Damage Assessment Pipeline Stages
              </p>
            </div>
          </div>

          <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            Pipeline Complete
          </span>
        </div>

        {/* Horizontal Timeline Steps */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 pt-2">
          {pipelineSteps.map((step, index) => (
            <div key={index} className="relative flex flex-col items-center text-center p-3 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2 font-mono">
              <div className="w-8 h-8 rounded-full bg-cyan-500/20 border border-cyan-400/50 flex items-center justify-center text-cyan-300 font-bold text-xs shadow-md shadow-cyan-950/50">
                {index + 1}
              </div>
              <span className="text-xs font-semibold text-slate-200 leading-snug">
                {step.title}
              </span>
              <span className="text-[10px] text-slate-500">
                {step.time}
              </span>
              <span className="text-[9px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold uppercase">
                Done
              </span>
            </div>
          ))}
        </div>
      </motion.div>

    </div>
  );
}
