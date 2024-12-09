import { useEffect, useRef } from 'react'
import { useWebSocket } from '@/lib/websocket'
import { Card } from '@/components/ui/card'
import * as d3 from 'd3'

interface Agent {
  id: string
  name: string
  status: string
  connections: string[]
}

interface Link {
  source: string
  target: string
  value: number
}

export function AgentNetwork() {
  const svgRef = useRef<SVGSVGElement>(null)
  const websocket = useWebSocket()

  useEffect(() => {
    websocket.connect('interface-network', 'interfaces')
    return () => websocket.disconnect()
  }, [])

  useEffect(() => {
    if (!svgRef.current) return

    // Sample data - replace with real agent data from WebSocket
    const agents: Agent[] = [
      { id: 'admin', name: 'Admin Agent', status: 'active', connections: ['task', 'file'] },
      { id: 'task', name: 'Task Agent', status: 'active', connections: ['knowledge'] },
      { id: 'file', name: 'File Agent', status: 'active', connections: ['knowledge'] },
      { id: 'knowledge', name: 'Knowledge Agent', status: 'active', connections: [] }
    ]

    // Create links from connections
    const links: Link[] = []
    agents.forEach(agent => {
      agent.connections.forEach(target => {
        links.push({
          source: agent.id,
          target,
          value: 1
        })
      })
    })

    // Set up the network visualization
    const width = 600
    const height = 400

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)

    // Clear previous content
    svg.selectAll('*').remove()

    // Create the simulation
    const simulation = d3.forceSimulation(agents as any)
      .force('link', d3.forceLink(links).id((d: any) => d.id))
      .force('charge', d3.forceManyBody().strength(-100))
      .force('center', d3.forceCenter(width / 2, height / 2))

    // Draw links
    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 2)

    // Draw nodes
    const node = svg.append('g')
      .selectAll('g')
      .data(agents)
      .join('g')

    // Add circles for nodes
    node.append('circle')
      .attr('r', 20)
      .attr('fill', d => d.status === 'active' ? '#4CAF50' : '#9E9E9E')

    // Add labels
    node.append('text')
      .text(d => d.name.split(' ')[0])
      .attr('x', 0)
      .attr('y', 30)
      .attr('text-anchor', 'middle')
      .attr('fill', 'currentColor')
      .style('font-size', '12px')

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y)

      node
        .attr('transform', (d: any) => `translate(${d.x},${d.y})`)
    })

    // Add drag behavior
    node.call(d3.drag()
      .on('start', (event: any) => {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        event.subject.fx = event.subject.x
        event.subject.fy = event.subject.y
      })
      .on('drag', (event: any) => {
        event.subject.fx = event.x
        event.subject.fy = event.y
      })
      .on('end', (event: any) => {
        if (!event.active) simulation.alphaTarget(0)
        event.subject.fx = null
        event.subject.fy = null
      }) as any)

  }, [websocket.messages])

  return (
    <Card className="p-4">
      <h3 className="text-lg font-semibold mb-4">Agent Network</h3>
      <svg ref={svgRef} className="w-full h-[400px]" />
    </Card>
  )
}
