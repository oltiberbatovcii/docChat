import { useEffect, useState } from 'react'
import { listDocuments } from './api/client'
import { ChatWindow } from './components/ChatWindow'
import { FileUpload } from './components/FileUpload'
import type { DocumentInfo } from './types'

// Only PDFs have pages; the backend splits other formats into sections at headings
function partName(filename: string): string {
  return filename.toLowerCase().endsWith('.pdf') ? 'pages' : 'sections'
}

function App() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [error, setError] = useState<string | null>(null)

  // Bumped after each upload; the effect below re-runs whenever it changes
  const [reloadCount, setReloadCount] = useState(0)

  useEffect(() => {
    listDocuments()
      .then((loaded) => {
        setDocuments(loaded)
        setError(null)
      })
      .catch((err: Error) => setError(err.message))
  }, [reloadCount])

  return (
    <div className="app">
      <aside className="sidebar">
        <h1>DocChat</h1>
        <FileUpload onUploaded={() => setReloadCount((count) => count + 1)} />
        <h2>Documents</h2>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {!error && documents.length === 0 && <p className="hint">Nothing uploaded yet.</p>}
        <ul className="documents">
          {documents.map((document) => (
            <li key={document.document_id}>
              <span className="filename">{document.filename}</span>
              <span className="hint">
                {document.pages} {partName(document.filename)} · {document.chunks} chunks
              </span>
            </li>
          ))}
        </ul>
      </aside>
      <ChatWindow />
    </div>
  )
}

export default App
