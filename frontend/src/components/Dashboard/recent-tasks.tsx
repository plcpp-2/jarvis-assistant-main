import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { PlayCircle, PauseCircle, XCircle } from "lucide-react"

const tasks = [
  {
    id: "TASK-1234",
    title: "Analyze system performance",
    status: "running",
    priority: "high",
    progress: 45,
  },
  {
    id: "TASK-1235",
    title: "Update knowledge base",
    status: "pending",
    priority: "medium",
    progress: 0,
  },
  {
    id: "TASK-1236",
    title: "Backup system files",
    status: "completed",
    priority: "low",
    progress: 100,
  },
  {
    id: "TASK-1237",
    title: "Monitor network traffic",
    status: "running",
    priority: "medium",
    progress: 72,
  },
]

export function RecentTasks() {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Task</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Priority</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {tasks.map((task) => (
          <TableRow key={task.id}>
            <TableCell className="font-medium">
              <div>
                <div className="font-bold">{task.title}</div>
                <div className="text-sm text-muted-foreground">
                  {task.id}
                </div>
              </div>
            </TableCell>
            <TableCell>
              <Badge
                variant={
                  task.status === "running"
                    ? "default"
                    : task.status === "completed"
                    ? "success"
                    : "secondary"
                }
              >
                {task.status}
              </Badge>
            </TableCell>
            <TableCell>
              <Badge
                variant={
                  task.priority === "high"
                    ? "destructive"
                    : task.priority === "medium"
                    ? "warning"
                    : "secondary"
                }
              >
                {task.priority}
              </Badge>
            </TableCell>
            <TableCell className="text-right">
              <div className="flex justify-end space-x-2">
                {task.status === "running" ? (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                  >
                    <PauseCircle className="h-4 w-4" />
                  </Button>
                ) : task.status === "pending" ? (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                  >
                    <PlayCircle className="h-4 w-4" />
                  </Button>
                ) : null}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                >
                  <XCircle className="h-4 w-4" />
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
