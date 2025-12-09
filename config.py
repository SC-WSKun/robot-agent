# 硬件配置
VIDEO_DEV="/dev/video0"

# OpenAI API 配置
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-cc8ad3c0dae048beafd7e89094230468")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# 模型配置
QWEN_MAX_MODEL = "qwen-max"  # 任务决策推理模型
QWEN_VL_MODEL = "qwen-vl-plus"  # 视觉理解模型
QWEN_OMNI_MODEL = "qwen-omni-flash"  # 多模态交互模型

# Agent 配置
PATROL_INTERVAL = 30.0  # 巡逻间隔（秒）
ACTION_TIMEOUT = 10.0  # Action 默认超时（秒）