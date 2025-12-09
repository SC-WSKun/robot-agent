# core/action/alert_action.py
"""AlertAction - 应急调用 Action

负责处理紧急情况，调用应急服务
"""

import time
from typing import Dict, Any
from core.action.base import BaseAction, ActionContext, ActionResult, ActionMetadata
from core.mcp_manager import McpManager


class AlertAction(BaseAction):
    """应急调用 Action
    
    检测到紧急情况时调用应急服务
    """
    
    def __init__(self):
        """初始化 AlertAction"""
        super().__init__()
        self.mcp_manager: McpManager = None
    
    def get_metadata(self) -> ActionMetadata:
        """获取 Action 元信息"""
        return ActionMetadata(
            name="alert",
            version="1.0.0",
            description="应急调用 Action，用于处理紧急情况",
            dependencies=["mcp_manager"],
            capabilities=["emergency_call", "alert_service"],
            author="Robot Agent Team"
        )
    
    def initialize(self, config_dict: Dict[str, Any]) -> None:
        """初始化 AlertAction
        
        Args:
            config_dict: 配置参数
        """
        try:
            print("[AlertAction] Initializing...")
            
            # 初始化 MCP Manager
            self.mcp_manager = McpManager()
            
            self._initialized = True
            print("[AlertAction] Initialization complete")
            
        except Exception as e:
            print(f"[AlertAction] Initialization failed: {e}")
            raise
    
    async def execute(self, context: ActionContext) -> ActionResult:
        """执行应急调用
        
        Args:
            context: Action 执行上下文
                - input_data: 紧急事件详情
                - shared_data.last_vision_result: 视觉分析结果
                
        Returns:
            ActionResult: 包含调用结果的 ActionResult
        """
        start_time = time.time()
        
        try:
            print("[AlertAction] Executing...")
            
            if not self._initialized:
                raise RuntimeError("AlertAction not initialized")
            
            # 获取紧急事件详情
            event_details = context.input_data
            if not event_details:
                # 从共享数据中获取
                vision_result = context.shared_data.get("last_vision_result", {})
                event_details = {
                    "type": "vision_emergency",
                    "description": vision_result.get("description", "未知紧急情况"),
                    "confidence": vision_result.get("confidence", 0.0),
                    "objects_detected": vision_result.get("objects_detected", [])
                }
            
            print(f"[AlertAction] Calling emergency service for: {event_details}")
            
            # 调用应急服务
            success = await self.mcp_manager.call_emergency_service(event_details)
            
            elapsed_time = time.time() - start_time
            print(f"[AlertAction] Execution complete in {elapsed_time:.2f}s, success={success}")
            
            return ActionResult(
                success=success,
                output={
                    "service_called": success,
                    "event_details": event_details
                },
                metadata={
                    "elapsed_time": elapsed_time,
                    "emergency_type": event_details.get("type", "unknown")
                }
            )
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"[AlertAction] Execution failed: {e}")
            return ActionResult(
                success=False,
                error=e,
                metadata={"elapsed_time": elapsed_time}
            )
    
    def cleanup(self) -> None:
        """清理资源"""
        print("[AlertAction] Cleaning up...")
        
        self.mcp_manager = None
        self._initialized = False
        print("[AlertAction] Cleanup complete")
