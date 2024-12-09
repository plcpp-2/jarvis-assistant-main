import { Metadata } from "next"
import { AgentChat } from "@/components/agent-communication/agent-chat"
import { AgentNetwork } from "@/components/agent-communication/agent-network"
import { InterfaceControls } from "@/components/agent-communication/interface-controls"

export const metadata: Metadata = {
  title: "Agent Communication",
  description: "Monitor and control agent communication",
}

export default function CommunicationPage() {
  return (
    <div className="flex-1 space-y-4 p-4">
      <h2 className="text-3xl font-bold tracking-tight">Agent Communication</h2>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <AgentChat />
        </div>
        <div>
          <InterfaceControls />
        </div>
      </div>

      <div className="mt-4">
        <AgentNetwork />
      </div>
    </div>
  )
}
