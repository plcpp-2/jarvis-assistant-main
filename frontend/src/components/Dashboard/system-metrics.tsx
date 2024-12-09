import { Card, AreaChart, Title, Text } from "@tremor/react"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"

const metrics = [
  {
    name: "CPU Usage",
    value: 45,
    change: "+2%",
    status: "normal",
  },
  {
    name: "Memory Usage",
    value: 62,
    change: "-5%",
    status: "normal",
  },
  {
    name: "Disk Usage",
    value: 78,
    change: "+8%",
    status: "warning",
  },
  {
    name: "Network Load",
    value: 34,
    change: "+12%",
    status: "normal",
  },
]

const data = [
  {
    time: "00:00",
    CPU: 35,
    Memory: 55,
    Disk: 70,
    Network: 25,
  },
  // Add more data points
]

export function SystemMetrics() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2">
        {metrics.map((metric) => (
          <Card key={metric.name} className="p-4">
            <div className="flex justify-between items-center">
              <Text>{metric.name}</Text>
              <Badge
                variant={
                  metric.status === "warning" ? "destructive" : "secondary"
                }
              >
                {metric.change}
              </Badge>
            </div>
            <div className="mt-4">
              <Progress value={metric.value} className="h-2" />
              <div className="flex justify-between mt-1">
                <Text className="text-sm text-muted-foreground">
                  {metric.value}%
                </Text>
                <Text className="text-sm text-muted-foreground">100%</Text>
              </div>
            </div>
          </Card>
        ))}
      </div>
      <Card>
        <Title>System Metrics Over Time</Title>
        <AreaChart
          className="h-72 mt-4"
          data={data}
          index="time"
          categories={["CPU", "Memory", "Disk", "Network"]}
          colors={["blue", "green", "red", "purple"]}
          valueFormatter={(number: number) =>
            number.toString() + "%"
          }
        />
      </Card>
    </div>
  )
}
