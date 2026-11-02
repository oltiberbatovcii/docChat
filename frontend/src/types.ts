// Mirrors the backend's Pydantic response models.

export interface DocumentInfo {
  document_id: string
  filename: string
  pages: number
  chunks: number
}

export interface Source {
  filename: string
  page: number
  location: string // e.g. "p.3" for a PDF or "section 3" for Word
  snippet: string
}

export interface ChatResponse {
  answer: string
  sources: Source[]
}

export interface Message {
  role: 'user' | 'assistant'
  text: string
  sources?: Source[]
}
