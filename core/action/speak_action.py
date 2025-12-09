# core/action/speak_action.py
"""SpeakAction - 语音合成 Action

负责将文本转换为语音输出
"""

import time
from typing import Dict, Any
from core.action.base import BaseAction, ActionContext, ActionResult, ActionMetadata
from core.client.openai_client import OpenAIClient
import config


class SpeakAction(BaseAction):
    """语音合成 Action
    
    将文本转换为语音并播放
    """
    
    def __init__(self):
        """初始化 SpeakAction"""
        super().__init__()
        self.openai_client: OpenAIClient = None
        self.model_name = config.QWEN_OMNI_MODEL
        self.voice = "default"
        self.speed = 1.0
        self.auto_play = True
    
    def get_metadata(self) -> ActionMetadata:
        """获取 Action 元信息"""
        return ActionMetadata(
            name="speak",
            version="1.0.0",
            description="语音合成 Action，用于将文本转换为语音",
            dependencies=["openai_api", "audio_device"],
            capabilities=["tts", "audio_playback"],
            author="Robot Agent Team"
        )
    
    def initialize(self, config_dict: Dict[str, Any]) -> None:
        """初始化 SpeakAction
        
        Args:
            config_dict: 配置参数
                - api_key: OpenAI API 密钥
                - base_url: API 端点 URL
                - model_name: 使用的语音模型
                - voice: 音色类型
                - speed: 语速倍率
                - auto_play: 是否自动播放
        """
        try:
            print("[SpeakAction] Initializing...")
            
            # 初始化 OpenAI 客户端
            api_key = config_dict.get("api_key") or config.OPENAI_API_KEY
            base_url = config_dict.get("base_url") or config.OPENAI_BASE_URL
            
            if not api_key:
                print("[SpeakAction] Warning: No API key provided, using mock mode")
                self.openai_client = None
            else:
                self.openai_client = OpenAIClient(api_key=api_key, base_url=base_url)
            
            # 更新配置参数
            self.model_name = config_dict.get("model_name", self.model_name)
            self.voice = config_dict.get("voice", self.voice)
            self.speed = config_dict.get("speed", self.speed)
            self.auto_play = config_dict.get("auto_play", self.auto_play)
            
            self._initialized = True
            print("[SpeakAction] Initialization complete")
            
        except Exception as e:
            print(f"[SpeakAction] Initialization failed: {e}")
            raise
    
    async def execute(self, context: ActionContext) -> ActionResult:
        """执行语音合成
        
        Args:
            context: Action 执行上下文
                - input_data: 要转换为语音的文本
                - config.voice: 音色选择（可选）
                
        Returns:
            ActionResult: 包含音频数据的 ActionResult
        """
        start_time = time.time()
        
        try:
            print("[SpeakAction] Executing...")
            
            if not self._initialized:
                raise RuntimeError("SpeakAction not initialized")
            
            # 获取要转换的文本
            text = context.input_data
            if not text or not isinstance(text, str):
                # 尝试从共享数据中获取默认文本
                vision_result = context.shared_data.get("last_vision_result", {})
                text = vision_result.get("description", "无内容")
            
            print(f"[SpeakAction] Text to speak: {text}")
            
            # 获取音色配置
            voice = context.config.get("voice", self.voice)
            speed = context.config.get("speed", self.speed)
            
            # 调用 TTS 模型
            if self.openai_client is None:
                # Mock 模式：返回模拟数据
                print("[SpeakAction] Using mock mode (no API key)")
                audio_bytes = b"mock_audio_data"
                duration = len(text) * 0.1  # 模拟音频时长
            else:
                audio_bytes = await self.openai_client.tts_completion(
                    model=self.model_name,
                    text=text,
                    voice=voice,
                    speed=speed
                )
                duration = len(audio_bytes) / 16000.0  # 假设 16kHz 采样率
            
            # 播放音频（如果启用自动播放）
            if self.auto_play and len(audio_bytes) > 0:
                await self._play_audio(audio_bytes)
            
            elapsed_time = time.time() - start_time
            print(f"[SpeakAction] Execution complete in {elapsed_time:.2f}s")
            
            return ActionResult(
                success=True,
                output={
                    "audio_bytes": audio_bytes,
                    "duration": duration,
                    "text": text
                },
                metadata={
                    "elapsed_time": elapsed_time,
                    "audio_size": len(audio_bytes),
                    "model": self.model_name,
                    "voice": voice
                }
            )
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            print(f"[SpeakAction] Execution failed: {e}")
            return ActionResult(
                success=False,
                error=e,
                metadata={"elapsed_time": elapsed_time}
            )
    
    async def _play_audio(self, audio_bytes: bytes) -> None:
        """播放音频
        
        Args:
            audio_bytes: 音频数据
        """
        try:
            print(f"[SpeakAction] Playing audio ({len(audio_bytes)} bytes)...")
            
            # TODO: 实际实现音频播放逻辑
            # 可以使用 pyaudio、sounddevice 或其他音频库
            # 这里只是占位实现
            
            # 示例：使用 subprocess 调用系统播放器
            # import subprocess
            # import tempfile
            # with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            #     f.write(audio_bytes)
            #     subprocess.run(['ffplay', '-nodisp', '-autoexit', f.name])
            
            print("[SpeakAction] Audio playback simulated (not implemented)")
            
        except Exception as e:
            print(f"[SpeakAction] Audio playback failed: {e}")
    
    def cleanup(self) -> None:
        """清理资源"""
        print("[SpeakAction] Cleaning up...")
        
        if self.openai_client:
            self.openai_client.close()
            self.openai_client = None
        
        self._initialized = False
        print("[SpeakAction] Cleanup complete")
