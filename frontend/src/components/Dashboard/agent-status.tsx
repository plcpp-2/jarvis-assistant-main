import { Card, DonutChart, Legend, Title } from "@tremor/react"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const agents = [
  {
    name: "Admin Agent",
    status: "active",
    tasks: 5,
    load: 32,
  },
  {
    name: "Task Agent",
    status: "active",
    tasks: 8,
    load: 45,
  },
  {
    name: "Knowledge Agent",
    status: "hibernating",
    tasks: 0,
    load: 0,
  },
  {
    name: "File Agent",
    status: "active",
    tasks: 3,
    load: 28,
  },
]

const data = [
  {
    name: "Active",
    value: 3,
  },
  {
    name: "Hibernating",
    value: 1,
  },
  {
    name: "Error",
    value: 0,
  },
]

export function AgentStatus() {
  return (
    <div className="space-y-6">
      <Card>
        <Title>Agent Distribution</Title>
        <div className="mt-4">
          <DonutChart
            className="h-40"
            data={data}
            category="value"
            index="name"
            colors={["green", "yellow", "red"]}
          />
        </div>
        <Legend
          className="mt-3"
          categories={["Active", "Hibernating", "Error"]}
          colors={["green", "yellow", "red"]}
        />
      </Card>
      <Card>
        <Title>Agent Details</Title>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Agent</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Tasks</TableHead>
              <TableHead>Load</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {agents.map((agent) => (
              <TableRow key={agent.name}>
                <TableCell>{agent.name}</TableCell>
                <TableCell>
                  <Badge
                    variant={
                      agent.status === "active"
                        ? "default"
                        : agent.status === "hibernating"
                        ? "secondary"
                        : "destructive"
                    }
                  >
                    {agent.status}
                  </Badge>
                </TableCell>
                <TableCell>{agent.tasks}</TableCell>
                <TableCell>{agent.load}%</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  )
}
