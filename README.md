# Robot Agent

本项目是机器人的Agent，这是 [PRD](https://k1ntis7zj04.feishu.cn/docx/GKw1dr5bHoqx8KxAAMzcmBMBnDc?from=from_copylink) 链接

## 运行测试

本项目使用 pytest 进行单元测试，可以使用下面的命令运行所有单测:
```bash
uv run pytest
```
如果需要更详细的信息，可以增加 -v 参数:
```bash
uv run pytest -v
```
如果只需要运行特定测试，可以使用下面的命令（自行替换文件名和测试函数名）:
```bash
uv run pytest test/test_camera.py::test_camera_initialization -s
```
如果需要运行集成测试，可以使用下面的命令:
```bash
# 先设置环境变量
export RUN_INTEGRATION=1
# 然后运行测试
uv run pytest test/test_camera_integration.py -v -s
```

## 待办事项 (TODO)

以下是代码中需要完成的待办事项：

1. **音频播放功能实现**
   - 文件：`core/action/speak_action.py`
   - 位置：第165行
   - 描述：需要实际实现音频播放逻辑
   - 可以使用 pyaudio、sounddevice 或其他音频库
   - 示例：使用 subprocess 调用系统播放器

2. **MCP Manager 架构优化**
   - 文件：`core/mcp_manager.py`
   - 位置：模块注释部分（第1-3行）
   - 描述：这里不应该是一个 MCP Tool Caller，而是一个 MCP Server 的调用器。可以管理 Agent 连接的 Server 连接。