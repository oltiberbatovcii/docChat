import { useState } from 'react'
import type { ChangeEvent } from 'react'
import { uploadDocument } from '../api/client'

interface FileUploadProps {
  onUploaded: () => void
}

export function FileUpload({ onUploaded }: FileUploadProps) {
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleChange(event: ChangeEvent<HTMLInputElement>) {
    const input = event.target
    const file = input.files?.[0]
    if (!file) return

    setIsUploading(true)
    setError(null)
    try {
      await uploadDocument(file)
      onUploaded()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setIsUploading(false)
      input.value = '' // otherwise picking the same file again wouldn't fire a change event
    }
  }

  return (
    <div className="upload">
      <label className={`button ${isUploading ? 'is-disabled' : ''}`}>
        {isUploading ? 'Uploading…' : 'Upload PDF'}
        <input
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleChange}
          disabled={isUploading}
          hidden
        />
      </label>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
