# core/agent.py
import asyncio
import time
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
from core.camera import CameraSensor
from core.mcp_manager import McpManager

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
    """巡检机器人代理主类"""
    
    def __init__(self, patrol_interval: float = 30.0):
        """
        初始化机器人代理
        
        Args:
            patrol_interval: 摄像头检查间隔时间(秒)
        """
        self.state = AgentState.IDLE
        self.patrol_interval = patrol_interval
        
        # 传感器和工具
        self.camera = CameraSensor()
        self.mcp_tool = McpManager()
        
        # 任务管理
        self.task_queue: List[Task] = []
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # 运行控制
        self._patrol_task: Optional[asyncio.Task] = None
        self._task_manager_task: Optional[asyncio.Task] = None
        
        print("[Agent] Robot agent initialized in IDLE state")
    
    def start(self):
        """启动代理"""
        print("[Agent] Starting robot agent...")
        self.set_state(AgentState.PATROLLING)
        
    def stop(self):
        """停止代理"""
        print("[Agent] Stopping robot agent...")
        self.set_state(AgentState.IDLE)
        
        # 取消所有运行中的任务
        if self._patrol_task:
            self._patrol_task.cancel()
            
        if self._task_manager_task:
            self._task_manager_task.cancel()
            
        # 取消所有正在运行的任务
        for task in self.running_tasks.values():
            task.cancel()
    
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
        """巡逻主循环"""
        try:
            print("[Agent] Entering patrol loop")
            while True:
                if self.state == AgentState.PATROLLING:
                    # 捕获图像并分析
                    image_data = await self.camera.capture_image()
                    analysis_result = await self.mcp_tool.analyze_image(image_data)
                    
                    # 根据分析结果采取行动
                    await self._handle_analysis_result(analysis_result)
                
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
        """处理紧急情况"""
        print(f"[Agent] Emergency detected: {emergency_data}")
        self.set_state(AgentState.ALERT)
        
        # 创建紧急响应任务
        task = Task(
            id=f"emergency_{int(time.time())}",
            name="Emergency Response",
            callback=self._execute_emergency_response,
            created_at=time.time(),
            timeout=120.0
        )
        
        # 添加紧急数据到任务
        task.data = emergency_data
        self.task_queue.append(task)
        
        # 切换到响应状态
        self.set_state(AgentState.RESPONDING)
    
    async def _execute_emergency_response(self, task: Task):
        """执行紧急响应"""
        try:
            print(f"[Agent] Executing emergency response for task {task.id}")
            
            success = await self.mcp_tool.call_emergency_service(task.data)
            if success:
                print(f"[Agent] Emergency service called successfully for task {task.id}")
                task.status = "completed"
            else:
                print(f"[Agent] Failed to call emergency service for task {task.id}")
                task.status = "failed"
                
        except Exception as e:
            print(f"[Agent] Error executing emergency response: {e}")
            task.status = "failed"
        
        finally:
            # 完成后回到巡逻状态
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

# 单测
async def main():
    """主函数示例"""
    agent = RobotAgent(patrol_interval=30.0)
    agent.start()
    
    # 运行一段时间后停止
    await asyncio.sleep(300)  # 运行5分钟
    agent.stop()

if __name__ == "__main__":
    asyncio.run(main())