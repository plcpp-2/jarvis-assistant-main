import { useEffect, useState } from 'react'
import { useWebSocket } from '@/lib/websocket'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { PlayCircle, PauseCircle, StopCircle, RefreshCw } from 'lucide-react'

interface Task {
  id: string
  type: string
  status: string
  priority: number
  progress: number
  result?: any
  error?: string
  created_at: string
  updated_at: string
}

export function TaskMonitor() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const websocket = useWebSocket()

  useEffect(() => {
    // Update tasks when new messages arrive
    const latestMessage = websocket.messages[websocket.messages.length - 1]
    if (latestMessage?.message_type === 'task_status') {
      updateTaskStatus(latestMessage.content)
    }
  }, [websocket.messages])

  const updateTaskStatus = (update: any) => {
    setTasks(prev => {
      const index = prev.findIndex(task => task.id === update.task_id)
      if (index === -1) {
        // New task
        return [...prev, {
          id: update.task_id,
          type: update.type,
          status: update.status,
          priority: update.priority || 5,
          progress: calculateProgress(update.status),
          result: update.result,
          error: update.error,
          created_at: update.timestamp,
          updated_at: update.timestamp,
        }]
      } else {
        // Update existing task
        const newTasks = [...prev]
        newTasks[index] = {
          ...newTasks[index],
          status: update.status,
          progress: calculateProgress(update.status),
          result: update.result,
          error: update.error,
          updated_at: update.timestamp,
        }
        return newTasks
      }
    })
  }

  const calculateProgress = (status: string): number => {
    switch (status) {
      case 'pending': return 0
      case 'started': return 25
      case 'running': return 50
      case 'completed': return 100
      case 'failed': return 100
      default: return 0
    }
  }

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed': return 'success'
      case 'failed': return 'destructive'
      case 'running': return 'default'
      case 'pending': return 'secondary'
      default: return 'default'
    }
  }

  const handleTaskAction = (taskId: string, action: string) => {
    websocket.sendMessage({
      sender: 'interface',
      message_type: 'task_control',
      content: {
        task_id: taskId,
        action,
      },
    })
  }

  return (
    <div className="space-y-4">
      <Card className="p-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Active Tasks</h3>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              websocket.sendMessage({
                sender: 'interface',
                message_type: 'task_list_request',
              })
            }}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Progress</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tasks.map((task) => (
              <TableRow
                key={task.id}
                className="cursor-pointer"
                onClick={() => setSelectedTask(task)}
              >
                <TableCell className="font-mono">{task.id}</TableCell>
                <TableCell>{task.type}</TableCell>
                <TableCell>
                  <Badge variant={getStatusColor(task.status) as any}>
                    {task.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Progress value={task.progress} className="w-[100px]" />
                </TableCell>
                <TableCell>
                  <div className="flex space-x-2">
                    <TooltipProvider>
                      {task.status === 'running' ? (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleTaskAction(task.id, 'pause')
                              }}
                            >
                              <PauseCircle className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>Pause Task</TooltipContent>
                        </Tooltip>
                      ) : task.status === 'pending' || task.status === 'paused' ? (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleTaskAction(task.id, 'resume')
                              }}
                            >
                              <PlayCircle className="h-4 w-4" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>Resume Task</TooltipContent>
                        </Tooltip>
                      ) : null}

                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleTaskAction(task.id, 'cancel')
                            }}
                          >
                            <StopCircle className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Cancel Task</TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {selectedTask && (
        <Card className="p-4">
          <h4 className="text-lg font-semibold mb-4">Task Details</h4>
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <div className="font-semibold">ID:</div>
              <div className="font-mono">{selectedTask.id}</div>
              
              <div className="font-semibold">Type:</div>
              <div>{selectedTask.type}</div>
              
              <div className="font-semibold">Status:</div>
              <div>
                <Badge variant={getStatusColor(selectedTask.status) as any}>
                  {selectedTask.status}
                </Badge>
              </div>
              
              <div className="font-semibold">Created:</div>
              <div>{new Date(selectedTask.created_at).toLocaleString()}</div>
              
              <div className="font-semibold">Updated:</div>
              <div>{new Date(selectedTask.updated_at).toLocaleString()}</div>
            </div>

            {selectedTask.result && (
              <div className="mt-4">
                <div className="font-semibold mb-2">Result:</div>
                <pre className="bg-muted p-2 rounded-md overflow-auto">
                  {JSON.stringify(selectedTask.result, null, 2)}
                </pre>
              </div>
            )}

            {selectedTask.error && (
              <div className="mt-4">
                <div className="font-semibold mb-2 text-destructive">Error:</div>
                <pre className="bg-destructive/10 p-2 rounded-md overflow-auto text-destructive">
                  {selectedTask.error}
                </pre>
              </div>
            )}
          </div>
        </Card>
      )}
    </div>
  )
}
