import type {
  ChatRequest,
  ChatResponse,
  CharactersResponse,
  DeliberationRequest,
  DeliberationResponse,
  HealthResponse,
  WSChatMessage,
  WSDeliberationMessage,
} from './types'

async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(path, { signal })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`HTTP ${res.status} ${res.statusText}${text ? `: ${text}` : ''}`)
  }
  return (await res.json()) as T
}

async function apiPost<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`HTTP ${res.status} ${res.statusText}${text ? `: ${text}` : ''}`)
  }
  return (await res.json()) as T
}

function wsBaseUrl(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${protocol}://${window.location.host}`
}

export function health(signal?: AbortSignal): Promise<HealthResponse> {
  return apiGet<HealthResponse>('/api/health', signal)
}

export function listCharacters(signal?: AbortSignal): Promise<CharactersResponse> {
  return apiGet<CharactersResponse>('/api/characters', signal)
}

export function chat(req: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
  return apiPost<ChatResponse>('/api/chat', req, signal)
}

export function deliberate(req: DeliberationRequest, signal?: AbortSignal): Promise<DeliberationResponse> {
  return apiPost<DeliberationResponse>('/api/deliberate', req, signal)
}

export function openChatStream(params: {
  onMessage: (msg: WSChatMessage) => void
  onError?: (ev: Event) => void
  onClose?: (ev: CloseEvent) => void
}): WebSocket {
  const ws = new WebSocket(`${wsBaseUrl()}/api/chat/stream`)

  ws.onmessage = (ev) => {
    try {
      params.onMessage(JSON.parse(ev.data) as WSChatMessage)
    } catch {
      // ignore malformed frames
    }
  }

  if (params.onError) ws.onerror = params.onError
  if (params.onClose) ws.onclose = params.onClose

  return ws
}

export function sendChatStreamRequest(ws: WebSocket, req: ChatRequest): void {
  if (ws.readyState !== WebSocket.OPEN) {
    throw new Error('WebSocket is not open. Current state: ' + ws.readyState)
  }
  ws.send(JSON.stringify(req))
}

export function openDeliberationStream(params: {
  request: DeliberationRequest
  onMessage: (msg: WSDeliberationMessage) => void
  onError?: (ev: Event) => void
  onClose?: (ev: CloseEvent) => void
}): WebSocket {
  const ws = new WebSocket(`${wsBaseUrl()}/api/deliberate/stream`)

  ws.onopen = () => {
    ws.send(JSON.stringify(params.request))
  }

  ws.onmessage = (ev) => {
    try {
      params.onMessage(JSON.parse(ev.data) as WSDeliberationMessage)
    } catch {
      // ignore malformed frames
    }
  }

  if (params.onError) ws.onerror = params.onError
  if (params.onClose) ws.onclose = params.onClose

  return ws
}
