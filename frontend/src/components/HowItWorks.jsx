import React from 'react';
import { Cpu, Search, Brain, Shield, Layers } from 'lucide-react';

export function HowItWorks() {
  const architectures = [
    {
      icon: Cpu,
      title: 'NVIDIA Nemotron Nano',
      subtitle: 'Fast Execution (Nebius Token Factory)',
      description: 'Performs sub-agent tasks in parallel: checkable claim extraction, unbiased search query generation, and stance assessment on retrieved sources.',
      badge: 'Fast MoE'
    },
    {
      icon: Search,
      title: 'Tavily Web Search API',
      subtitle: 'Real-Time Evidence Retrieval',
      description: 'Executes targeted search queries across trusted sources. Deduplicates evidence by root domain to avoid single-outlet bias.',
      badge: 'Live Web'
    },
    {
      icon: Brain,
      title: 'NVIDIA Nemotron Ultra',
      subtitle: 'Frontier Reasoning (550B MoE)',
      description: 'Weighs supporting vs contradicting evidence, detects logical fallacies, calculates calibrated confidence scores, and formulates final verdicts.',
      badge: 'Deep Reasoning'
    },
  ];

  return (
    <div className="w-full max-w-4xl mx-auto mt-16 pt-12 border-t border-slate-200 dark:border-slate-800">
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-bold uppercase tracking-wider font-mono mb-3">
          <Layers className="w-3.5 h-3.5" />
          <span>System Architecture</span>
        </div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
          How FactCheck Radar Works
        </h2>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400 max-w-xl mx-auto">
          Combining tiered NVIDIA Nemotron models on Nebius Token Factory with Tavily's live search for trustworthy, auditable verification.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {architectures.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div
              key={idx}
              className="glass-panel rounded-2xl p-6 shadow-sm border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between hover:border-slate-300 dark:hover:border-slate-700 transition-all"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-semibold">
                    {item.badge}
                  </span>
                </div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  {item.title}
                </h3>
                <div className="text-xs text-emerald-600 dark:text-emerald-400 font-medium font-mono mb-2">
                  {item.subtitle}
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                  {item.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
