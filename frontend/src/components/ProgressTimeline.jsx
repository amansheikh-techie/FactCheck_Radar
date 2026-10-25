import React from 'react';
import { CheckCircle2, Loader2, Circle, AlertCircle } from 'lucide-react';

const PIPELINE_STEPS = [
  { id: 'extracting_claims', label: 'Extracting Checkable Claims', model: 'Nemotron Nano' },
  { id: 'generating_queries', label: 'Generating Neutral Search Queries', model: 'Nemotron Nano' },
  { id: 'searching', label: 'Retrieving Web Evidence', model: 'Tavily Search API' },
  { id: 'assessing_sources', label: 'Assessing Source Stances', model: 'Nemotron Nano' },
  { id: 'reasoning', label: 'Weighing Evidence & Verdict', model: 'Nemotron Ultra' },
];

export function ProgressTimeline({ currentStep, message, error }) {
  const getStepStatus = (stepId, index) => {
    if (error) return 'error';
    if (!currentStep) return 'pending';
    if (currentStep === 'done') return 'completed';

    const stepOrder = [
      'fetching_url',
      'extracting_claims',
      'generating_queries',
      'searching',
      'assessing_sources',
      'reasoning',
      'done'
    ];

    const currentIndex = stepOrder.indexOf(currentStep);
    const thisIndex = stepOrder.indexOf(stepId);

    if (currentIndex > thisIndex) return 'completed';
    if (currentIndex === thisIndex) return 'running';
    return 'pending';
  };

  return (
    <div className="glass-panel rounded-2xl p-6 shadow-sm border border-slate-200/80 dark:border-slate-800 animate-fade-in">
      <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </span>
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200 font-mono">
            Autonomous Agent Pipeline
          </h3>
        </div>
        <span className="text-xs font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
          Live Execution
        </span>
      </div>

      {/* Message alert box */}
      {message && (
        <div className="my-4 px-3.5 py-2.5 rounded-xl bg-emerald-500/10 dark:bg-emerald-500/15 border border-emerald-500/20 text-xs font-medium text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin shrink-0 text-emerald-600 dark:text-emerald-400" />
          <span>{message}</span>
        </div>
      )}

      {/* Timeline Steps */}
      <div className="mt-4 space-y-3">
        {PIPELINE_STEPS.map((step, idx) => {
          const status = getStepStatus(step.id, idx);

          return (
            <div
              key={step.id}
              className={`flex items-center justify-between p-3 rounded-xl transition-all ${
                status === 'running'
                  ? 'bg-emerald-500/10 dark:bg-emerald-500/20 border border-emerald-500/30'
                  : 'bg-white/40 dark:bg-slate-900/30 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-3">
                {status === 'completed' ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
                ) : status === 'running' ? (
                  <Loader2 className="w-5 h-5 text-emerald-500 animate-spin shrink-0" />
                ) : status === 'error' ? (
                  <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
                ) : (
                  <Circle className="w-5 h-5 text-slate-300 dark:text-slate-700 shrink-0" />
                )}

                <div>
                  <div
                    className={`text-xs font-semibold ${
                      status === 'running'
                        ? 'text-emerald-700 dark:text-emerald-300'
                        : status === 'completed'
                        ? 'text-slate-900 dark:text-slate-100'
                        : 'text-slate-500 dark:text-slate-400'
                    }`}
                  >
                    {step.label}
                  </div>
                </div>
              </div>

              <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 font-medium">
                {step.model}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
