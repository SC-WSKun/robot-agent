# Robot Agent 使用指南

## 概述

Robot Agent 已重构为基于 Action 插槽机制的中枢管理器架构，支持灵活扩展各种功能模块。

## 快速开始

### 1. 配置环境变量

```bash
# OpenAI API 配置（可选，不配置时使用 Mock 模式）
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
```

### 2. 运行 Agent

```bash
# 使用 uv 运行
uv run python main.py

# 或者直接运行
python main.py
```

## 核心架构

### Action 插槽机制

Agent 通过 Actions 插槽实现能力扩展：

```python
from core.agent import RobotAgent
from core.action import WatchAction, SpeakAction, AlertAction

# 创建 Agent
agent = RobotAgent(patrol_interval=30.0)

# 注册 Actions
agent.register_action("watch", WatchAction())
agent.register_action("speak", SpeakAction())
agent.register_action("alert", AlertAction())

# 启动
agent.start()
```

### 内置 Actions

| Action 名称 | 功能 | 依赖 |
|------------|------|------|
| **WatchAction** | 图像理解，用于巡检环境分析 | 摄像头、OpenAI API (qwen-vl-plus) |
| **SpeakAction** | 语音合成，将文本转为语音 | OpenAI API (qwen-omni-flash) |
| **AlertAction** | 应急调用，处理紧急情况 | MCP Manager |

## 高级用法

### 1. 自定义 Action

创建自定义 Action 只需继承 `BaseAction`：

```python
from core.action.base import BaseAction, ActionContext, ActionResult, ActionMetadata

class MyCustomAction(BaseAction):
    def get_metadata(self) -> ActionMetadata:
        return ActionMetadata(
            name="my_action",
            version="1.0.0",
            description="我的自定义 Action",
            dependencies=["some_service"],
            capabilities=["custom_capability"]
        )
    
    def initialize(self, config_dict: Dict[str, Any]) -> None:
        # 初始化资源
        self._initialized = True
    
    async def execute(self, context: ActionContext) -> ActionResult:
        # 执行业务逻辑
        return ActionResult(
            success=True,
            output={"result": "处理完成"}
        )
    
    def cleanup(self) -> None:
        # 清理资源
        self._initialized = False
```

### 2. 执行 Action

```python
# 单独执行
result = await agent.execute_action("watch")

# 执行 Action 链
results = await agent.execute_action_chain(["watch", "speak"])

# 带输入数据执行
result = await agent.execute_action("speak", input_data="你好，世界")
```

### 3. 共享上下文

Actions 之间通过共享上下文传递数据：

```python
# WatchAction 写入共享数据
context.shared_data["last_vision_result"] = analysis_result

# SpeakAction 读取共享数据
vision_result = context.shared_data.get("last_vision_result", {})
```

## 配置说明

### config.py 配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `VIDEO_DEV` | 摄像头设备路径 | `/dev/video0` |
| `OPENAI_API_KEY` | OpenAI API 密钥 | 环境变量 |
| `OPENAI_BASE_URL` | API 端点 URL | 阿里云 DashScope |
| `QWEN_MAX_MODEL` | 决策推理模型 | `qwen-max` |
| `QWEN_VL_MODEL` | 视觉理解模型 | `qwen-vl-plus` |
| `QWEN_OMNI_MODEL` | 多模态交互模型 | `qwen-omni-flash` |
| `PATROL_INTERVAL` | 巡逻间隔（秒） | `30.0` |
| `ACTION_TIMEOUT` | Action 默认超时（秒） | `10.0` |

### Action 配置

注册 Action 时可传入配置参数：

```python
agent.register_action("watch", WatchAction(), {
    "api_key": "custom-api-key",
    "model_name": "qwen-vl-max",
    "temperature": 0.5
})
```

## 运行模式

### Mock 模式

未配置 `OPENAI_API_KEY` 时，Actions 自动进入 Mock 模式：
- WatchAction 返回模拟的图像分析结果
- SpeakAction 返回模拟的音频数据
- 适合开发和测试

### 生产模式

配置 `OPENAI_API_KEY` 后，Actions 调用真实的 API：
- 需要网络连接
- 消耗 API 配额
- 返回真实的模型输出

## 测试

```bash
# 运行所有测试
uv run pytest test/ -v

# 运行 Action 测试
uv run pytest test/test_actions.py -v

# 运行单个测试
uv run pytest test/test_actions.py::TestWatchAction::test_watch_action_execute_mock -v
```

## 故障排查

### 问题：摄像头无法打开

**解决方案：**
1. 检查摄像头设备路径：`ls /dev/video*`
2. 修改 `config.py` 中的 `VIDEO_DEV`
3. 确保有摄像头访问权限

### 问题：API 调用失败

**解决方案：**
1. 验证 `OPENAI_API_KEY` 是否正确
2. 检查网络连接
3. 查看 API 配额是否充足
4. 可以先使用 Mock 模式测试

### 问题：Action 执行超时

**解决方案：**
1. 增加 `ACTION_TIMEOUT` 配置
2. 检查网络延迟
3. 优化 Action 内部逻辑

## 扩展开发

### 添加新的 Action

1. 在 `core/action/` 创建新文件
2. 继承 `BaseAction` 并实现抽象方法
3. 在 `core/action/__init__.py` 中导出
4. 在 Agent 中注册使用

### 集成 MCP 服务

保留的 `McpManager` 可以封装为 Action：

```python
from core.action.base import BaseAction
from core.mcp_manager import McpManager

class McpAction(BaseAction):
    # 实现 MCP 服务调用逻辑
    pass
```

## 最佳实践

1. **资源管理**：确保在 `cleanup()` 中释放所有资源
2. **错误处理**：在 `execute()` 中捕获异常并返回错误信息
3. **日志记录**：使用统一的日志前缀（如 `[ActionName]`）
4. **超时控制**：长时间运行的操作应支持超时配置
5. **共享数据**：使用明确的键名避免冲突

## 参考文档

- 设计文档：`.qoder/quests/central-controller-design.md`
- API 参考：项目 Wiki
- 测试示例：`test/test_actions.py`
