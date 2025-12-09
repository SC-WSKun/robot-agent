# core/action/watch_action.py
"""WatchAction - 图像理解 Action

负责巡检期间的环境理解
"""

import time
from typing import Dict, Any
from core.action.base import BaseAction, ActionContext, ActionResult, ActionMetadata
from core.camera import CameraSensor
from core.client.openai_client import OpenAIClient
import config


class WatchAction(BaseAction):
    """图像理解 Action
    
    从摄像头捕获图像并调用视觉模型进行分析
    """
    
    DEFAULT_PROMPT = """分析这张巡检图像，识别以下内容：
1. 场景中的物体和人员
2. 是否存在异常情况（火灾、烟雾、未授权人员等）
3. 环境状态评估

以 JSON 格式返回结果，包含字段：
- objects_detected: 检测到的物体列表（数组）
- emergency: 是否存在紧急情况（布尔值）
- confidence: 分析置信度（0-1之间的浮点数）
- description: 场景描述文本（字符串）
"""
    
    def __init__(self):
        """初始化 WatchAction"""
        super().__init__()
        self.camera: CameraSensor = None
        self.openai_client: OpenAIClient = None
        self.model_name = config.QWEN_VL_MODEL
        self.prompt_template = self.DEFAULT_PROMPT
        self.max_tokens = 500
        self.temperature = 0.7
    
    def get_metadata(self) -> ActionMetadata:
        """获取 Action 元信息"""
        return ActionMetadata(
            name="watch",
            version="1.0.0",
            description="图像理解 Action，用于巡检期间的环境分析",
            dependencies=["camera", "openai_api"],
            capabilities=["vision", "object_detection", "emergency_detection"],
            author="Robot Agent Team"
        )
    
    def initialize(self, config_dict: Dict[str, Any]) -> None:
        """初始化 WatchAction
        
        Args:
            config_dict: 配置参数
                - api_key: OpenAI API 密钥
                - base_url: API 端点 URL
                - model_name: 使用的视觉模型
                - prompt_template: 提示词模板
                - max_tokens: 最大生成 token 数
                - temperature: 生成温度
        """
        try:
            print("[WatchAction] Initializing...")
            
            # 初始化摄像头
            self.camera = CameraSensor()
            
            # 初始化 OpenAI 客户端
            api_key = config_dict.get("api_key") or config.OPENAI_API_KEY
            base_url = config_dict.get("base_url") or config.OPENAI_BASE_URL
            
            if not api_key:
                print("[WatchAction] Warning: No API key provided, using mock mode")
                self.openai_client = None
            else:
                self.openai_client = OpenAIClient(api_key=api_key, base_url=base_url)
            
            # 更新配置参数
            self.model_name = config_dict.get("model_name", self.model_name)
            self.prompt_template = config_dict.get("prompt_template", self.prompt_template)
            self.max_tokens = config_dict.get("max_tokens", self.max_tokens)
            self.temperature = config_dict.get("temperature", self.temperature)
            
            self._initialized = True
            print("[WatchAction] Initialization complete")
            
        except Exception as e:
            print(f"[WatchAction] Initialization failed: {e}")
            raise
    
    async def execute(self, context: ActionContext) -> ActionResult:
        """执行图像理解
        
        Args:
            context: Action 执行上下文
            
        Returns:
            ActionResult: 包含分析结果的 ActionResult
        """
        start_time = time.time()
        
        try:
            print("[WatchAction] Executing...")
            
            if not self._initialized:
                raise RuntimeError("WatchAction not initialized")
            
            # 1. 捕获图像
            image_bytes = await self.camera.capture_image()
            if image_bytes is None:
                return ActionResult(
                    success=False,
                    error=Exception("Failed to capture image"),
                    metadata={"elapsed_time": time.time() - start_time}
                )
            
            # 2. 调用视觉模型分析
            if self.openai_client is None:
                # Mock 模式：返回模拟数据
                print("[WatchAction] Using mock mode (no API key)")
                analysis_result = {
                    "objects_detected": ["person", "chair", "table"],
                    "emergency": False,
                    "confidence": 0.95,
                    "description": "正常办公环境，未发现异常情况"
                }
            else:
                # 获取自定义提示词（如果有）
                prompt = context.config.get("prompt", self.prompt_template)
                
                # 调用 OpenAI API
                analysis_result = await self.openai_client.vision_completion(
                    model=self.model_name,
                    image=image_bytes,
                    prompt=prompt,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
            
            # 3. 确保结果包含必要字段
            if "objects_detected" not in analysis_result:
                analysis_result["objects_detected"] = []
            if "emergency" not in analysis_result:
                analysis_result["emergency"] = False
            if "confidence" not in analysis_result:
                analysis_result["confidence"] = 0.0
            if "description" not in analysis_result:
                analysis_result["description"] = "无描述"
            
            # 4. 更新共享数据
            context.shared_data["last_vision_result"] = analysis_result
            
            elapsed_time = time.time() - start_time
            print(f"[WatchAction] Execution complete in {elapsed_time:.2f}s")
            print(f"[WatchAction] Result: emergency={analysis_result['emergency']}, "
                  f"objects={len(analysis_result['objects_detected'])}")
            
            return ActionResult(
                success=True,
                output=analysis_result,
                metadata={
                    "elapsed_time": elapsed_time,
                    "image_size": len(image_bytes),
                    "model": self.model_name
                },
                next_actions=[]  # 由决策模型决定后续 Action
            )
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"[WatchAction] Execution failed: {e}")
            return ActionResult(
                success=False,
                error=e,
                metadata={"elapsed_time": elapsed_time}
            )
    
    def cleanup(self) -> None:
        """清理资源"""
        print("[WatchAction] Cleaning up...")
        
        if self.camera:
            # CameraSensor 的清理由其 __del__ 方法处理
            self.camera = None
        
        if self.openai_client:
            self.openai_client.close()
            self.openai_client = None
        
        self._initialized = False
        print("[WatchAction] Cleanup complete")
