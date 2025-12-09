"""todo:
    这里不应该是一个 MCP Tool Caller， 而是一个 MCP Server 的调用器。可以管理 Agent 连接的 Server 连接。
"""
import asyncio
from typing import Dict, Any

class McpManager:
    """MCP工具调用器"""
    
    async def call_emergency_service(self, event_details: Dict[str, Any]) -> bool:
        """调用紧急服务"""
        print(f"[MCP] Calling emergency service for: {event_details}")
        await asyncio.sleep(0.5)
        return True