from agents.agent_manager import AgentManager
from file_management.file_ops import FileOperations
from security.encryption import SecurityManager
from system.system_ops import SystemOperations


class JarvisAssistant:
    def __init__(self):
        self.agent_manager = AgentManager()
        self.file_ops = FileOperations()
        self.security = SecurityManager()
        self.system = SystemOperations()

    def initialize(self):
        """Initialize the assistant."""
        print("Initializing Jarvis Assistant...")
        system_info = self.system.get_system_info()
        print(f"Running on: {system_info['system']} {system_info['platform']}")

    def process_command(self, command: str):
        """Process user commands."""
        if command.startswith("file"):
            # Handle file operations
            return self.file_ops.list_directory()
        elif command.startswith("system"):
            # Handle system operations
            return self.system.get_system_info()
        elif command.startswith("security"):
            # Handle security operations
            pass
        else:
            # Delegate to agent manager
            self.agent_manager.delegate_task("general", {"command": command})


def main():
    assistant = JarvisAssistant()
    assistant.initialize()

    print("Jarvis Assistant is ready. Type 'exit' to quit.")
    while True:
        command = input(">> ")
        if command.lower() == "exit":
            break
        assistant.process_command(command)


if __name__ == "__main__":
    main()
