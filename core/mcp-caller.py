class MCPToolCaller:
    """MCP工具调用器"""
    
    async def analyze_image(self, image_data: bytes) -> Dict[str, Any]:
        """调用大模型分析图像"""
        print("[MCP] Analyzing image with AI model...")
        # 模拟AI分析延迟
        await asyncio.sleep(1.0)
        
        # 模拟分析结果 - 正常情况
        return {
            "action": "continue_patrol",
            "objects_detected": ["person", "chair", "table"],
            "emergency": False,
            "confidence": 0.95
        }
    
    async def call_emergency_service(self, event_details: Dict[str, Any]) -> bool:
        """调用紧急服务"""
        print(f"[MCP] Calling emergency service for: {event_details}")
        await asyncio.sleep(0.5)
        return True