import React, { useEffect, useState } from 'react';
import { useFactCheck } from './hooks/useFactCheck';
import { HeroInput } from './components/HeroInput';
import { ProgressTimeline } from './components/ProgressTimeline';
import { ResultCard } from './components/ResultCard';
import { HowItWorks } from './components/HowItWorks';
import { ThemeToggle } from './components/ThemeToggle';
import { ShareButton } from './components/ShareButton';
import { Radar, AlertCircle, AlertTriangle, RotateCcw, ShieldCheck, Sparkles, Cpu } from 'lucide-react';

export default function App() {
  const {
    loading,
    step,
    stepMessage,
    extractedClaims,
    result,
    error,
    startFactCheck,
    reset,
  } = useFactCheck();

  const [healthData, setHealthData] = useState(null);

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((data) => setHealthData(data))
      .catch(() => {});
  }, []);

  const activeProvider = result?.provider && result.provider !== 'sample'
    ? result.provider
    : (healthData?.provider || 'nvidia');

  return (
    <div className="min-h-screen flex flex-col justify-between selection:bg-emerald-500 selection:text-white">
      {/* Top Navbar */}
      <header className="sticky top-0 z-50 glass-panel border-b border-slate-200/80 dark:border-slate-800/80 px-4 sm:px-8 py-3.5 transition-colors">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-emerald-600 via-teal-500 to-emerald-400 flex items-center justify-center text-white shadow-md shadow-emerald-500/20">
              <Radar className="w-6 h-6 animate-pulse-subtle" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-base sm:text-lg tracking-tight text-slate-900 dark:text-white">
                  FactCheck <span className="text-emerald-500 font-mono">Radar</span>
                </span>
                <span className="hidden sm:inline-flex px-2 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                  via {activeProvider}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium hidden sm:block">
                Autonomous Evidence Retrieval & Reasoning with NVIDIA Nemotron
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-8 sm:py-12 flex flex-col gap-8">
        {/* Hero Title Section */}
        <section className="text-center max-w-2xl mx-auto pt-2">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-200/60 dark:bg-slate-800/60 border border-slate-300/50 dark:border-slate-700/50 text-xs font-semibold text-slate-700 dark:text-slate-300 font-mono mb-4 shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-emerald-500" />
            <span>Nebius x NVIDIA Global AI Hackathon</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-black text-slate-900 dark:text-white tracking-tight leading-tight">
            Stop Misinformation with <span className="bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-500 bg-clip-text text-transparent">Transparent AI</span>
          </h1>
          <p className="mt-3 text-sm sm:text-base text-slate-600 dark:text-slate-400 leading-relaxed">
            Paste any viral claim, news headline, or article URL. Our autonomous multi-agent pipeline extracts checkable facts, retrieves real-time web evidence via Tavily, and reasons with NVIDIA Nemotron.
          </p>
        </section>

        {/* Hero Input Box */}
        <HeroInput onCheck={startFactCheck} loading={loading} />

        {/* Error Alert */}
        {error && (
          <div className="w-full max-w-3xl mx-auto p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 flex items-start justify-between gap-3 animate-fade-in text-sm">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div>
                <div className="font-bold">Investigation Encountered An Issue</div>
                <div className="mt-0.5 text-xs opacity-90">{error}</div>
              </div>
            </div>
            <button
              onClick={reset}
              className="p-1.5 rounded-lg hover:bg-rose-500/10 text-rose-700 dark:text-rose-400 transition-colors shrink-0"
              title="Reset"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Live Progress Timeline (Visible while loading or before result is complete) */}
        {loading && (
          <div className="w-full max-w-3xl mx-auto">
            <ProgressTimeline currentStep={step} message={stepMessage} error={error} />
          </div>
        )}

        {/* Extracted Claims Preview (Appears right after Step 1) */}
        {loading && extractedClaims.length > 0 && (
          <div className="w-full max-w-3xl mx-auto glass-panel rounded-2xl p-5 border border-slate-200/80 dark:border-slate-800 animate-fade-in">
            <div className="text-xs font-mono font-bold uppercase text-slate-500 dark:text-slate-400 tracking-wider mb-2">
              Detected Checkable Claims ({extractedClaims.length})
            </div>
            <div className="space-y-2">
              {extractedClaims.map((c, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-slate-800 dark:text-slate-200 bg-white/40 dark:bg-slate-900/40 p-2.5 rounded-xl border border-slate-200/50 dark:border-slate-800">
                  <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-mono font-bold text-[10px] flex items-center justify-center shrink-0">
                    {i + 1}
                  </span>
                  <span className="font-medium line-clamp-1 flex-1">"{c.claim}"</span>
                  <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-[10px] font-mono text-slate-600 dark:text-slate-400">
                    {c.category}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Results Section */}
        {result && (
          <section className="w-full max-w-3xl mx-auto space-y-6 animate-fade-in">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-500" />
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                  Investigation Verdicts ({result.claim_verdicts?.length || 0})
                </h2>
              </div>
              <div className="flex items-center gap-2">
                <ShareButton result={result} />
                <button
                  onClick={reset}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-semibold text-slate-600 dark:text-slate-400 transition-colors"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>New Check</span>
                </button>
              </div>
            </div>

            {/* Explicit Demo Mode / Live API Notice */}
            {(!result.is_live || result.status_notice || result.provider === 'sample') && (
              <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-700 dark:text-amber-400 flex items-start gap-3 animate-fade-in text-sm font-medium">
                <AlertTriangle className="w-5 h-5 shrink-0 text-amber-500 mt-0.5" />
                <div>
                  <div className="font-bold tracking-tight">
                    {result.status_notice || 'Live API unavailable - sample result'}
                  </div>
                  <div className="text-xs opacity-90 mt-0.5">
                    Showing demonstration schema result. FactCheck Radar is honest: never presenting sample data as live.
                  </div>
                </div>
              </div>
            )}

            {/* Provider and Models Used Info Tag */}
            <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono text-slate-500 dark:text-slate-400 bg-slate-100/80 dark:bg-slate-900/50 px-3 py-1.5 rounded-xl border border-slate-200/60 dark:border-slate-800">
              <span>Provider: <strong className="text-emerald-600 dark:text-emerald-400 uppercase">{result.provider || activeProvider}</strong></span>
              <span>•</span>
              <span>Fast: <strong className="text-slate-700 dark:text-slate-300">{result.models_used?.fast || result.model_fast}</strong></span>
              <span>•</span>
              <span>Reasoning: <strong className="text-slate-700 dark:text-slate-300">{result.models_used?.reasoning || result.model_reasoning}</strong></span>
            </div>

            {/* Verdict Cards */}
            <div className="space-y-5">
              {result.claim_verdicts?.map((cv, idx) => (
                <ResultCard key={idx} claimVerdict={cv} index={idx} />
              ))}
            </div>
          </section>
        )}

        {/* Technical Architecture Info */}
        <HowItWorks />
      </main>

      {/* Footer */}
      <footer className="glass-panel border-t border-slate-200/80 dark:border-slate-800/80 py-6 px-4 text-center text-xs text-slate-500 dark:text-slate-400 transition-colors mt-12">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2 font-mono">
            <span>
              Powered by <strong>NVIDIA Nemotron</strong> via <strong className="text-emerald-500 uppercase">{activeProvider}</strong>
            </span>
            <span className="text-slate-300 dark:text-slate-700">|</span>
            <span className="text-[11px] text-slate-400">
              {result?.models_used?.fast || healthData?.model_fast || 'nemotron-fast'} & {result?.models_used?.reasoning || healthData?.model_reasoning || 'nemotron-ultra'}
            </span>
          </div>
          <div className="flex items-center gap-4 text-xs font-medium">
            <span className="text-emerald-600 dark:text-emerald-400 font-mono">MIT License</span>
            <span>•</span>
            <a
              href="https://github.com/amansheikh-techie/FactCheck_Radar"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              GitHub Repository
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
