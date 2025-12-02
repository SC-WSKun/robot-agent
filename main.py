from core.agent import RobotAgent, AgentMode

async def main():
    agent = RobotAgent(wake_interval=30)

asyncio.run(main())
