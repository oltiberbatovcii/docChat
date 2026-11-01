// Every call to the backend lives here, so components never deal with URLs or HTTP details.
import type { ChatResponse, DocumentInfo } from '../types'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, init)
  } catch {
    // fetch only rejects when no response arrived at all
    throw new Error('Cannot reach the server. Is the backend running?')
  }
  if (!response.ok) {
    throw new Error(await readErrorMessage(response))
  }
  return response.json() as Promise<T>
}

async function readErrorMessage(response: Response): Promise<string> {
  const fallback = `Request failed (${response.status})`
  try {
    const body: { detail?: unknown } = await response.json()
    // FastAPI sends a string for our own errors and a list for validation errors
    return typeof body.detail === 'string' ? body.detail : fallback
  } catch {
    return fallback
  }
}

export function listDocuments(): Promise<DocumentInfo[]> {
  return request('/documents')
}

export function uploadDocument(file: File): Promise<DocumentInfo> {
  const body = new FormData()
  body.append('file', file)
  return request('/documents', { method: 'POST', body })
}

export function sendChat(question: string): Promise<ChatResponse> {
  return request('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
}
