import asyncio
from core.agent import RobotAgent
from core.action import WatchAction, SpeakAction, AlertAction

async def main():
    """主程序入口（使用 Action 机制）"""
    print("[Main] Initializing Robot Agent...")
    
    # 创建 Agent
    agent = RobotAgent(patrol_interval=30.0)
    
    # 注册 Actions
    print("[Main] Registering actions...")
    agent.register_action("watch", WatchAction())
    agent.register_action("speak", SpeakAction())
    agent.register_action("alert", AlertAction())
    
    print("[Main] Actions registered:")
    for name, metadata in agent.action_metadata.items():
        print(f"  - {name}: {metadata.description}")
    
    # 启动 Agent
    print("[Main] Starting agent...")
    agent.start()
    
    try:
        # 保持运行
        print("[Main] Agent is running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        print("\n[Main] Shutting down...")
    finally:
        agent.stop()
        print("[Main] Agent stopped.")

if __name__ == "__main__":
    asyncio.run(main())
