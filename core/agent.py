# core/agent.py
import asyncio
import time
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from abc import ABC, abstractmethod

# 导入 Action 相关类
from core.action import (
    BaseAction,
    ActionContext,
    ActionResult,
    ActionMetadata,
    WatchAction,
    SpeakAction,
    AlertAction,
)
import config

class AgentState(Enum):
    """代理状态枚举"""
    IDLE = "idle"
    PATROLLING = "patrolling"
    RESPONDING = "responding"
    ALERT = "alert"

@dataclass
class Task:
    """任务数据结构"""
    id: str
    name: str
    callback: Callable
    created_at: float
    timeout: float = 60.0
    status: str = "pending"  # pending, running, completed, failed, timeout

class RobotAgent:
    """巡检机器人代理主类（重构后的中枢管理器）
    
    通过 Actions 插槽机制实现能力的灵活扩展
    """
    
    def __init__(self, patrol_interval: float = None):
        """
        初始化机器人代理
        
        Args:
            patrol_interval: 巡逻间隔时间(秒)
        """
        self.state = AgentState.IDLE
        self.patrol_interval = patrol_interval or config.PATROL_INTERVAL
        
        # Actions 插槽
        self.actions: Dict[str, BaseAction] = {}
        self.action_metadata: Dict[str, ActionMetadata] = {}
        self.shared_context: Dict[str, Any] = {}  # Action 间共享的上下文
        
        # 任务管理（保留）
        self.task_queue: List[Task] = []
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # 运行控制
        self._patrol_task: Optional[asyncio.Task] = None
        self._task_manager_task: Optional[asyncio.Task] = None
        
        print("[Agent] Robot agent initialized in IDLE state")
        print("[Agent] Using action-based architecture")
    
    def start(self):
        """启动代理"""
        print("[Agent] Starting robot agent...")
        self.set_state(AgentState.PATROLLING)
    
    def stop(self):
        """停止代理"""
        print("[Agent] Stopping robot agent...")
        
        # 清理所有 Actions
        for action_name in list(self.actions.keys()):
            self.unregister_action(action_name)
        
        self.set_state(AgentState.IDLE)
        
        # 取消所有运行中的任务
        if self._patrol_task:
            self._patrol_task.cancel()
            
        if self._task_manager_task:
            self._task_manager_task.cancel()
            
        # 取消所有正在运行的任务
        for task in self.running_tasks.values():
            task.cancel()
    
    def register_action(self, name: str, action: BaseAction, config_dict: Dict[str, Any] = None) -> None:
        """注册并初始化一个 Action
        
        Args:
            name: Action 名称
            action: Action 实例
            config_dict: 配置参数
        """
        try:
            print(f"[Agent] Registering action: {name}")
            
            # 初始化 Action
            if config_dict is None:
                config_dict = {}
            action.initialize(config_dict)
            
            # 存储 Action 和元信息
            self.actions[name] = action
            self.action_metadata[name] = action.metadata
            
            print(f"[Agent] Action '{name}' registered successfully")
            
        except Exception as e:
            print(f"[Agent] Failed to register action '{name}': {e}")
            raise
    
    def unregister_action(self, name: str) -> None:
        """注销 Action 并清理资源
        
        Args:
            name: Action 名称
        """
        if name in self.actions:
            print(f"[Agent] Unregistering action: {name}")
            
            action = self.actions[name]
            action.cleanup()
            
            del self.actions[name]
            del self.action_metadata[name]
            
            print(f"[Agent] Action '{name}' unregistered")
    
    async def execute_action(self, name: str, input_data: Any = None, config_dict: Dict[str, Any] = None) -> ActionResult:
        """执行指定的 Action
        
        Args:
            name: Action 名称
            input_data: 输入数据
            config_dict: 动态配置参数
            
        Returns:
            ActionResult: 执行结果
        """
        if name not in self.actions:
            print(f"[Agent] Action '{name}' not found")
            return ActionResult(
                success=False,
                error=Exception(f"Action '{name}' not registered")
            )
        
        try:
            # 构造 ActionContext
            context = ActionContext(
                agent_state=self.state,
                input_data=input_data,
                shared_data=self.shared_context,
                config=config_dict or {}
            )
            
            # 执行 Action
            action = self.actions[name]
            result = await action.execute(context)
            
            return result
            
        except Exception as e:
            print(f"[Agent] Error executing action '{name}': {e}")
            return ActionResult(
                success=False,
                error=e
            )
    
    async def execute_action_chain(self, action_names: List[str], input_data: Any = None) -> List[ActionResult]:
        """按顺序执行多个 Action
        
        Args:
            action_names: Action 名称列表
            input_data: 初始输入数据
            
        Returns:
            List[ActionResult]: 执行结果列表
        """
        results = []
        current_input = input_data
        
        for action_name in action_names:
            result = await self.execute_action(action_name, current_input)
            results.append(result)
            
            # 如果执行失败，停止后续 Action
            if not result.success:
                print(f"[Agent] Action chain stopped at '{action_name}' due to failure")
                break
            
            # 使用当前 Action 的输出作为下一个 Action 的输入
            current_input = result.output
        
        return results
    
    def set_state(self, state: AgentState):
        """设置代理状态"""
        print(f"[Agent] State changed from {self.state.value} to {state.value}")
        self.state = state
        
        if state == AgentState.PATROLLING:
            self._start_patrol_routine()
        elif state == AgentState.IDLE:
            self._stop_patrol_routine()
    
    def _start_patrol_routine(self):
        """启动巡逻例程"""
        if self._patrol_task is None or self._patrol_task.done():
            self._patrol_task = asyncio.create_task(self._patrol_loop())
            print("[Agent] Patrol routine started")
            
        if self._task_manager_task is None or self._task_manager_task.done():
            self._task_manager_task = asyncio.create_task(self._task_manager())
            print("[Agent] Task manager started")
    
    def _stop_patrol_routine(self):
        """停止巡逻例程"""
        if self._patrol_task:
            self._patrol_task.cancel()
            self._patrol_task = None
            print("[Agent] Patrol routine stopped")
            
        if self._task_manager_task:
            self._task_manager_task.cancel()
            self._task_manager_task = None
            print("[Agent] Task manager stopped")
    
    async def _patrol_loop(self):
        """巡逻主循环（使用 Action 机制）"""
        try:
            print("[Agent] Entering patrol loop (action-based)")
            while True:
                if self.state == AgentState.PATROLLING:
                    # 执行 watch Action 进行图像理解
                    if "watch" in self.actions:
                        result = await self.execute_action("watch")
                        
                        if result.success:
                            # 根据分析结果采取行动
                            analysis_result = result.output
                            await self._handle_analysis_result(analysis_result)
                        else:
                            print(f"[Agent] Watch action failed: {result.error}")
                    else:
                        print("[Agent] Warning: 'watch' action not registered")
                
                # 等待下次巡逻
                await asyncio.sleep(self.patrol_interval)
                
        except asyncio.CancelledError:
            print("[Agent] Patrol loop cancelled")
        except Exception as e:
            print(f"[Agent] Error in patrol loop: {e}")
    
    async def _handle_analysis_result(self, result: Dict[str, Any]):
        """处理图像分析结果"""
        print(f"[Agent] Handling analysis result: {result}")
        
        if result.get("emergency", False):
            # 处理紧急情况
            await self._handle_emergency(result)
        else:
            # 继续正常巡逻
            print("[Agent] No emergency detected, continuing patrol")
    
    async def _handle_emergency(self, emergency_data: Dict[str, Any]):
        """处理紧急情况（使用 Action 机制）"""
        print(f"[Agent] Emergency detected: {emergency_data}")
        self.set_state(AgentState.ALERT)
        
        # 执行 alert Action
        if "alert" in self.actions:
            result = await self.execute_action("alert", input_data=emergency_data)
            if result.success:
                print("[Agent] Emergency service called successfully")
            else:
                print(f"[Agent] Failed to call emergency service: {result.error}")
        
        # 执行 speak Action 进行语音播报
        if "speak" in self.actions:
            alert_text = f"检测到紧急情况：{emergency_data.get('description', '未知异常')}"
            await self.execute_action("speak", input_data=alert_text)
        
        # 切换到响应状态
        self.set_state(AgentState.RESPONDING)
        
        # 稍后回到巡逻状态
        await asyncio.sleep(5.0)
        self.set_state(AgentState.PATROLLING)
    
    async def _task_manager(self):
        """任务管理器"""
        try:
            print("[Agent] Task manager started")
            while True:
                # 处理任务队列
                await self._process_task_queue()
                
                # 检查运行中任务的超时情况
                await self._check_task_timeouts()
                
                # 短暂休眠避免过度占用CPU
                await asyncio.sleep(1.0)
                
        except asyncio.CancelledError:
            print("[Agent] Task manager cancelled")
        except Exception as e:
            print(f"[Agent] Error in task manager: {e}")
    
    async def _process_task_queue(self):
        """处理任务队列"""
        if not self.task_queue:
            return
            
        # 处理队列中的任务
        current_time = time.time()
        processed_tasks = []
        
        for task in self.task_queue:
            # 检查任务是否超时
            if current_time - task.created_at > task.timeout:
                print(f"[Agent] Task {task.id} timed out")
                task.status = "timeout"
                processed_tasks.append(task)
                continue
            
            # 启动新任务
            if task.status == "pending":
                print(f"[Agent] Starting task {task.id}: {task.name}")
                task.status = "running"
                
                # 创建异步任务
                async_task = asyncio.create_task(task.callback(task))
                self.running_tasks[task.id] = async_task
                processed_tasks.append(task)
        
        # 从队列中移除已处理的任务
        for task in processed_tasks:
            if task in self.task_queue:
                self.task_queue.remove(task)
    
    async def _check_task_timeouts(self):
        """检查运行中任务的超时情况"""
        current_time = time.time()
        timed_out_tasks = []
        
        for task_id, async_task in self.running_tasks.items():
            # 查找对应的任务对象
            task = None
            for t in self.task_queue:
                if t.id == task_id:
                    task = t
                    break
            
            # 超时取消任务
            if task and current_time - task.created_at > task.timeout:
                print(f"[Agent] Cancelling timed out task {task_id}")
                async_task.cancel()
                task.status = "timeout"
                timed_out_tasks.append(task_id)
        
        # 清理已完成或超时的任务
        finished_tasks = []
        for task_id, async_task in self.running_tasks.items():
            if async_task.done():
                finished_tasks.append(task_id)
        
        for task_id in finished_tasks + timed_out_tasks:
            self.running_tasks.pop(task_id, None)
    
    def add_task(self, task: Task):
        """添加新任务到队列"""
        print(f"[Agent] Adding task to queue: {task.name} ({task.id})")
        self.task_queue.append(task)

# 示例：使用 Action 机制的 main 函数
async def main():
    """主函数示例（使用 Action 机制）"""
    agent = RobotAgent(patrol_interval=30.0)
    
    # 注册 Actions
    agent.register_action("watch", WatchAction())
    agent.register_action("speak", SpeakAction())
    agent.register_action("alert", AlertAction())
    
    # 启动代理
    agent.start()
    
    # 运行一段时间后停止
    await asyncio.sleep(300)  # 运行5分钟
    agent.stop()

if __name__ == "__main__":
    asyncio.run(main())