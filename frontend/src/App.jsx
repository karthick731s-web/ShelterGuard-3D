import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import PointCloudViewerModal from './components/PointCloudViewerModal';

import DashboardPage from './pages/DashboardPage';
import RobotPage from './pages/RobotPage';
import LidarPage from './pages/LidarPage';
import PointCloudPage from './pages/PointCloudPage';
import DamagePage from './pages/DamagePage';
import ReportPage from './pages/ReportPage';
import TerminalPage from './pages/TerminalPage';
import WorkflowPage from './pages/WorkflowPage';
import AboutPage from './pages/AboutPage';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [statusData, setStatusData] = useState(null);
  const [inspectionData, setInspectionData] = useState(null);
  const [logs, setLogs] = useState([]);
  const [is3DModalOpen, setIs3DModalOpen] = useState(false);

  // Poll status, inspection summary, and logs from backend API
  const fetchAllData = async () => {
    try {
      const [statusRes, inspectionRes, logsRes] = await Promise.allSettled([
        axios.get('/api/status'),
        axios.get('/api/inspection'),
        axios.get('/api/logs'),
      ]);

      if (statusRes.status === 'fulfilled') {
        setStatusData(statusRes.value.data);
      }
      if (inspectionRes.status === 'fulfilled') {
        setInspectionData(inspectionRes.value.data);
      }
      if (logsRes.status === 'fulfilled' && logsRes.value.data?.logs) {
        setLogs(logsRes.value.data.logs);
      }
    } catch (err) {
      console.warn('API polling fallback:', err);
    }
  };

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleTriggerRun = async () => {
    try {
      await axios.post('/api/run-inspection');
      fetchAllData();
    } catch (err) {
      console.error('Trigger inspection error:', err);
    }
  };

  const damageCount = inspectionData?.damage_summary?.total_count || 29;

  const renderActivePage = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <DashboardPage
            inspectionData={inspectionData}
            statusData={statusData}
            onOpen3D={() => setIs3DModalOpen(true)}
            onTriggerRun={handleTriggerRun}
          />
        );
      case 'robot':
        return <RobotPage statusData={statusData} />;
      case 'lidar':
        return <LidarPage scanStats={inspectionData?.scan_stats} />;
      case 'pointcloud':
        return (
          <PointCloudPage
            scanStats={inspectionData?.scan_stats}
            onOpen3D={() => setIs3DModalOpen(true)}
          />
        );
      case 'damage':
        return <DamagePage damageSummary={inspectionData?.damage_summary} />;
      case 'report':
        return <ReportPage inspectionData={inspectionData} />;
      case 'terminal':
        return (
          <TerminalPage
            logs={logs}
            isRunning={statusData?.is_running}
            onTriggerRun={handleTriggerRun}
          />
        );
      case 'workflow':
        return <WorkflowPage />;
      case 'about':
        return <AboutPage />;
      default:
        return (
          <DashboardPage
            inspectionData={inspectionData}
            statusData={statusData}
            onOpen3D={() => setIs3DModalOpen(true)}
            onTriggerRun={handleTriggerRun}
          />
        );
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#080c14] text-slate-100 selection:bg-cyan-500 selection:text-black">
      {/* Top Navbar */}
      <Navbar
        statusData={statusData}
        onTriggerRun={handleTriggerRun}
      />

      {/* Main Workspace Body */}
      <div className="flex-1 flex w-full">
        {/* Sidebar */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          statusData={statusData}
          damageCount={damageCount}
        />

        {/* Mobile Nav Tabs */}
        <div className="md:hidden flex overflow-x-auto p-2 bg-slate-900 border-b border-slate-800 text-xs font-mono gap-2 w-full">
          {['dashboard', 'robot', 'lidar', 'pointcloud', 'damage', 'report', 'terminal', 'workflow', 'about'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1.5 rounded-lg shrink-0 capitalize ${
                activeTab === tab ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-400 bg-slate-800'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Main Content Area */}
        <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-7xl mx-auto w-full overflow-x-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.25 }}
            >
              {renderActivePage()}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* 3D Point Cloud Modal */}
      <PointCloudViewerModal
        isOpen={is3DModalOpen}
        onClose={() => setIs3DModalOpen(false)}
        pointStats={inspectionData?.scan_stats}
      />
    </div>
  );
}
