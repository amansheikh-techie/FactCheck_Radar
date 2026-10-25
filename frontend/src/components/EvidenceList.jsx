import React, { useState } from 'react';
import { ChevronDown, ChevronUp, ExternalLink, ShieldCheck, ShieldAlert, Minus } from 'lucide-react';

const STANCE_BADGES = {
  supports: {
    label: 'Supports',
    classes: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-500/30',
    icon: ShieldCheck,
  },
  contradicts: {
    label: 'Contradicts',
    classes: 'bg-rose-500/15 text-rose-700 dark:text-rose-400 border-rose-500/30',
    icon: ShieldAlert,
  },
  neutral: {
    label: 'Neutral',
    classes: 'bg-slate-500/15 text-slate-700 dark:text-slate-400 border-slate-500/30',
    icon: Minus,
  },
};

export function EvidenceList({ citations = [] }) {
  const [expanded, setExpanded] = useState(true);

  if (!citations || citations.length === 0) {
    return (
      <div className="text-xs text-slate-500 dark:text-slate-400 italic py-2">
        No external web citations retrieved for this claim.
      </div>
    );
  }

  return (
    <div className="mt-4 border-t border-slate-100 dark:border-slate-800/80 pt-3">
      <button
        onClick={() => setExpanded(prev => !prev)}
        className="flex items-center justify-between w-full text-left text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 transition-colors py-1 focus:outline-none"
      >
        <span className="flex items-center gap-1.5 uppercase tracking-wider font-mono">
          <span>Cited Sources & Evidence</span>
          <span className="px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-800 text-[10px] font-bold">
            {citations.length}
          </span>
        </span>
        {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {expanded && (
        <div className="mt-3 space-y-2.5 animate-fade-in">
          {citations.map((cite, i) => {
            const stanceConfig = STANCE_BADGES[cite.stance] || STANCE_BADGES.neutral;
            const StanceIcon = stanceConfig.icon;

            return (
              <div
                key={i}
                className="p-3 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white/50 dark:bg-slate-900/40 hover:border-slate-300 dark:hover:border-slate-700 transition-all text-xs"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="w-5 h-5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono font-bold flex items-center justify-center text-[10px]">
                      {cite.number || i + 1}
                    </span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200 line-clamp-1">
                      {cite.title || 'Source Reference'}
                    </span>
                    <span className="text-[11px] text-slate-600 dark:text-slate-400 font-mono">
                      ({cite.domain})
                    </span>
                  </div>

                  <span
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md border text-[10px] font-medium shrink-0 ${stanceConfig.classes}`}
                  >
                    <StanceIcon className="w-3 h-3" />
                    {stanceConfig.label}
                  </span>
                </div>

                <div className="mt-2 flex items-center justify-end">
                  <a
                    href={cite.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-600 dark:text-emerald-400 hover:underline"
                  >
                    <span>View original source</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
