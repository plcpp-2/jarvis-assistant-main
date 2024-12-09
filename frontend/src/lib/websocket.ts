import { create } from 'zustand'

type WebSocketState = {
  socket: WebSocket | null
  connected: boolean
  messages: any[]
  connect: (clientId: string, clientType: string) => void
  disconnect: () => void
  sendMessage: (message: any) => void
}

export const useWebSocket = create<WebSocketState>((set, get) => ({
  socket: null,
  connected: false,
  messages: [],
  
  connect: (clientId: string, clientType: string) => {
    const socket = new WebSocket(`ws://localhost:8000/ws/${clientId}/${clientType}`)
    
    socket.onopen = () => {
      set({ connected: true })
      console.log('WebSocket connected')
    }
    
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data)
      set((state) => ({ messages: [...state.messages, message] }))
      
      // Handle different message types
      switch (message.message_type) {
        case 'agent_status':
          // Update agent status in UI
          break
        case 'task_update':
          // Update task status
          break
        case 'interface_action':
          // Handle interface updates
          break
      }
    }
    
    socket.onclose = () => {
      set({ connected: false })
      console.log('WebSocket disconnected')
    }
    
    set({ socket })
  },
  
  disconnect: () => {
    const { socket } = get()
    if (socket) {
      socket.close()
      set({ socket: null, connected: false })
    }
  },
  
  sendMessage: (message: any) => {
    const { socket } = get()
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message))
    }
  },
}))

// Utility functions for common message types
export const sendAgentStatus = (status: any) => {
  useWebSocket.getState().sendMessage({
    sender: 'interface',
    message_type: 'agent_status',
    content: status
  })
}

export const sendTaskUpdate = (update: any) => {
  useWebSocket.getState().sendMessage({
    sender: 'interface',
    message_type: 'task_update',
    content: update
  })
}

export const sendInterfaceAction = (action: any) => {
  useWebSocket.getState().sendMessage({
    sender: 'interface',
    message_type: 'interface_action',
    content: action
  })
}
