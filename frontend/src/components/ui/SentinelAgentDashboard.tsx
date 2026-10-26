"use client";

import React, { useState, useEffect } from 'react';
import { useGatewayStore } from '@/stores/gateway-store';
import {
  ShieldAlert,
  ShieldCheck,
  HelpCircle,
  AlertTriangle,
  Terminal,
  Cpu,
  Eye,
  Sliders,
  Mic,
  UploadCloud,
  FileAudio,
  CheckCircle2,
  RefreshCw,
  FileText,
  Lock,
} from 'lucide-react';

export function SentinelAgentDashboard() {
  const agentVerdicts = useGatewayStore(s => s.agentVerdicts);
  const activeIntervention = useGatewayStore(s => s.activeIntervention);
  const dismissIntervention = useGatewayStore(s => s.dismissIntervention);

  // ── 1. Deliberation Simulation State ─────────────────────────────────
  const [testSessionId, setTestSessionId] = useState('demo-session-agent');
  const [callerId, setCallerId] = useState('+919876543210');
  const [transcript, setTranscript] = useState('Digital arrest warrant issued by CBI. Do not disconnect the video call, transfer money to safe custody account immediately.');
  const [acousticScore, setAcousticScore] = useState(82);
  const [deliberating, setDeliberating] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  // ── 2. Weight Configuration State ────────────────────────────────────
  const [acousticWeight, setAcousticWeight] = useState(0.50);
  const [semanticWeight, setSemanticWeight] = useState(0.50);
  const [challengeThreshold, setChallengeThreshold] = useState(50.0);
  const [criticalThreshold, setCriticalThreshold] = useState(75.0);
  const [savingWeights, setSavingWeights] = useState(false);
  const [weightsSavedMsg, setWeightsSavedMsg] = useState('');

  // ── 3. Audio Transcription State ─────────────────────────────────────
  const [selectedAudioFile, setSelectedAudioFile] = useState<File | null>(null);
  const [transcribing, setTranscribing] = useState(false);
  const [transcriptionResult, setTranscriptionResult] = useState<any>(null);

  // Load active weights on mount
  useEffect(() => {
    fetch('http://localhost:8011/api/config/agent')
      .then(res => res.json())
      .then(data => {
        if (data.config) {
          setAcousticWeight(data.config.acoustic_weight);
          setSemanticWeight(data.config.semantic_weight);
          setChallengeThreshold(data.config.challenge_threshold);
          setCriticalThreshold(data.config.critical_alert_threshold);
        }
      })
      .catch(() => {});
  }, []);

  const sessionIds = Object.keys(agentVerdicts);
  const latestLiveVerdict = sessionIds.length > 0 ? agentVerdicts[sessionIds[sessionIds.length - 1]] : null;
  const displayVerdict = testResult || latestLiveVerdict;

  // Handle saving weight configuration
  const handleSaveWeights = async () => {
    setSavingWeights(true);
    setWeightsSavedMsg('');
    try {
      const res = await fetch('http://localhost:8011/api/config/agent', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          acoustic_weight: Number(acousticWeight),
          semantic_weight: Number(semanticWeight),
          challenge_threshold: Number(challengeThreshold),
          critical_alert_threshold: Number(criticalThreshold),
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setWeightsSavedMsg('Weights saved and live!');
        setTimeout(() => setWeightsSavedMsg(''), 3000);
      } else {
        alert(data.detail || 'Failed to save weights');
      }
    } catch (err: any) {
      alert('Error updating weights: ' + err.message);
    } finally {
      setSavingWeights(false);
    }
  };

  // Handle audio transcription upload
  const handleTranscribeAudio = async () => {
    if (!selectedAudioFile) return;
    setTranscribing(true);
    try {
      const formData = new FormData();
      formData.append('audio', selectedAudioFile);

      const res = await fetch('http://localhost:8011/api/transcribe', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setTranscriptionResult(data);
      if (data.transcript) {
        setTranscript(data.transcript);
      }
    } catch (err: any) {
      alert('Transcription failed: ' + err.message);
    } finally {
      setTranscribing(false);
    }
  };

  // Handle running agent deliberation
  const handleTestDeliberation = async () => {
    setDeliberating(true);
    try {
      const res = await fetch('http://localhost:8011/api/agent/deliberate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: testSessionId,
          window_seq: 1,
          acoustic_score: Number(acousticScore),
          transcript: transcript,
          caller_id: callerId,
        }),
      });
      const data = await res.json();
      if (data.verdict) {
        setTestResult(data.verdict);
      }
    } catch (err) {
      console.error('Deliberation error:', err);
    } finally {
      setDeliberating(false);
    }
  };

  const getActionBadge = (action: string) => {
    switch (action) {
      case 'ALERT_AND_ANCHOR':
      case 'TERMINATE_AND_ANCHOR':
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-red-500/20 text-red-400 border border-red-500/30">
            <AlertTriangle className="w-3.5 h-3.5" /> CRITICAL ALERT &amp; ANCHOR (ADVISORY)
          </span>
        );
      case 'CHALLENGE':
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
            <HelpCircle className="w-3.5 h-3.5" /> COGNITIVE CHALLENGE SUGGESTED
          </span>
        );
      case 'MONITOR':
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
            <Eye className="w-3.5 h-3.5" /> CONTINUOUS MONITORING
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <ShieldCheck className="w-3.5 h-3.5" /> SAFE (ALLOW)
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-xl">
      {/* Real-Time Advisory Intervention Banner */}
      {activeIntervention && (
        <div className="bg-red-950/80 border-2 border-red-500/80 rounded-xl p-5 flex items-center justify-between text-red-200 animate-pulse shadow-2xl">
          <div className="flex items-center gap-4">
            <AlertTriangle className="w-8 h-8 text-red-400" />
            <div>
              <div className="font-bold text-lg text-white flex items-center gap-2">
                CRITICAL SCAM ALERT &mdash; EVIDENCE ANCHORED (ADVISORY ONLY)
                <span className="text-xs bg-red-800 text-white px-2 py-0.5 rounded font-mono font-normal">Call Not Terminated</span>
              </div>
              <p className="text-sm text-red-300 mt-0.5">{activeIntervention.reason || activeIntervention.prompt}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={dismissIntervention}
              className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white font-semibold rounded-lg text-xs"
            >
              Dismiss Alert
            </button>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-indigo-400" />
              Autonomous Anti-Fraud Sentinel Agent
            </h2>
            <span className="px-2.5 py-0.5 rounded text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 font-mono">
              Advisory Mode &bull; Non-Terminating
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Multi-modal reasoning fusing acoustic deepfakes, conversational psychological intent, and OSINT caller threat intel.
          </p>
        </div>

        {displayVerdict && (
          <div className="flex items-center gap-3">
            {getActionBadge(displayVerdict.action)}
            <div className="text-right">
              <span className="text-[11px] uppercase tracking-wider text-slate-500 block">Threat Score</span>
              <span className="text-xl font-extrabold text-slate-100 font-mono">
                {displayVerdict.composite_threat_score}/100
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Dynamic Weight Tuning Panel */}
      <div className="bg-slate-950/70 rounded-xl p-5 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-indigo-400" />
            Sentinel Dynamic Weight Tuning &amp; Thresholds
          </h3>
          <div className="flex items-center gap-3">
            {weightsSavedMsg && (
              <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> {weightsSavedMsg}
              </span>
            )}
            <button
              onClick={handleSaveWeights}
              disabled={savingWeights}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${savingWeights ? 'animate-spin' : ''}`} />
              {savingWeights ? 'Saving...' : 'Save Weights to API'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
          <div className="space-y-1.5">
            <div className="flex justify-between text-slate-400">
              <span>Acoustic Weight:</span>
              <strong className="text-indigo-400 font-mono">{acousticWeight.toFixed(2)}</strong>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={acousticWeight}
              onChange={e => {
                const val = Number(e.target.value);
                setAcousticWeight(val);
                setSemanticWeight(Number((1.0 - val).toFixed(2)));
              }}
              className="w-full accent-indigo-500 cursor-pointer"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-slate-400">
              <span>Semantic Intent Weight:</span>
              <strong className="text-indigo-400 font-mono">{semanticWeight.toFixed(2)}</strong>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              value={semanticWeight}
              onChange={e => {
                const val = Number(e.target.value);
                setSemanticWeight(val);
                setAcousticWeight(Number((1.0 - val).toFixed(2)));
              }}
              className="w-full accent-indigo-500 cursor-pointer"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-slate-400">
              <span>Challenge Threshold:</span>
              <strong className="text-amber-400 font-mono">{challengeThreshold}</strong>
            </div>
            <input
              type="range"
              min="30"
              max="70"
              step="5"
              value={challengeThreshold}
              onChange={e => setChallengeThreshold(Number(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-slate-400">
              <span>Critical Alert Threshold:</span>
              <strong className="text-red-400 font-mono">{criticalThreshold}</strong>
            </div>
            <input
              type="range"
              min="60"
              max="95"
              step="5"
              value={criticalThreshold}
              onChange={e => setCriticalThreshold(Number(e.target.value))}
              className="w-full accent-red-500 cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* Main Grid: Deliberation Tester + Audio Transcription & Intent Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Interactive Deliberation Console & Whisper Audio Uploader */}
        <div className="bg-slate-950/60 rounded-xl p-5 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-emerald-400" />
              Live Call Deliberation Console
            </h3>
            <span className="text-xs text-slate-500 font-mono">POST /api/agent/deliberate</span>
          </div>

          {/* Audio File Transcription Dropzone */}
          <div className="p-3 rounded-lg border border-dashed border-slate-700 bg-slate-900/40 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Mic className="w-3.5 h-3.5 text-indigo-400" />
                Upload Audio for Live Whisper ASR
              </span>
              {selectedAudioFile && (
                <span className="text-[11px] text-slate-400 font-mono">{selectedAudioFile.name}</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <input
                type="file"
                accept=".wav,.mp3,.ogg,.m4a"
                onChange={e => setSelectedAudioFile(e.target.files?.[0] || null)}
                className="text-xs text-slate-400 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-slate-800 file:text-slate-200"
              />
              <button
                onClick={handleTranscribeAudio}
                disabled={!selectedAudioFile || transcribing}
                className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded text-xs font-medium flex items-center gap-1"
              >
                <UploadCloud className="w-3 h-3" />
                {transcribing ? 'Transcribing...' : 'Transcribe'}
              </button>
            </div>
            {transcriptionResult && (
              <div className="text-[11px] text-emerald-400 font-mono bg-slate-950/80 p-2 rounded border border-slate-800">
                ✓ Transcribed ({transcriptionResult.detectedLanguage}): &ldquo;{transcriptionResult.transcript}&rdquo;
              </div>
            )}
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Caller ID (Registry OSINT)</label>
              <input
                type="text"
                value={callerId}
                onChange={e => setCallerId(e.target.value)}
                placeholder="+919876543210 (Try a known scam number or clean number)"
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1">
                Acoustic Deepfake Score: <span className="font-bold text-indigo-400">{acousticScore}%</span>
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={acousticScore}
                onChange={e => setAcousticScore(Number(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer"
              />
            </div>

            <div>
              <label className="text-xs text-slate-400 block mb-1">Conversation Transcript (Intent Analysis)</label>
              <textarea
                rows={3}
                value={transcript}
                onChange={e => setTranscript(e.target.value)}
                placeholder="Transcribed conversation..."
                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2 pt-1">
              <button
                onClick={handleTestDeliberation}
                disabled={deliberating}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium rounded-lg text-xs flex items-center gap-2 transition-colors"
              >
                <Cpu className="w-4 h-4" />
                {deliberating ? 'Agent Deliberating...' : 'Trigger Advisory Agent Cycle'}
              </button>

              <button
                onClick={() => {
                  setCallerId('+919876543210');
                  setAcousticScore(88);
                  setTranscript('Digital arrest warrant registered. CBI kotwali police aayegi, transfer 50000 to safe custody account immediately.');
                }}
                className="px-2.5 py-1.5 bg-red-950/50 hover:bg-red-900/50 border border-red-800 text-red-200 rounded text-xs"
              >
                Digital Arrest Preset
              </button>

              <button
                onClick={() => {
                  setCallerId('+919988776655');
                  setAcousticScore(15);
                  setTranscript('Official bank alert: Remember to never share your OTP or password with anyone calling you.');
                }}
                className="px-2.5 py-1.5 bg-emerald-950/50 hover:bg-emerald-900/50 border border-emerald-800 text-emerald-200 rounded text-xs"
              >
                Educational Warning Preset
              </button>
            </div>
          </div>
        </div>

        {/* Right: Decision Trace & Intent Category Inspector */}
        <div className="bg-slate-950/60 rounded-xl p-5 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-indigo-400" />
              Autonomous Decision Trace (Sense &rarr; Reason &rarr; Act)
            </h3>
            {displayVerdict && (
              <span className="text-xs text-slate-400 font-mono">
                Caller Rep: <strong className="text-amber-400">{displayVerdict.caller_reputation}</strong>
              </span>
            )}
          </div>

          {displayVerdict ? (
            <div className="space-y-3 max-h-[360px] overflow-y-auto pr-1">
              <div className="p-3 rounded-lg bg-indigo-950/40 border border-indigo-900/50 text-xs text-indigo-200">
                <span className="font-bold block text-indigo-300 mb-0.5">Summary Deliberation:</span>
                {displayVerdict.reasoning_summary}
              </div>

              {displayVerdict.trace?.map((step: any, idx: number) => (
                <div key={idx} className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between text-slate-400">
                    <span className="font-bold text-slate-200 flex items-center gap-1.5">
                      <span className="w-4 h-4 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center text-[10px]">
                        {step.step}
                      </span>
                      Tool: <code className="text-emerald-400">{step.tool_executed}</code>
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">Step {idx + 1}</span>
                  </div>
                  <p className="text-slate-300 italic">&ldquo;{step.thought}&rdquo;</p>
                  <div className="bg-slate-950 p-2 rounded text-[11px] font-mono text-cyan-300 border border-slate-800/80">
                    &bull; {step.tool_output}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-[280px] flex flex-col items-center justify-center text-slate-500 text-center space-y-2">
              <ShieldCheck className="w-10 h-10 opacity-30" />
              <p className="text-xs">No active agent evaluation yet.</p>
              <p className="text-[11px] text-slate-600">
                Trigger the deliberation cycle or upload audio to inspect the agent&apos;s step-by-step decision trace.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
