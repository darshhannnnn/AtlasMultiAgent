import React, { useRef, useState } from 'react';

export const GlassCard = ({ children, className = '', contentClassName = '', ...props }) => {
  const cardRef = useRef(null);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setCoords({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  return (
    <div
      ref={cardRef}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onMouseMove={handleMouseMove}
      className={`relative bg-white/30 backdrop-blur-2xl border border-white/50 shadow-[0_8px_40px_rgba(168,152,120,0.1),inset_0_1px_0_rgba(255,255,255,0.6)] rounded-2xl overflow-hidden transition-all duration-300 hover:bg-white/40 hover:border-white/65 min-h-0 ${className}`}
      {...props}
    >
      {/* Top glass shine */}
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/80 to-transparent pointer-events-none z-20" />

      {/* Liquid ripple glow on hover */}
      {isHovered && (
        <div
          className="absolute pointer-events-none rounded-full transition-opacity duration-300"
          style={{
            width: '280px',
            height: '280px',
            background: 'radial-gradient(circle, rgba(232, 223, 208, 0.35) 0%, rgba(255, 255, 255, 0.12) 45%, rgba(0, 0, 0, 0) 70%)',
            transform: 'translate(-50%, -50%)',
            left: `${coords.x}px`,
            top: `${coords.y}px`,
            zIndex: 1,
          }}
        />
      )}

      <div className={`relative z-10 w-full h-full min-h-0 ${contentClassName || 'p-6'}`}>{children}</div>
    </div>
  );
};

export default GlassCard;
