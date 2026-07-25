import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FiNavigation, 
  FiDisc, 
  FiBox, 
  FiMap, 
  FiAlertTriangle, 
  FiZap, 
  FiFileText,
  FiArrowDown,
  FiCheckCircle,
  FiGitCommit
} from 'react-icons/fi';

const WORKFLOW_STAGES = [
  {
    id: 1,
    title: 'Robot Navigation',
    subtitle: 'Autonomous Pathing',
    icon: FiNavigation,
    color: 'from-cyan-500/20 to-blue-500/20 border-cyan-500/40 text-cyan-300',
    iconColor: 'text-cyan-400',
    description: 'TurtleBot3 navigates through designated shelter entry point using ROS2 Nav2 stack and costmap obstacle avoidance.',
    metrics: ['Waypoint: (6.75, 5.25)', 'Distance: 31.1 m', 'Speed: 0.35 m/s']
  },
  {
    id: 2,
    title: 'LiDAR Scan',
    subtitle: '360° Multilayer Acquisition',
    icon: FiDisc,
    color: 'from-blue-500/20 to-indigo-500/20 border-blue-500/40 text-blue-300',
    iconColor: 'text-blue-400',
    description: '360-degree laser range finder captures 360 rays per pass at 10 Hz across 8 elevation scan levels.',
    metrics: ['Rays: 360 / Pass', 'Frequency: 10 Hz', 'Passes: 8 Multi-Level']
  },
  {
    id: 3,
    title: 'Point Cloud Generation',
    subtitle: '3D Point Matrix Filtering',
    icon: FiBox,
    color: 'from-indigo-500/20 to-purple-500/20 border-indigo-500/40 text-indigo-300',
    iconColor: 'text-indigo-400',
    description: 'Combines multi-pass laser ranges into unified XYZ point matrix (202,322 points) and applies Statistical Outlier Removal (SOR).',
    metrics: ['Total Points: 202,322', 'Valid Points: 199,926', 'Density: 1,420 pts/m³']
  },
  {
    id: 4,
    title: 'Environment Mapping',
    subtitle: '2D/3D Occupancy Grid',
    icon: FiMap,
    color: 'from-teal-500/20 to-emerald-500/20 border-teal-500/40 text-teal-300',
    iconColor: 'text-teal-400',
    description: 'Generates 2D occupancy grid and 3D spatial mesh map of the shelter interior (94.2% room coverage).',
    metrics: ['Mapped Area: 48.5 m²', 'Room Coverage: 94.2%', 'Occupancy: 12.4%']
  },
  {
    id: 5,
    title: 'Damage Detection',
    subtitle: 'Displacement & Void Clustering',
    icon: FiAlertTriangle,
    color: 'from-amber-500/20 to-orange-500/20 border-amber-500/40 text-amber-300',
    iconColor: 'text-amber-400',
    description: 'Identifies structural anomalies such as collapsed wall sections, floor voids, leaning walls (18.4° tilt), and cracks.',
    metrics: ['Anomalies: 29', 'Damaged Area: 18.4 m²', 'Max Tilt: 18.4°']
  },
  {
    id: 6,
    title: 'Severity Classification',
    subtitle: 'Risk Index Evaluation',
    icon: FiZap,
    color: 'from-orange-500/20 to-red-500/20 border-orange-500/40 text-orange-300',
    iconColor: 'text-red-400',
    description: 'Calculates overall structural collapse score (0-100 gauge). Assigns safety rating: SAFE, LOW, MEDIUM, HIGH, or CRITICAL.',
    metrics: ['Score: 86.8 / 100', 'Risk Level: CRITICAL', 'Confidence: 82%']
  },
  {
    id: 7,
    title: 'Inspection Report Generation',
    subtitle: 'Automated Diagnostic Output',
    icon: FiFileText,
    color: 'from-emerald-500/20 to-cyan-500/20 border-emerald-500/40 text-emerald-300',
    iconColor: 'text-emerald-400',
    description: 'Compiles inspection summary JSON, generates visual PNG heatmaps, and outputs downloadable TXT engineering report.',
    metrics: ['Output: inspection_report.txt', 'Format: JSON / TXT', 'Status: Complete']
  }
];

export default function WorkflowPage() {
  const [selectedStage, setSelectedStage] = useState(WORKFLOW_STAGES[0]);

  return (
    <div className="space-y-6 font-mono">
      {/* Header */}
      <div className="glass-panel p-6 rounded-2xl border border-cyan-500/30 flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FiGitCommit className="text-cyan-400" />
            3D LiDAR Inspection Workflow Pipeline
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Interactive 7-Stage Autonomous Structural Assessment Architecture
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
          7 STAGES ACTIVE
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Side: Animated Vertical Step Flow */}
        <div className="lg:col-span-2 space-y-3">
          {WORKFLOW_STAGES.map((stage, index) => {
            const Icon = stage.icon;
            const isSelected = selectedStage.id === stage.id;
            return (
              <React.Fragment key={stage.id}>
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.4, delay: index * 0.08 }}
                  onClick={() => setSelectedStage(stage)}
                  className={`glass-card p-4 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                    isSelected
                      ? 'border-cyan-400 bg-gradient-to-r from-cyan-950/60 to-slate-900/90 shadow-xl shadow-cyan-950/40 scale-[1.02]'
                      : 'border-slate-800 hover:border-cyan-500/30 hover:bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className={`p-3 rounded-xl bg-gradient-to-br ${stage.color} border shadow-md`}>
                      <Icon className={`w-6 h-6 ${stage.iconColor}`} />
                    </div>

                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
                          STAGE {stage.id}
                        </span>
                        <h3 className="font-bold text-white text-sm">{stage.title}</h3>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">{stage.subtitle}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-xs text-emerald-400 font-bold hidden sm:inline flex items-center gap-1">
                      <FiCheckCircle className="w-3.5 h-3.5" /> Executed
                    </span>
                  </div>
                </motion.div>

                {/* Animated Arrow Connector */}
                {index < WORKFLOW_STAGES.length - 1 && (
                  <div className="flex justify-center my-1 text-cyan-500/60">
                    <motion.div
                      animate={{ y: [0, 4, 0] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    >
                      <FiArrowDown className="w-5 h-5" />
                    </motion.div>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Right Side: Detailed Stage Inspector Panel */}
        <div className="glass-card p-6 rounded-2xl border border-cyan-500/30 sticky top-24 h-fit space-y-4">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-3">
            <div className={`p-3 rounded-xl bg-gradient-to-br ${selectedStage.color} border`}>
              <selectedStage.icon className={`w-6 h-6 ${selectedStage.iconColor}`} />
            </div>
            <div>
              <span className="text-[10px] text-cyan-400 font-bold uppercase">
                Stage {selectedStage.id} Inspector
              </span>
              <h3 className="font-bold text-white text-base">{selectedStage.title}</h3>
            </div>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/80 p-3.5 rounded-xl border border-slate-800">
            {selectedStage.description}
          </p>

          <div className="space-y-2">
            <span className="text-xs text-slate-400 font-bold block">Stage Output Metrics:</span>
            {selectedStage.metrics.map((metric, idx) => (
              <div key={idx} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 text-xs">
                <span className="text-slate-400 font-semibold">{metric.split(':')[0]}</span>
                <span className="text-cyan-300 font-bold">{metric.split(':')[1]}</span>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-slate-800 text-[11px] text-emerald-400 flex items-center justify-between">
            <span>Stage Latency: &lt; 150 ms</span>
            <span>Status: Verified</span>
          </div>
        </div>

      </div>
    </div>
  );
}
