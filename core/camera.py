import cv2
import asyncio
import numpy as np
from config import VIDEO_DEV
class CameraSensor:
    """摄像头传感器模拟类"""
    
    def __init__(self):
        """初始化摄像头"""
        self.cap = None
    
    def __del__(self):
        """释放摄像头"""
        if self.cap is not None:
            self.cap.release()
    
    async def capture_image(self) -> bytes:
        """捕获图像数据"""
        print("[Camera] Capturing image...")
        
        # 新开线程执行摄像头操作，避免堵塞
        image_bytes = await asyncio.to_thread(self._capture_sync)
        
        if image_bytes is None:
            print("[Camera] Failed to capture image.")
            return None
        
        print("[Camera] Image captured successfully.")
        return image_bytes
    
    def _capture_sync(self) -> bytes:
        """同步方式捕获图像"""
        try:
            # 初始化摄像头
            if self.cap is None:
                self.cap = cv2.VideoCapture(VIDEO_DEV)
                if not self.cap.isOpened():
                    print(f"[Camera] Cannot open camera device {VIDEO_DEV}")
                    return None
            
            # 设置摄像头参数
            # self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            # self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # 捕获帧
            ret, frame = self.cap.read()
            if not ret:
                print("[Camera] Cannot read frame from camera")
                return None
            
            # 将图像转换为 JPEG 格式的字节数据
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            return buffer.tobytes()
            
        except Exception as e:
            print(f"[Camera] Error capturing image: {e}")
            return None