import React, { useState } from 'react';
import { Share2, Check, Copy } from 'lucide-react';

export function ShareButton({ result }) {
  const [copied, setCopied] = useState(false);

  if (!result || !result.claim_verdicts || result.claim_verdicts.length === 0) {
    return null;
  }

  const handleCopy = async () => {
    const lines = [
      `🔍 FactCheck Radar Investigation Report`,
      `Input: "${result.input}"`,
      `Verified via NVIDIA Nemotron on Nebius Token Factory & Tavily Search`,
      `----------------------------------------------------`,
    ];

    result.claim_verdicts.forEach((v, idx) => {
      lines.push(`Claim #${idx + 1}: "${v.claim}"`);
      lines.push(`Verdict: ${v.verdict} (Confidence: ${v.confidence}%)`);
      lines.push(`Explanation: ${v.explanation}`);
      if (v.citations && v.citations.length > 0) {
        lines.push(`Sources:`);
        v.citations.forEach((c) => {
          lines.push(`  - [${c.stance.toUpperCase()}] ${c.title} (${c.url})`);
        });
      }
      lines.push(``);
    });

    const textToCopy = lines.join('\n');
    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
    }
  };

  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-semibold shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500"
      title="Copy complete investigation report"
    >
      {copied ? (
        <>
          <Check className="w-4 h-4 text-emerald-500" />
          <span className="text-emerald-600 dark:text-emerald-400">Report Copied!</span>
        </>
      ) : (
        <>
          <Copy className="w-4 h-4" />
          <span>Copy Report</span>
        </>
      )}
    </button>
  );
}
