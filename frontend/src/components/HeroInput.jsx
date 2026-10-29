import React, { useState } from 'react';
import { Search, Sparkles, Link, ArrowRight, X } from 'lucide-react';

const SAMPLE_CLAIMS = [
  {
    type: 'Scientific (True)',
    text: 'Water boils at 100 degrees Celsius at standard atmospheric pressure.',
    tag: 'Science',
  },
  {
    type: 'Myth (False)',
    text: 'The Great Wall of China is visible from space with the naked eye.',
    tag: 'History',
  },
  {
    type: 'Ambiguous (Mixed)',
    text: 'Drinking two cups of coffee daily extends human life expectancy.',
    tag: 'Health',
  },
  {
    type: 'Article URL',
    text: 'https://en.wikipedia.org/wiki/Apollo_11',
    tag: 'URL',
  },
];

export function HeroInput({ onCheck, loading }) {
  const [input, setInput] = useState('');
  const [demoMode, setDemoMode] = useState(false);
  const maxLength = 5000;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onCheck(input, demoMode);
  };

  const handleSelectSample = (sampleText) => {
    setInput(sampleText);
    onCheck(sampleText, demoMode);
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Input Form Card */}
      <div className="glass-panel rounded-3xl p-4 sm:p-6 shadow-xl border border-slate-200/90 dark:border-slate-800 relative transition-all focus-within:ring-2 focus-within:ring-emerald-500/50">
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div className="relative">
            <textarea
              id="claim-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Paste a headline, claim, rumor, or article URL to verify..."
              rows={3}
              maxLength={maxLength}
              disabled={loading}
              className="w-full resize-none rounded-2xl bg-slate-50 dark:bg-slate-900/80 p-4 text-sm sm:text-base text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none border border-slate-200 dark:border-slate-800/80 focus:border-emerald-500 transition-all leading-relaxed"
            />
            {input && !loading && (
              <button
                type="button"
                onClick={() => setInput('')}
                className="absolute top-3 right-3 p-1.5 rounded-full text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
                title="Clear input"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
            <div className="flex items-center gap-3">
              <button
                type="button"
                id="mode-toggle-btn"
                onClick={() => setDemoMode(!demoMode)}
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-[11px] font-mono font-medium border transition-colors ${
                  demoMode
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400'
                    : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400'
                }`}
                title="Toggle between live inference and explicit demo sample mode"
              >
                <span className={`w-2 h-2 rounded-full ${demoMode ? 'bg-amber-500' : 'bg-emerald-500 animate-pulse'}`} />
                <span>{demoMode ? 'Sample Demo Mode' : 'Live AI Mode'}</span>
              </button>
              <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 font-mono">
                <span>{input.length}/{maxLength}</span>
              </div>
            </div>

            <button
              id="verify-button"
              type="submit"
              disabled={loading || !input.trim()}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-sm shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 dark:focus:ring-offset-slate-900"
            >
              <Search className="w-4 h-4" />
              <span>{loading ? 'Investigating...' : 'Verify Claim'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>

      {/* Clickable Example Chips */}
      <div className="mt-5">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2.5 font-mono">
          <Sparkles className="w-3.5 h-3.5 text-amber-500" />
          <span>Quick Demo Examples:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_CLAIMS.map((sample, idx) => (
            <button
              key={idx}
              id={`sample-chip-${idx}`}
              onClick={() => handleSelectSample(sample.text)}
              disabled={loading}
              className="text-xs text-left px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/60 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-all flex items-center gap-2 shadow-sm hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
            >
              <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold font-mono">
                {sample.tag}
              </span>
              <span className="line-clamp-1">{sample.text}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
