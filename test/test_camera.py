# test/test_camera.py
import pytest
from unittest.mock import patch, Mock
import asyncio
from core.camera import CameraSensor

@patch('core.camera.cv2')
def test_camera_initialization(mock_cv2):
    """测试摄像头初始化"""
    camera = CameraSensor()
    assert camera.cap is None

@pytest.mark.asyncio
@patch('core.camera.cv2')
async def test_capture_image_success(mock_cv2):
    """测试成功捕获图像"""
    # 模拟OpenCV行为
    mock_cap = Mock()
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, Mock())  # 成功读取帧
    mock_cv2.imencode.return_value = (True, Mock())
    
    camera = CameraSensor()
    result = await camera.capture_image()
    
    assert result is not None
    mock_cv2.VideoCapture.assert_called_once()

@pytest.mark.asyncio
@patch('core.camera.cv2')
async def test_capture_image_failure(mock_cv2):
    """测试捕获图像失败"""
    # 模拟OpenCV行为（读取帧失败）
    mock_cap = Mock()
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (False, None)  # 读取帧失败
    
    camera = CameraSensor()
    result = await camera.capture_image()
    
    assert result is None