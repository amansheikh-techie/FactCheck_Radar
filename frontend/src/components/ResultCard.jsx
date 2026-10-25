import React from 'react';
import { VerdictBadge } from './VerdictBadge';
import { ConfidenceMeter } from './ConfidenceMeter';
import { EvidenceList } from './EvidenceList';

export function ResultCard({ claimVerdict, index }) {
  if (!claimVerdict) return null;

  const { claim, verdict, confidence, explanation, citations } = claimVerdict;

  return (
    <div className="glass-panel rounded-2xl p-6 shadow-sm transition-all hover:shadow-md animate-fade-in relative overflow-hidden">
      {/* Top Header: Claim Number & Verdict & Meter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <span className="w-7 h-7 rounded-lg bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-mono font-bold text-xs flex items-center justify-center shrink-0">
            #{index + 1}
          </span>
          <VerdictBadge verdict={verdict} size="lg" />
        </div>
        <ConfidenceMeter confidence={confidence} />
      </div>

      {/* Claim statement */}
      <div className="mt-4">
        <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white leading-snug">
          "{claim}"
        </h3>
      </div>

      {/* 2-3 sentence Reasoning Explanation */}
      <div className="mt-3 p-3.5 rounded-xl bg-slate-100/70 dark:bg-slate-900/50 border border-slate-200/60 dark:border-slate-800/80">
        <div className="text-xs font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-1 font-mono">
          Agent Reasoning
        </div>
        <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
          {explanation}
        </p>
      </div>

      {/* Cited Evidence & Sources */}
      <EvidenceList citations={citations} />
    </div>
  );
}
