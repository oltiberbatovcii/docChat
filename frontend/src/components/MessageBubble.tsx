import type { Message } from '../types'
import { SourceList } from './SourceList'

interface MessageBubbleProps {
  message: Message
}

export function MessageBubble({ message }: MessageBubbleProps) {
  return (
    <div className={`bubble bubble-${message.role}`}>
      <p>{message.text}</p>
      {message.sources && message.sources.length > 0 && <SourceList sources={message.sources} />}
    </div>
  )
}
