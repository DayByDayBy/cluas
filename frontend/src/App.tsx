import './App.css'
import { useEffect, useMemo, useRef, useState } from 'react'
import type { CharacterInfo, ChatRequest, Message, Phase, PhaseEntry } from './api/types'
import { listCharacters, openChatStream, openDeliberationStream, sendChatStreamRequest } from './api/client'

type Tab = 'chat' | 'deliberation'

function nowIso(): string {
  return new Date().toISOString()
}

function isPhase(value: unknown): value is Phase {
  return value === 'thesis' || value === 'antithesis' || value === 'synthesis'
}

function App() {
  const [tab, setTab] = useState<Tab>('chat')
  const [apiKey, setApiKey] = useState<string>('')
  const [characters, setCharacters] = useState<CharacterInfo[]>([])

  const characterByName = useMemo(() => {
    const map = new Map<string, CharacterInfo>()
    for (const c of characters) map.set(c.name, c)
    return map
  }, [characters])

  useEffect(() => {
    let cancelled = false
    listCharacters()
      .then((res) => {
        if (!cancelled) setCharacters(res.characters)
      })
      .catch(() => {
        if (!cancelled) setCharacters([])
      })
    return () => {
      cancelled = true
    }
  }, [])

  const [chatHistory, setChatHistory] = useState<Message[]>([])
  const [chatInput, setChatInput] = useState('')
  const [chatError, setChatError] = useState<string | null>(null)
  const [chatStreamingByCharacter, setChatStreamingByCharacter] = useState<Record<string, string>>({})
  const chatWsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const ws = openChatStream({
      onMessage: (msg) => {
        if (msg.type === 'start' && msg.character) {
          const character = msg.character
          setChatStreamingByCharacter((prev) => ({ ...prev, [character]: '' }))
          return
        }

        if (msg.type === 'chunk' && msg.character && msg.content) {
          const character = msg.character
          const chunk = msg.content
          setChatStreamingByCharacter((prev) => ({
            ...prev,
            [character]: `${prev[character] ?? ''}${chunk}`,
          }))
          return
        }

        if (msg.type === 'done' && msg.character) {
          const character = msg.character
          const content = (msg.content ?? '').trim()
          if (content) {
            setChatHistory((prev) => [
              ...prev,
              {
                role: 'assistant',
                content,
                speaker: character,
                emoji: characterByName.get(character)?.emoji,
                timestamp: nowIso(),
              },
            ])
          }
          setChatStreamingByCharacter((prev) => {
            const next = { ...prev }
            delete next[character]
            return next
          })
          return
        }

        if (msg.type === 'error') {
          setChatError(msg.error ?? 'Chat stream error')
        }
      },
      onError: () => {
        setChatError('WebSocket error')
      },
    })

    chatWsRef.current = ws
    return () => {
      chatWsRef.current = null
      ws.close()
    }
  }, [characterByName])

  const chatIsBusy = useMemo(
    () => Object.keys(chatStreamingByCharacter).length > 0,
    [chatStreamingByCharacter],
  )

  function sendChat(): void {
    setChatError(null)
    const message = chatInput.trim()
    if (!message) return

    const ws = chatWsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      setChatError('Chat socket not connected')
      return
    }

    const req: ChatRequest = {
      message,
      history: chatHistory,
      apiKey: apiKey.trim() ? apiKey.trim() : null,
    }

    sendChatStreamRequest(ws, req)
    setChatHistory((prev) => [...prev, { role: 'user', content: message, timestamp: nowIso() }])
    setChatInput('')
  }

  const [delibQuestion, setDelibQuestion] = useState('')
  const [delibRounds, setDelibRounds] = useState<1 | 2 | 3>(1)
  const [delibSummariser, setDelibSummariser] = useState('Moderator')
  const [delibIsRunning, setDelibIsRunning] = useState(false)
  const [delibError, setDelibError] = useState<string | null>(null)
  const [delibStatus, setDelibStatus] = useState<{ cycle: number; phase: Phase | null; character: string | null }>(
    { cycle: 1, phase: null, character: null },
  )
  const [delibStreamingText, setDelibStreamingText] = useState('')
  const [delibEntries, setDelibEntries] = useState<PhaseEntry[]>([])
  const [cycleSummaries, setCycleSummaries] = useState<Array<{ cycle: number; summary: string }>>([])
  const [finalSummary, setFinalSummary] = useState<{ by: string; content: string } | null>(null)
  const delibWsRef = useRef<WebSocket | null>(null)

  const [theaterPlaying, setTheaterPlaying] = useState(false)
  const [theaterSpeed, setTheaterSpeed] = useState<'slow' | 'normal' | 'fast'>('normal')
  const [theaterIndex, setTheaterIndex] = useState(0)

  const theaterCurrent = delibEntries[theaterIndex] ?? null

  useEffect(() => {
    if (!theaterPlaying) return
    if (delibEntries.length === 0) return
    if (theaterIndex >= delibEntries.length - 1) {
      setTheaterPlaying(false)
      return
    }
    const delayMs = theaterSpeed === 'slow' ? 2500 : theaterSpeed === 'fast' ? 800 : 1500
    const t = window.setTimeout(() => {
      setTheaterIndex((i) => Math.min(i + 1, delibEntries.length - 1))
    }, delayMs)
    return () => window.clearTimeout(t)
  }, [theaterPlaying, theaterSpeed, theaterIndex, delibEntries.length])

  function stopDeliberation(): void {
    delibWsRef.current?.close()
    delibWsRef.current = null
    setDelibIsRunning(false)
  }

  function startDeliberation(): void {
    setDelibError(null)

    const question = delibQuestion.trim()
    if (!question) {
      setDelibError('Question is required')
      return
    }

    stopDeliberation()
    setDelibIsRunning(true)
    setDelibEntries([])
    setCycleSummaries([])
    setFinalSummary(null)
    setDelibStreamingText('')
    setDelibStatus({ cycle: 1, phase: null, character: null })
    setTheaterPlaying(false)
    setTheaterIndex(0)

    const ws = openDeliberationStream({
      request: {
        question,
        rounds: delibRounds,
        summariser: delibSummariser,
        apiKey: apiKey.trim() ? apiKey.trim() : null,
      },
      onMessage: (msg) => {
        if (msg.type === 'phase_start') {
          setDelibStatus((prev) => ({
            ...prev,
            cycle: msg.cycle ?? prev.cycle,
            phase: isPhase(msg.phase) ? msg.phase : prev.phase,
          }))
          return
        }

        if (msg.type === 'character_start') {
          setDelibStatus((prev) => ({
            ...prev,
            cycle: msg.cycle ?? prev.cycle,
            phase: isPhase(msg.phase) ? msg.phase : prev.phase,
            character: msg.character ?? prev.character,
          }))
          setDelibStreamingText('')
          return
        }

        if (msg.type === 'chunk' && msg.content) {
          setDelibStreamingText((prev) => `${prev}${msg.content ?? ''}`)
          return
        }

        if (msg.type === 'character_done') {
          const phase = isPhase(msg.phase) ? msg.phase : null
          const cycle = msg.cycle ?? 1
          const character = msg.character ?? 'Unknown'
          const content = (msg.content ?? delibStreamingText).trim()
          if (phase && content) {
            setDelibEntries((prev) => [
              ...prev,
              {
                cycle,
                phase,
                character,
                content,
                timestamp: nowIso(),
              },
            ])
          }
          setDelibStreamingText('')
          return
        }

        if (msg.type === 'summary') {
          setCycleSummaries((prev) => [
            ...prev,
            { cycle: msg.cycle ?? prev.length + 1, summary: (msg.content ?? '').trim() },
          ])
          return
        }

        if (msg.type === 'done') {
          setFinalSummary({ by: msg.character ?? 'Moderator', content: (msg.content ?? '').trim() })
          setDelibIsRunning(false)
          delibWsRef.current?.close()
          delibWsRef.current = null
          return
        }

        if (msg.type === 'error') {
          setDelibError(msg.error ?? 'Deliberation error')
          setDelibIsRunning(false)
          delibWsRef.current?.close()
          delibWsRef.current = null
        }
      },
      onError: () => {
        setDelibError('WebSocket error')
        setDelibIsRunning(false)
      },
      onClose: () => {
        setDelibIsRunning(false)
      },
    })

    delibWsRef.current = ws
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">Cluas Huginn</div>
        <nav className="tabs">
          <button
            className={tab === 'chat' ? 'tab tabActive' : 'tab'}
            type="button"
            onClick={() => setTab('chat')}
          >
            Chat
          </button>
          <button
            className={tab === 'deliberation' ? 'tab tabActive' : 'tab'}
            type="button"
            onClick={() => setTab('deliberation')}
          >
            Deliberation
          </button>
        </nav>
        <div className="apikey">
          <input
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Optional API key"
            type="password"
            autoComplete="off"
          />
        </div>
      </header>

      {tab === 'chat' ? (
        <main className="panel">
          <div className="panelHeader">
            <div className="panelTitle">Council Chat</div>
            <div className="panelHint">Mention characters like @Corvus, or let everyone respond.</div>
          </div>

          <div className="chatHistory">
            {chatHistory.map((m, idx) => {
              const char = m.speaker ? characterByName.get(m.speaker) : undefined
              const label = m.role === 'user' ? 'You' : m.speaker ?? 'Assistant'
              const emoji = m.role === 'user' ? '🧑' : char?.emoji ?? m.emoji ?? '💬'
              return (
                <div key={`${idx}-${m.timestamp ?? ''}`} className={m.role === 'user' ? 'msg msgUser' : 'msg msgBot'}>
                  <div className="msgMeta">
                    <span className="msgEmoji">{emoji}</span>
                    <span className="msgSpeaker">{label}</span>
                  </div>
                  <div className="msgBody">{m.content}</div>
                </div>
              )
            })}

            {Object.entries(chatStreamingByCharacter).map(([speaker, content]) => {
              const char = characterByName.get(speaker)
              const emoji = char?.emoji ?? '💬'
              return (
                <div key={`stream-${speaker}`} className="msg msgBot msgStreaming">
                  <div className="msgMeta">
                    <span className="msgEmoji">{emoji}</span>
                    <span className="msgSpeaker">{speaker}</span>
                  </div>
                  <div className="msgBody">{content || '…'}</div>
                </div>
              )
            })}
          </div>

          {chatError ? <div className="error">{chatError}</div> : null}

          <div className="composer">
            <textarea
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Say something…"
              rows={3}
              disabled={chatIsBusy}
            />
            <div className="composerActions">
              <button type="button" onClick={() => setChatHistory([])} disabled={chatIsBusy}>
                Clear
              </button>
              <button type="button" onClick={sendChat} disabled={chatIsBusy || !chatInput.trim()}>
                Send
              </button>
            </div>
          </div>
        </main>
      ) : (
        <main className="panel">
          <div className="panelHeader">
            <div className="panelTitle">Deliberation + Theater Mode</div>
            <div className="panelHint">Stream a dialectic cycle and replay it as a performance.</div>
          </div>

          <div className="delibForm">
            <label className="field">
              <div className="fieldLabel">Question</div>
              <textarea
                value={delibQuestion}
                onChange={(e) => setDelibQuestion(e.target.value)}
                placeholder="What should the council deliberate on?"
                rows={3}
                disabled={delibIsRunning}
              />
            </label>

            <div className="fieldRow">
              <label className="field">
                <div className="fieldLabel">Rounds</div>
                <select
                  value={delibRounds}
                  onChange={(e) => setDelibRounds(Number(e.target.value) as 1 | 2 | 3)}
                  disabled={delibIsRunning}
                >
                  <option value={1}>1</option>
                  <option value={2}>2</option>
                  <option value={3}>3</option>
                </select>
              </label>

              <label className="field">
                <div className="fieldLabel">Summariser</div>
                <select
                  value={delibSummariser}
                  onChange={(e) => setDelibSummariser(e.target.value)}
                  disabled={delibIsRunning}
                >
                  <option value="Moderator">Moderator</option>
                  {characters.map((c) => (
                    <option key={c.name} value={c.name}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="delibActions">
              {delibIsRunning ? (
                <button type="button" onClick={stopDeliberation}>
                  Stop
                </button>
              ) : (
                <button type="button" onClick={startDeliberation}>
                  Start
                </button>
              )}
            </div>

            {delibError ? <div className="error">{delibError}</div> : null}
          </div>

          <div className="statusRow">
            <div className="statusItem">
              <span className="statusLabel">Cycle</span>
              <span className="statusValue">{delibStatus.cycle}</span>
            </div>
            <div className="statusItem">
              <span className="statusLabel">Phase</span>
              <span className="statusValue">{delibStatus.phase ?? '—'}</span>
            </div>
            <div className="statusItem">
              <span className="statusLabel">Character</span>
              <span className="statusValue">{delibStatus.character ?? '—'}</span>
            </div>
          </div>

          {delibStreamingText ? (
            <div className="liveCard">
              <div className="liveCardTitle">Live</div>
              <div className="liveCardBody">{delibStreamingText}</div>
            </div>
          ) : null}

          <div className="theater">
            <div className="theaterHeader">
              <div className="theaterTitle">Theater Mode</div>
              <div className="theaterControls">
                <button
                  type="button"
                  onClick={() => setTheaterPlaying((p) => !p)}
                  disabled={delibEntries.length === 0}
                >
                  {theaterPlaying ? 'Pause' : 'Play'}
                </button>
                <button
                  type="button"
                  onClick={() => setTheaterIndex((i) => Math.max(0, i - 1))}
                  disabled={delibEntries.length === 0 || theaterIndex === 0}
                >
                  Prev
                </button>
                <button
                  type="button"
                  onClick={() => setTheaterIndex((i) => Math.min(delibEntries.length - 1, i + 1))}
                  disabled={delibEntries.length === 0 || theaterIndex >= delibEntries.length - 1}
                >
                  Next
                </button>
                <select value={theaterSpeed} onChange={(e) => setTheaterSpeed(e.target.value as 'slow' | 'normal' | 'fast')}>
                  <option value="slow">Slow</option>
                  <option value="normal">Normal</option>
                  <option value="fast">Fast</option>
                </select>
              </div>
            </div>

            {theaterCurrent ? (
              <div className="theaterStage">
                <div className="stageMeta">
                  <span className="stageTag">Cycle {theaterCurrent.cycle}</span>
                  <span className="stageTag">{theaterCurrent.phase}</span>
                  <span className="stageTag">{theaterCurrent.character}</span>
                </div>
                <div className="stageBody">{theaterCurrent.content}</div>
              </div>
            ) : (
              <div className="theaterEmpty">Run a deliberation to populate the stage.</div>
            )}

            <div className="timeline">
              {delibEntries.map((e, idx) => (
                <button
                  key={`${e.cycle}-${e.phase}-${e.character}-${idx}`}
                  type="button"
                  className={idx === theaterIndex ? 'timelineItem timelineActive' : 'timelineItem'}
                  onClick={() => {
                    setTheaterPlaying(false)
                    setTheaterIndex(idx)
                  }}
                >
                  <span className="timelineMeta">
                    {e.cycle} · {e.phase} · {e.character}
                  </span>
                  <span className="timelinePreview">{e.content.slice(0, 120)}</span>
                </button>
              ))}
            </div>
          </div>

          {cycleSummaries.length > 0 ? (
            <div className="summaries">
              <div className="sectionTitle">Cycle Summaries</div>
              {cycleSummaries.map((s) => (
                <div key={`summary-${s.cycle}`} className="summaryCard">
                  <div className="summaryTitle">Cycle {s.cycle}</div>
                  <div className="summaryBody">{s.summary}</div>
                </div>
              ))}
            </div>
          ) : null}

          {finalSummary ? (
            <div className="final">
              <div className="sectionTitle">Final Summary</div>
              <div className="summaryCard">
                <div className="summaryTitle">{finalSummary.by}</div>
                <div className="summaryBody">{finalSummary.content}</div>
              </div>
            </div>
          ) : null}
        </main>
      )}
    </div>
  )
}

export default App
