import React from 'react';
import { motion } from 'framer-motion';
import { FiNavigation, FiBatteryCharging, FiCpu, FiCompass, FiShield, FiActivity, FiMapPin } from 'react-icons/fi';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function RobotPage({ statusData }) {
  const telemetryData = [
    { time: '00s', speed: 0.0, battery: 99, distance: 0.0 },
    { time: '05s', speed: 0.22, battery: 99, distance: 4.2 },
    { time: '10s', speed: 0.35, battery: 98, distance: 11.5 },
    { time: '15s', speed: 0.28, battery: 98, distance: 19.8 },
    { time: '20s', speed: 0.40, battery: 98, distance: 26.4 },
    { time: '25s', speed: 0.15, battery: 98, distance: 31.1 },
  ];

  return (
    <div className="space-y-6 font-mono">
      {/* Title */}
      <div className="glass-panel p-6 rounded-2xl border border-cyan-500/30 flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FiNavigation className="text-cyan-400" />
            Robot Telemetry & Autonomous Navigation
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            TurtleBot3 Waffle Pi • ROS2 /cmd_vel Controller & Waypoint Planner
          </p>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          Connected & Calibrated
        </span>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-1">
          <span className="text-slate-500 text-xs">Robot Identifier</span>
          <div className="text-xl font-bold text-cyan-300">TB3-01 (Waffle)</div>
          <span className="text-[10px] text-slate-400">Diff-Drive Mobile Base</span>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-1">
          <span className="text-slate-500 text-xs">Battery Charge</span>
          <div className="text-xl font-bold text-emerald-400 flex items-center gap-2">
            <FiBatteryCharging /> 98%
          </div>
          <span className="text-[10px] text-slate-400">Voltage: 12.4 V</span>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-1">
          <span className="text-slate-500 text-xs">Current Coordinates</span>
          <div className="text-xl font-bold text-slate-100">(6.75, 5.25, 90°)</div>
          <span className="text-[10px] text-cyan-400">Odometry Frame: map</span>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-1">
          <span className="text-slate-500 text-xs">Path Traveled</span>
          <div className="text-xl font-bold text-amber-300">31.1 Meters</div>
          <span className="text-[10px] text-slate-400">20 Autonomous Steps</span>
        </div>
      </div>

      {/* Speed & Distance Graph */}
      <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <FiActivity className="text-cyan-400" />
          Autonomous Trajectory Velocity Profile
        </h3>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={telemetryData}>
              <XAxis dataKey="time" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc' }} />
              <Line type="monotone" dataKey="speed" stroke="#06b6d4" strokeWidth={3} name="Velocity (m/s)" />
              <Line type="monotone" dataKey="distance" stroke="#10b981" strokeWidth={2} name="Distance (m)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
