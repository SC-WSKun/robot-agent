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