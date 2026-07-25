import React, { useState } from 'react';
import { FiImage, FiMaximize2, FiAlertCircle, FiEye } from 'react-icons/fi';

export default function ImageWithFallback({ src, alt, title, fallbackType = 'grid', className = "" }) {
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  // Custom visual SVG graphics if backend file is missing
  const renderFallbackVisual = () => {
    if (fallbackType === 'pointcloud') {
      return (
        <div className="w-full h-full min-h-[200px] flex flex-col items-center justify-center p-4 bg-[#080c14] bg-grid-pattern relative overflow-hidden rounded-xl border border-cyan-500/20">
          <div className="absolute inset-0 bg-gradient-to-t from-cyan-950/40 via-transparent to-slate-950/60"></div>
          {/* Animated Point cloud scatter graphics */}
          <div className="relative z-10 text-center space-y-2">
            <div className="w-24 h-24 mx-auto relative flex items-center justify-center">
              <div className="absolute inset-0 rounded-full border border-cyan-500/40 animate-ping"></div>
              <div className="w-16 h-16 rounded-full bg-cyan-500/10 border border-cyan-400/50 flex items-center justify-center text-cyan-400">
                <FiImage className="w-8 h-8" />
              </div>
            </div>
            <p className="font-mono text-xs text-cyan-300 font-semibold">{title}</p>
            <span className="inline-block font-mono text-[10px] text-slate-400 bg-slate-900/80 px-2 py-0.5 rounded border border-slate-800">
              3D LiDAR Point Field Generated
            </span>
          </div>
        </div>
      );
    } else if (fallbackType === 'map') {
      return (
        <div className="w-full h-full min-h-[200px] flex flex-col items-center justify-center p-4 bg-[#090e1a] bg-dot-pattern relative overflow-hidden rounded-xl border border-emerald-500/20">
          <div className="absolute w-32 h-32 rounded-full border border-emerald-500/30 animate-pulse"></div>
          <div className="relative z-10 text-center space-y-2">
            <div className="w-16 h-16 mx-auto rounded-xl bg-emerald-500/10 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <FiImage className="w-8 h-8" />
            </div>
            <p className="font-mono text-xs text-emerald-300 font-semibold">{title}</p>
            <span className="inline-block font-mono text-[10px] text-slate-400 bg-slate-900/80 px-2 py-0.5 rounded border border-slate-800">
              Occupancy Grid Map (2D/3D)
            </span>
          </div>
        </div>
      );
    } else {
      return (
        <div className="w-full h-full min-h-[200px] flex flex-col items-center justify-center p-4 bg-[#140b0e] relative overflow-hidden rounded-xl border border-red-500/20">
          <div className="relative z-10 text-center space-y-2">
            <div className="w-16 h-16 mx-auto rounded-xl bg-red-500/10 border border-red-500/40 flex items-center justify-center text-red-400">
              <FiAlertCircle className="w-8 h-8 animate-pulse" />
            </div>
            <p className="font-mono text-xs text-red-300 font-semibold">{title}</p>
            <span className="inline-block font-mono text-[10px] text-slate-400 bg-slate-900/80 px-2 py-0.5 rounded border border-slate-800">
              Structural Damage Heatmap
            </span>
          </div>
        </div>
      );
    }
  };

  return (
    <>
      <div className={`relative group overflow-hidden rounded-xl bg-slate-950 border border-slate-800 ${className}`}>
        {/* Render Actual Image if no error */}
        {!error ? (
          <>
            <img
              src={src}
              alt={alt}
              onLoad={() => setLoading(false)}
              onError={() => {
                setError(true);
                setLoading(false);
              }}
              className={`w-full h-full object-cover transition-transform duration-500 group-hover:scale-105 ${
                loading ? 'opacity-0' : 'opacity-100'
              }`}
            />

            {/* Hover overlay with maximize button */}
            {!loading && (
              <div className="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                <button
                  onClick={() => setIsPreviewOpen(true)}
                  className="px-3 py-1.5 rounded-lg bg-cyan-500 text-slate-950 font-mono text-xs font-bold flex items-center gap-1.5 shadow-lg"
                >
                  <FiEye className="w-4 h-4" />
                  <span>Enlarge</span>
                </button>
              </div>
            )}

            {/* Loading Spinner */}
            {loading && (
              <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80">
                <div className="w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            )}
          </>
        ) : (
          renderFallbackVisual()
        )}
      </div>

      {/* Fullscreen Lightbox Modal */}
      {isPreviewOpen && !error && (
        <div 
          onClick={() => setIsPreviewOpen(false)}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/90 backdrop-blur-md cursor-pointer"
        >
          <div className="relative max-w-4xl max-h-[90vh] glass-panel p-2 rounded-2xl border border-cyan-500/40">
            <img src={src} alt={alt} className="max-w-full max-h-[85vh] rounded-xl object-contain" />
            <div className="p-3 text-center font-mono text-xs text-cyan-300 font-semibold">
              {title} • Click anywhere to close
            </div>
          </div>
        </div>
      )}
    </>
  );
}
