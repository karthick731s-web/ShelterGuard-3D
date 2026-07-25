import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  FiFileText, 
  FiDownload, 
  FiShield, 
  FiAlertOctagon, 
  FiCheckCircle, 
  FiClock, 
  FiCpu, 
  FiCheck,
  FiCode
} from 'react-icons/fi';
import axios from 'axios';

export default function ReportPage({ inspectionData }) {
  const [reportText, setReportText] = useState('');
  const [loading, setLoading] = useState(true);
  const [downloaded, setDownloaded] = useState(false);

  const data = inspectionData || {};
  const severity = data.severity || { score: 86.8, risk_level: 'CRITICAL' };
  const damageSummary = data.damage_summary || { instances: [] };

  useEffect(() => {
    // Fetch raw TXT report from backend API
    axios.get('/api/report')
      .then(res => {
        if (res.data && res.data.report) {
          setReportText(res.data.report);
        }
      })
      .catch(err => {
        console.error('Error fetching report:', err);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleDownloadTxt = () => {
    const textToSave = reportText || `=== 3D LiDAR SHELTER INSPECTION REPORT ===
Shelter ID: ${data.shelter_id || 'SH-001'}
Robot ID: ${data.robot_id || 'TB3-01'}
Timestamp: ${data.timestamp || new Date().toLocaleString()}

SEVERITY ASSESSMENT:
Severity Score: ${severity.score || 86.8} / 100
Risk Level: ${severity.risk_level || 'CRITICAL'}
Recommendation: ${severity.recommendation || 'IMMINENT COLLAPSE RISK. Do NOT enter.'}

DETECTED DAMAGES:
Total Anomalies: ${damageSummary.total_count || 29}
Total Damaged Area: ${damageSummary.total_area_m2 || 18.4} m²
Types: ${(damageSummary.damage_types || []).join(', ')}

===========================================
End of Report`;

    const blob = new Blob([textToSave], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Inspection_Report_${data.shelter_id || 'SH-001'}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    setDownloaded(true);
    setTimeout(() => setDownloaded(false), 3000);
  };

  return (
    <div className="space-y-6 font-mono">
      {/* Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-cyan-500/30 flex flex-wrap justify-between items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FiFileText className="text-cyan-400" />
            Official Structural Inspection Report
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Automated Damage Classification & Engineering Safety Recommendation
          </p>
        </div>

        <button
          onClick={handleDownloadTxt}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs flex items-center gap-2 shadow-xl shadow-cyan-950/50 transition active:scale-95"
        >
          {downloaded ? <FiCheck className="w-4 h-4 text-emerald-950" /> : <FiDownload className="w-4 h-4" />}
          <span>{downloaded ? 'Downloaded TXT Report!' : 'Download TXT Report'}</span>
        </button>
      </div>

      {/* Structured Executive Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-1">
          <span className="text-slate-500 text-xs">Shelter ID</span>
          <div className="text-xl font-bold text-cyan-300">{data.shelter_id || 'SH-001'}</div>
          <span className="text-[10px] text-slate-400">Sector Alpha 4</span>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-1">
          <span className="text-slate-500 text-xs">Robot Inspection ID</span>
          <div className="text-xl font-bold text-slate-200">{data.robot_id || 'TB3-01'}</div>
          <span className="text-[10px] text-slate-400">Autonomous LiDAR Drone</span>
        </div>

        <div className="glass-card p-4 rounded-xl border border-slate-800 space-y-1">
          <span className="text-slate-500 text-xs">Inspection Time</span>
          <div className="text-sm font-bold text-slate-100 flex items-center gap-1.5 mt-1">
            <FiClock className="text-cyan-400" />
            {data.timestamp || '2026-07-25 14:00:00'}
          </div>
          <span className="text-[10px] text-slate-400">Duration: 14m 22s</span>
        </div>

        <div className="glass-card p-4 rounded-xl border border-red-500/30 bg-red-950/20 space-y-1">
          <span className="text-slate-400 text-xs">Risk Level & Score</span>
          <div className="text-xl font-bold text-red-400 flex items-center gap-2">
            <FiAlertOctagon /> {severity.risk_level || 'CRITICAL'} ({severity.score || 86.8})
          </div>
          <span className="text-[10px] text-red-300 font-semibold">Immediate Action Required</span>
        </div>
      </div>

      {/* Safety Recommendation Box */}
      <div className="glass-card p-6 rounded-2xl border border-red-500/40 bg-gradient-to-r from-red-950/40 to-slate-900/90 space-y-2">
        <h3 className="text-sm font-bold text-red-400 flex items-center gap-2">
          <FiShield className="w-5 h-5" />
          Engineering Safety Recommendation
        </h3>
        <p className="text-sm text-red-200 font-semibold leading-relaxed">
          "{severity.recommendation || 'IMMINENT COLLAPSE RISK. Do NOT enter under any circumstances. Evacuate all personnel within 50 m radius immediately.'}"
        </p>
      </div>

      {/* Damage Coordinates Table */}
      <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <FiCode className="text-cyan-400" />
          Detected Damage Coordinates & Severity Breakdown
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="py-2.5 px-3">Damage Type</th>
                <th className="py-2.5 px-3">Coordinates (X, Y, Z)</th>
                <th className="py-2.5 px-3">Extent (m / m²)</th>
                <th className="py-2.5 px-3">Confidence</th>
                <th className="py-2.5 px-3">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              {(damageSummary.instances || []).map((inst, idx) => (
                <tr key={idx} className="hover:bg-slate-900/40 transition">
                  <td className="py-3 px-3 font-bold text-cyan-300">{inst.type}</td>
                  <td className="py-3 px-3 text-slate-300">
                    ({inst.location_xyz[0]}, {inst.location_xyz[1]}, {inst.location_xyz[2]})
                  </td>
                  <td className="py-3 px-3 font-bold text-amber-300">{inst.extent_m} m</td>
                  <td className="py-3 px-3 text-emerald-400 font-bold">{(inst.confidence * 100).toFixed(0)}%</td>
                  <td className="py-3 px-3 text-slate-400 text-[11px]">{inst.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Raw TXT Viewer */}
      {reportText && (
        <div className="glass-card p-6 rounded-2xl border border-slate-800 space-y-3">
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <FiFileText className="text-cyan-400" />
              Full Raw Report Output (`inspection_report.txt`)
            </h3>

            <button
              onClick={handleDownloadTxt}
              className="px-3 py-1 rounded-lg bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-xs font-bold hover:bg-cyan-500/30 transition"
            >
              Download File
            </button>
          </div>

          <pre className="p-4 rounded-xl bg-[#050811] border border-slate-800 text-xs text-slate-300 overflow-x-auto whitespace-pre-wrap font-mono leading-relaxed max-h-96">
            {reportText}
          </pre>
        </div>
      )}
    </div>
  );
}
