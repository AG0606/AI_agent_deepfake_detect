export type GatewayStatus = 'ONLINE' | 'OFFLINE';

export interface SystemStats {
  totalCalls: number;
  totalChunks: number;
  totalAudioBytes: number;
  recordings: number;
  totalStorageBytes: number;
}

export interface NetworkInfo {
  recommendedIp: string;
  interfaces: string[];
  port: number;
}

export interface LiveSession {
  sessionId: string;
  status: 'STREAMING' | 'COMPLETED';
  rms: number;
  bytes: number;
  bufferedBytes: number;
  chunkBytes: number;
  chunksEmitted: number;
}

export interface DecisionTrace {
  step: number;
  thought: string;
  tool_executed: string;
  tool_output: string;
}

export interface SentinelAgentVerdict {
  session_id: string;
  window_seq: number;
  timestamp_ms: number;
  verdict: 'SAFE' | 'SUSPICIOUS' | 'THREAT_DETECTED' | 'ATTACK_CONFIRMED' | string;
  action: 'ALLOW' | 'MONITOR' | 'CHALLENGE' | 'ALERT_AND_ANCHOR' | 'TERMINATE_AND_ANCHOR' | string;
  composite_threat_score: number;
  acoustic_score: number;
  semantic_score: number;
  caller_reputation: string;
  reasoning_summary: string;
  trace: DecisionTrace[];
  intervention_details: Record<string, any>;
}

export interface SentinelIntervention {
  type: string;
  session_id: string;
  reason?: string;
  prompt?: string;
  urgency: 'LOW' | 'HIGH' | 'CRITICAL';
}

export interface Chunk {
  sequence: number;
  bytes: number;
  durationMs: number;
  timestampMs: number;
  mlStatus: 'PENDING' | 'SENT' | 'OK' | 'DETECTOR_UNAVAILABLE' | 'DECODE_ERROR' | string;
  deepfakeScore?: number | null;
  agentVerdict?: SentinelAgentVerdict;
  rawResult?: any;
  latencyMs?: number;
  anomalyScore?: number;
  speakerMatch?: string;
  transcript?: string;
}

export interface ConnectionEvent {
  id: string;
  call_id: string;
  session_id: string;
  event_type: string;
  created_at: string;
}

export interface Call {
  id: string;
  session_id: string;
  source: string;
  status: string;
  created_at: string;
  ended_at: string | null;
  duration_ms: number;
  ai_likelihood_pct: number | null;
  transcript?: string | null;
  audio_streams?: {
    sample_rate: number;
    channels: number;
    encoding: string;
    bytes_received: number;
  }[];
  recordings?: {
    id: string;
    format: string;
    size_bytes: number;
    duration_ms: number;
  }[];
}
