import React from 'react';

export function ConfidenceMeter({ confidence }) {
  const score = Math.max(0, Math.min(100, Math.round(confidence || 0)));

  // Color gradient based on confidence score
  let barColor = 'bg-rose-500';
  let textColor = 'text-rose-600 dark:text-rose-400';
  
  if (score >= 80) {
    barColor = 'bg-emerald-500';
    textColor = 'text-emerald-600 dark:text-emerald-400';
  } else if (score >= 60) {
    barColor = 'bg-green-500';
    textColor = 'text-green-600 dark:text-green-400';
  } else if (score >= 40) {
    barColor = 'bg-amber-500';
    textColor = 'text-amber-600 dark:text-amber-400';
  } else if (score >= 20) {
    barColor = 'bg-orange-500';
    textColor = 'text-orange-600 dark:text-orange-400';
  }

  return (
    <div className="flex flex-col gap-1.5 w-full max-w-[200px]" title={`Evidence confidence: ${score}%`}>
      <div className="flex items-center justify-between text-xs font-semibold">
        <span className="text-slate-500 dark:text-slate-400">Confidence</span>
        <span className={`${textColor} font-bold font-mono`}>{score}%</span>
      </div>
      <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden relative">
        <div
          className={`h-full ${barColor} transition-all duration-700 ease-out rounded-full`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}
