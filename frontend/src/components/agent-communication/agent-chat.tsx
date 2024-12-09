import { useState, useEffect } from 'react'
import { useWebSocket } from '@/lib/websocket'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

interface Message {
  id: string
  sender: string
  content: string
  timestamp: string
}

export function AgentChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const websocket = useWebSocket()

  useEffect(() => {
    // Connect to WebSocket when component mounts
    websocket.connect('interface-chat', 'interfaces')

    return () => {
      websocket.disconnect()
    }
  }, [])

  useEffect(() => {
    // Update messages when new ones arrive
    const latestMessage = websocket.messages[websocket.messages.length - 1]
    if (latestMessage?.message_type === 'direct_message') {
      setMessages(prev => [...prev, {
        id: Math.random().toString(),
        sender: latestMessage.sender,
        content: latestMessage.content.text,
        timestamp: new Date().toISOString()
      }])
    }
  }, [websocket.messages])

  const sendMessage = () => {
    if (!input.trim()) return

    const message = {
      sender: 'interface',
      message_type: 'direct_message',
      content: {
        text: input,
        timestamp: new Date().toISOString()
      },
      target: 'agents'
    }

    websocket.sendMessage(message)
    setInput('')
  }

  return (
    <Card className="flex flex-col h-[600px] p-4">
      <div className="flex-1 mb-4">
        <ScrollArea className="h-[500px]">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex items-start space-x-2 mb-4 ${
                message.sender === 'interface' ? 'flex-row-reverse' : ''
              }`}
            >
              <Avatar className="h-8 w-8">
                <AvatarImage
                  src={`/agents/${message.sender}.png`}
                  alt={message.sender}
                />
                <AvatarFallback>
                  {message.sender[0].toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div
                className={`flex flex-col ${
                  message.sender === 'interface'
                    ? 'items-end'
                    : 'items-start'
                }`}
              >
                <div
                  className={`rounded-lg px-3 py-2 ${
                    message.sender === 'interface'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  }`}
                >
                  {message.content}
                </div>
                <span className="text-xs text-muted-foreground mt-1">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))}
        </ScrollArea>
      </div>
      <div className="flex space-x-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
        />
        <Button onClick={sendMessage}>Send</Button>
      </div>
    </Card>
  )
}
