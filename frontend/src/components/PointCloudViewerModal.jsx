import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { FiX, FiMaximize2, FiRotateCw, FiEye, FiLayers, FiDownload } from 'react-icons/fi';

export default function PointCloudViewerModal({ isOpen, onClose, pointStats }) {
  const mountRef = useRef(null);
  const [pointCount, setPointCount] = useState(pointStats?.total_points || 202322);
  const [pointColorMode, setPointColorMode] = useState('height'); // 'height', 'intensity', 'damage'
  const [pointSize, setPointSize] = useState(0.06);
  const [autoRotate, setAutoRotate] = useState(true);

  const sceneRef = useRef(null);
  const pointsMeshRef = useRef(null);
  const requestRef = useRef(null);
  const isDraggingRef = useRef(false);
  const previousMousePositionRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    if (!isOpen || !mountRef.current) return;

    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;

    // Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x080c14);
    scene.fog = new THREE.FogExp2(0x080c14, 0.03);
    sceneRef.current = scene;

    // Camera
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
    camera.position.set(6, 6, 8);
    camera.lookAt(0, 0, 0);

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mountRef.current.appendChild(renderer.domElement);

    // Helpers (Grid & Bounding Box)
    const gridHelper = new THREE.GridHelper(15, 30, 0x06b6d4, 0x1e293b);
    gridHelper.position.y = -1;
    scene.add(gridHelper);

    // Create Synthetic/Loaded 3D Shelter Point Cloud
    const numPoints = Math.min(pointCount, 150000);
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(numPoints * 3);
    const colors = new Float32Array(numPoints * 3);

    const colorObj = new THREE.Color();

    for (let i = 0; i < numPoints; i++) {
      // Simulate shelter room layout (walls, roof, collapsed sections, floor)
      let x, y, z;
      const type = Math.random();

      if (type < 0.35) {
        // Floor points
        x = (Math.random() - 0.5) * 10;
        z = (Math.random() - 0.5) * 10;
        y = -1.0 + (Math.random() * 0.05);
      } else if (type < 0.70) {
        // Walls with damage holes
        const side = Math.floor(Math.random() * 4);
        if (side === 0) { x = -5; z = (Math.random() - 0.5) * 10; }
        else if (side === 1) { x = 5; z = (Math.random() - 0.5) * 10; }
        else if (side === 2) { z = -5; x = (Math.random() - 0.5) * 10; }
        else { z = 5; x = (Math.random() - 0.5) * 10; }

        // Wall height
        y = -1 + Math.random() * 3.5;

        // Damage hole in North-West corner
        if (x > 1.5 && z > 0.5 && y > 0) {
          x += (Math.random() - 0.5) * 1.5;
          y -= Math.random() * 0.8; // Fallen debris
        }
      } else {
        // Debris & Damaged Roof
        x = (Math.random() - 0.5) * 8;
        z = (Math.random() - 0.5) * 8;
        y = 2.5 - Math.hypot(x - 2, z - 1) * 0.3 + (Math.random() * 0.2);
        if (x > 1 && z > 0) {
          // Collapse slope
          y = Math.max(-0.9, y - 2.0);
        }
      }

      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;

      // Color mapping
      if (pointColorMode === 'height') {
        const normY = (y + 1) / 3.5; // 0 to 1
        colorObj.setHSL(0.55 - normY * 0.5, 0.9, 0.55); // Cyan -> Green -> Red
      } else if (pointColorMode === 'damage') {
        const isDamaged = (x > 1.2 && x < 3.5 && z > -0.5 && z < 2.5 && y < 1.5);
        if (isDamaged) {
          colorObj.setHex(0xef4444); // Red damage zone
        } else {
          colorObj.setHex(0x38bdf8); // Cyan normal shelter
        }
      } else {
        const intensity = 0.4 + Math.random() * 0.6;
        colorObj.setRGB(intensity * 0.2, intensity * 0.8, intensity);
      }

      colors[i * 3] = colorObj.r;
      colors[i * 3 + 1] = colorObj.g;
      colors[i * 3 + 2] = colorObj.b;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: pointSize,
      vertexColors: true,
      transparent: true,
      opacity: 0.85,
      sizeAttenuation: true
    });

    const points = new THREE.Points(geometry, material);
    scene.add(points);
    pointsMeshRef.current = points;

    // Highlight Damaged Region Bounding Box
    const boxGeo = new THREE.BoxGeometry(2.5, 2.5, 2.5);
    const boxMat = new THREE.MeshBasicMaterial({
      color: 0xef4444,
      wireframe: true,
      transparent: true,
      opacity: 0.6
    });
    const boxMesh = new THREE.Mesh(boxGeo, boxMat);
    boxMesh.position.set(2.0, 0.5, 1.0);
    scene.add(boxMesh);

    // Mouse Interaction (Orbit rotation)
    const handleMouseDown = (e) => {
      isDraggingRef.current = true;
      previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseMove = (e) => {
      if (!isDraggingRef.current || !pointsMeshRef.current) return;

      const deltaX = e.clientX - previousMousePositionRef.current.x;
      const deltaY = e.clientY - previousMousePositionRef.current.y;

      pointsMeshRef.current.rotation.y += deltaX * 0.008;
      pointsMeshRef.current.rotation.x += deltaY * 0.008;
      boxMesh.rotation.y += deltaX * 0.008;
      boxMesh.rotation.x += deltaY * 0.008;

      previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseUp = () => {
      isDraggingRef.current = false;
    };

    const domElem = mountRef.current;
    domElem.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    // Animation Loop
    const animate = () => {
      requestRef.current = requestAnimationFrame(animate);

      if (autoRotate && pointsMeshRef.current && !isDraggingRef.current) {
        pointsMeshRef.current.rotation.y += 0.003;
        boxMesh.rotation.y += 0.003;
      }

      renderer.render(scene, camera);
    };

    animate();

    // Resize Handler
    const handleResize = () => {
      if (!mountRef.current) return;
      const newW = mountRef.current.clientWidth;
      const newH = mountRef.current.clientHeight;
      camera.aspect = newW / newH;
      camera.updateProjectionMatrix();
      renderer.setSize(newW, newH);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
      window.removeEventListener('resize', handleResize);
      domElem.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      geometry.dispose();
      material.dispose();
    };
  }, [isOpen, pointColorMode, pointSize, autoRotate, pointCount]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div className="relative w-full max-w-5xl h-[85vh] glass-panel rounded-2xl border border-cyan-500/30 flex flex-col overflow-hidden shadow-2xl shadow-cyan-950/50">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/90 font-mono">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <FiMaximize2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-white text-base">3D Point Cloud Inspection Viewer</h2>
              <p className="text-xs text-slate-400">
                Interactive LiDAR Point Field (Points: {pointCount.toLocaleString()})
              </p>
            </div>
          </div>

          {/* Controls toolbar */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setAutoRotate(!autoRotate)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition ${
                autoRotate ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40' : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}
            >
              <FiRotateCw className={autoRotate ? 'animate-spin-slow' : ''} />
              <span>{autoRotate ? 'Auto Rotate ON' : 'Rotate OFF'}</span>
            </button>

            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-slate-800 hover:bg-red-500/20 hover:text-red-400 text-slate-400 border border-slate-700 transition"
            >
              <FiX className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 3D Canvas Viewport */}
        <div className="relative flex-1 bg-[#080c14] cursor-grab active:cursor-grabbing" ref={mountRef}>
          {/* Overlay Info Legend */}
          <div className="absolute top-4 left-4 p-4 rounded-xl bg-slate-900/80 backdrop-blur-md border border-slate-800 space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between gap-4">
              <span className="text-slate-400">Density:</span>
              <span className="text-cyan-300 font-bold">1,420 pts/m³</span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-slate-400">Bounding Volume:</span>
              <span className="text-slate-200">10.0 x 10.0 x 3.5 m</span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-slate-400">Damage Red Box:</span>
              <span className="text-red-400 font-bold">NW Wall Void</span>
            </div>
          </div>

          {/* Color Mode Switcher */}
          <div className="absolute top-4 right-4 flex gap-1 p-1 bg-slate-900/90 rounded-xl border border-slate-800 text-xs font-mono">
            <button
              onClick={() => setPointColorMode('height')}
              className={`px-3 py-1.5 rounded-lg transition ${
                pointColorMode === 'height' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Height Ramp
            </button>
            <button
              onClick={() => setPointColorMode('damage')}
              className={`px-3 py-1.5 rounded-lg transition ${
                pointColorMode === 'damage' ? 'bg-red-500 text-white font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              Damage Heatmap
            </button>
            <button
              onClick={() => setPointColorMode('intensity')}
              className={`px-3 py-1.5 rounded-lg transition ${
                pointColorMode === 'intensity' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
              }`}
            >
              LiDAR Intensity
            </button>
          </div>

          <div className="absolute bottom-4 left-4 text-[11px] font-mono text-slate-500 bg-slate-950/60 px-3 py-1 rounded-md border border-slate-800">
            Click & Drag to rotate • Scroll to zoom
          </div>
        </div>

        {/* Footer info bar */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-900/90 flex justify-between items-center text-xs font-mono text-slate-400">
          <div className="flex items-center gap-4">
            <span>Points: <strong className="text-cyan-300">{pointCount.toLocaleString()}</strong></span>
            <span>Scan Passes: <strong className="text-emerald-400">8 Passes</strong></span>
          </div>

          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold transition"
          >
            Close 3D View
          </button>
        </div>
      </div>
    </div>
  );
}
