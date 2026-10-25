import { useState, useRef, useCallback } from 'react';

export function useFactCheck() {
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(null);
  const [stepMessage, setStepMessage] = useState('');
  const [extractedClaims, setExtractedClaims] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const abortControllerRef = useRef(null);

  const startFactCheck = useCallback(async (input) => {
    if (!input || !input.trim()) return;

    // Reset previous states
    setLoading(true);
    setStep('initializing');
    setStepMessage('Connecting to FactCheck Radar agent pipeline...');
    setExtractedClaims([]);
    setResult(null);
    setError(null);

    // Cancel prior request if any
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch('/api/factcheck', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ input: input.trim() }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        let errMessage = `Error ${response.status}: ${response.statusText}`;
        try {
          const errData = await response.json();
          if (errData.detail) errMessage = errData.detail;
        } catch (_) {}
        throw new Error(errMessage);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop() || ''; // Keep trailing incomplete event chunk

        for (const evt of events) {
          if (!evt.trim()) continue;
          const lines = evt.split('\n');
          let eventType = 'message';
          let dataStr = '';

          for (const line of lines) {
            if (line.startsWith('event:')) {
              eventType = line.slice(6).trim();
            } else if (line.startsWith('data:')) {
              dataStr += line.slice(5).trim();
            }
          }

          if (!dataStr) continue;

          try {
            const data = JSON.parse(dataStr);
            if (eventType === 'step') {
              setStep(data.step);
              setStepMessage(data.message);
            } else if (eventType === 'claims') {
              setExtractedClaims(data.claims || []);
            } else if (eventType === 'result') {
              setResult(data);
              setStep('done');
              setStepMessage('Fact-check complete!');
            } else if (eventType === 'error') {
              setError(data.message || 'An error occurred during verification');
              setStep('error');
            }
          } catch (e) {
            console.error('Failed to parse SSE payload:', dataStr, e);
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Failed to connect to agent');
        setStep('error');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setLoading(false);
    setStep(null);
    setStepMessage('');
    setExtractedClaims([]);
    setResult(null);
    setError(null);
  }, []);

  return {
    loading,
    step,
    stepMessage,
    extractedClaims,
    result,
    error,
    startFactCheck,
    reset,
  };
}
