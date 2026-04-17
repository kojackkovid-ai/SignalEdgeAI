import React from 'react';

interface ConfidenceGaugeProps {
  confidence: number; // 0-100
  label?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const ConfidenceGauge: React.FC<ConfidenceGaugeProps> = ({ 
  confidence = 0, 
  label = 'Confidence', 
  size = 'md' 
}) => {
  // Ensure confidence is a valid number
  const safeConfidence = typeof confidence === 'number' ? confidence : 0;
  
  const getColor = (conf: number) => {
    // Dark colors for readability on white background
    if (conf >= 75) return '#166534'; // Dark green
    if (conf >= 50) return '#92400e'; // Dark amber/brown
    return '#991b1b'; // Dark red
  };


  const getSizeClass = (s: string) => {
    const sizes: Record<string, string> = {
      sm: 'w-24 h-3',
      md: 'w-32 h-4',
      lg: 'w-48 h-6'
    };
    return sizes[s] || sizes.md;
  };

  return (
    <div className="confidence-gauge">
      <div className="flex items-center gap-2">
        <span className="text-xs text-gray-400 uppercase tracking-wider">
          {label}
        </span>
        <div className={`gauge-bar ${getSizeClass(size)}`}>
          <div 
            className="gauge-fill"
            style={{
              width: `${safeConfidence}%`,
              backgroundColor: getColor(safeConfidence)
            }}
          />
        </div>
        <span className="text-sm font-bold" style={{ color: getColor(safeConfidence) }}>
          {safeConfidence.toFixed(0)}%
        </span>
      </div>
      <div className="text-xs text-gray-500 mt-1">
        {safeConfidence >= 75 && '█ High Confidence'}
        {safeConfidence >= 50 && safeConfidence < 75 && '▌ Medium Confidence'}
        {safeConfidence < 50 && '▂ Low Confidence'}
      </div>
    </div>
  );
};

export default ConfidenceGauge;
