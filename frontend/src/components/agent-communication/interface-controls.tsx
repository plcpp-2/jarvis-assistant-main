import { useState } from 'react'
import { useWebSocket } from '@/lib/websocket'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'

export function InterfaceControls() {
  const [selectedAgent, setSelectedAgent] = useState('')
  const [command, setCommand] = useState('')
  const websocket = useWebSocket()

  const sendCommand = () => {
    if (!selectedAgent || !command) return

    websocket.sendMessage({
      sender: 'interface',
      message_type: 'interface_action',
      content: {
        command,
        target: selectedAgent,
        timestamp: new Date().toISOString()
      }
    })

    setCommand('')
  }

  const handleEmergencyStop = () => {
    websocket.sendMessage({
      sender: 'interface',
      message_type: 'interface_action',
      content: {
        command: 'EMERGENCY_STOP',
        target: 'all',
        timestamp: new Date().toISOString()
      }
    })
  }

  return (
    <Card className="p-4 space-y-4">
      <h3 className="text-lg font-semibold">Interface Controls</h3>
      
      <div className="space-y-2">
        <Label>Target Agent</Label>
        <Select onValueChange={setSelectedAgent} value={selectedAgent}>
          <SelectTrigger>
            <SelectValue placeholder="Select agent" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="admin">Admin Agent</SelectItem>
            <SelectItem value="task">Task Agent</SelectItem>
            <SelectItem value="file">File Agent</SelectItem>
            <SelectItem value="knowledge">Knowledge Agent</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Command</Label>
        <Input
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          placeholder="Enter command..."
        />
      </div>

      <div className="flex space-x-2">
        <Button onClick={sendCommand} disabled={!selectedAgent || !command}>
          Send Command
        </Button>

        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button variant="destructive">Emergency Stop</Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Emergency Stop</AlertDialogTitle>
              <AlertDialogDescription>
                This will immediately stop all agent operations. Are you sure?
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={handleEmergencyStop}>
                Stop All Agents
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>

      <div className="space-y-2">
        <h4 className="font-medium">Quick Actions</h4>
        <div className="grid grid-cols-2 gap-2">
          <Button
            variant="outline"
            onClick={() => {
              websocket.sendMessage({
                sender: 'interface',
                message_type: 'interface_action',
                content: {
                  command: 'PAUSE_ALL',
                  target: 'all',
                  timestamp: new Date().toISOString()
                }
              })
            }}
          >
            Pause All
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              websocket.sendMessage({
                sender: 'interface',
                message_type: 'interface_action',
                content: {
                  command: 'RESUME_ALL',
                  target: 'all',
                  timestamp: new Date().toISOString()
                }
              })
            }}
          >
            Resume All
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              websocket.sendMessage({
                sender: 'interface',
                message_type: 'interface_action',
                content: {
                  command: 'STATUS_CHECK',
                  target: 'all',
                  timestamp: new Date().toISOString()
                }
              })
            }}
          >
            Status Check
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              websocket.sendMessage({
                sender: 'interface',
                message_type: 'interface_action',
                content: {
                  command: 'SYNC_ALL',
                  target: 'all',
                  timestamp: new Date().toISOString()
                }
              })
            }}
          >
            Sync All
          </Button>
        </div>
      </div>
    </Card>
  )
}
