import { Metadata } from "next"
import { TaskCreator } from "@/components/task-execution/task-creator"
import { TaskMonitor } from "@/components/task-execution/task-monitor"

export const metadata: Metadata = {
  title: "Task Execution",
  description: "Create and monitor tasks",
}

export default function TasksPage() {
  return (
    <div className="flex-1 space-y-4 p-4">
      <h2 className="text-3xl font-bold tracking-tight">Task Execution</h2>

      <div className="grid gap-4 md:grid-cols-2">
        <TaskCreator />
        <TaskMonitor />
      </div>
    </div>
  )
}
