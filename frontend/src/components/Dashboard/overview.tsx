import { Card } from "@tremor/react"
import { AreaChart } from "@tremor/react"

const data = [
  {
    date: "Jan 22",
    Tasks: 167,
    "System Load": 45,
  },
  {
    date: "Feb 22",
    Tasks: 125,
    "System Load": 42,
  },
  // Add more data points
]

export function Overview() {
  return (
    <Card>
      <AreaChart
        className="h-72 mt-4"
        data={data}
        index="date"
        categories={["Tasks", "System Load"]}
        colors={["blue", "red"]}
        valueFormatter={(number: number) =>
          number.toString()
        }
      />
    </Card>
  )
}
