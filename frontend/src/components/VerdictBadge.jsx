import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, HelpCircle, AlertCircle, MinusCircle } from 'lucide-react';

const VERDICT_STYLES = {
  'True': {
    bg: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-700 dark:text-emerald-400',
    icon: CheckCircle2,
    dot: 'bg-emerald-500',
  },
  'Mostly True': {
    bg: 'bg-green-500/15 border-green-500/30 text-green-700 dark:text-green-400',
    icon: CheckCircle2,
    dot: 'bg-green-500',
  },
  'Mixed': {
    bg: 'bg-amber-500/15 border-amber-500/30 text-amber-700 dark:text-amber-400',
    icon: AlertTriangle,
    dot: 'bg-amber-500',
  },
  'Mostly False': {
    bg: 'bg-orange-500/15 border-orange-500/30 text-orange-700 dark:text-orange-400',
    icon: AlertCircle,
    dot: 'bg-orange-500',
  },
  'False': {
    bg: 'bg-rose-500/15 border-rose-500/30 text-rose-700 dark:text-rose-400',
    icon: XCircle,
    dot: 'bg-rose-500',
  },
  'Unverifiable': {
    bg: 'bg-slate-500/15 border-slate-500/30 text-slate-700 dark:text-slate-400',
    icon: HelpCircle,
    dot: 'bg-slate-400',
  },
};

export function VerdictBadge({ verdict, size = 'md' }) {
  const config = VERDICT_STYLES[verdict] || VERDICT_STYLES['Unverifiable'];
  const Icon = config.icon;

  const sizeClasses = size === 'lg' 
    ? 'px-4 py-1.5 text-base gap-2 font-bold'
    : 'px-3 py-1 text-sm gap-1.5 font-semibold';

  return (
    <span
      className={`inline-flex items-center rounded-full border shadow-sm ${config.bg} ${sizeClasses} transition-all`}
    >
      <Icon className={size === 'lg' ? 'w-5 h-5' : 'w-4 h-4'} />
      <span>{verdict}</span>
    </span>
  );
}
