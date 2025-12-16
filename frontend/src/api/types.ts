/**
 * TypeScript interfaces for the Cluas Huginn API.
 * These mirror the Pydantic models in src/api/models.py
 */

// =============================================================================
// Shared Types
// =============================================================================

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  speaker?: string;  // Character name for assistant messages
  emoji?: string;
  timestamp?: string;
}

export interface CharacterInfo {
  name: string;
  emoji: string;
  color: string;
}

// Character constants (client-side reference)
export const CHARACTERS: Record<string, CharacterInfo> = {
  corvus: { name: 'Corvus', emoji: '🦅', color: '#2c3e50' },
  magpie: { name: 'Magpie', emoji: '🐦', color: '#8e44ad' },
  raven: { name: 'Raven', emoji: '🦢', color: '#34495e' },
  crow: { name: 'Crow', emoji: '🐦‍⬛', color: '#1a1a1a' },
} as const;

// =============================================================================
// Chat API
// =============================================================================

export interface ChatRequest {
  message: string;
  history: Message[];
  apiKey?: string | null;
  mentions?: string[];  // Pre-parsed @mentions from client
}

export interface ChatResponseMetadata {
  responding_characters: string[];
  timestamp: string;
  duration_ms?: number;
}

export interface ChatResponse {
  history: Message[];
  metadata: ChatResponseMetadata;
}

// WebSocket message types
export type WSChatMessageType = 'start' | 'chunk' | 'done' | 'error';

export interface WSChatMessage {
  type: WSChatMessageType;
  character?: string;
  content?: string;
  error?: string;
}

// =============================================================================
// Deliberation API
// =============================================================================

export interface DeliberationRequest {
  question: string;
  rounds: 1 | 2 | 3;
  summariser: string;
  apiKey?: string | null;
}

export type Phase = 'thesis' | 'antithesis' | 'synthesis';

export interface PhaseEntry {
  cycle: number;
  phase: Phase;
  character: string;
  content: string;
  timestamp?: string;
}

export interface CycleSummary {
  cycle: number;
  summary: string;
}

export interface FinalSummary {
  by: string;
  content: string;
}

export interface DeliberationMetadata {
  character_order: string[];
  seed: number;
  duration_ms?: number;
}

export interface DeliberationResponse {
  question: string;
  rounds: number;
  phases: {
    thesis: PhaseEntry[];
    antithesis: PhaseEntry[];
    synthesis: PhaseEntry[];
  };
  cycle_summaries: CycleSummary[];
  final_summary: FinalSummary;
  metadata: DeliberationMetadata;
}

// WebSocket message types for deliberation streaming
export type WSDeliberationMessageType = 
  | 'phase_start' 
  | 'character_start' 
  | 'chunk' 
  | 'character_done' 
  | 'phase_done' 
  | 'summary' 
  | 'done' 
  | 'error';

export interface WSDeliberationMessage {
  type: WSDeliberationMessageType;
  phase?: Phase;
  cycle?: number;
  character?: string;
  content?: string;
  error?: string;
}

// =============================================================================
// System / Meta
// =============================================================================

export interface HealthResponse {
  status: 'ok' | 'degraded' | 'error';
  gradio_available: boolean;
  timestamp: string;
}

export interface CharactersResponse {
  characters: CharacterInfo[];
}

// =============================================================================
// Theater Mode Types (for the killer feature)
// =============================================================================

export interface TheaterState {
  isPlaying: boolean;
  currentPhase: Phase | null;
  currentCycle: number;
  currentCharacterIndex: number;
  speed: 'slow' | 'normal' | 'fast';  // Playback speed
}

export interface TheaterEntry extends PhaseEntry {
  // Extended for theater mode animation
  animationDelay?: number;
  isActive?: boolean;
  isComplete?: boolean;
}
