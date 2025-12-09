# test/test_camera_integration.py
import pytest
import asyncio
import os
from core.camera import CameraSensor

@pytest.mark.asyncio
@pytest.mark.skipif(os.environ.get('SKIP_INTEGRATION') == '1', reason="Skipping integration tests")
async def test_camera_integration():
    """摄像头集成测试 - 实际测试硬件"""
    if not os.environ.get('RUN_INTEGRATION'):
        pytest.skip("Integration tests skipped. Set RUN_INTEGRATION=1 to run.")
    
    print("\n=== Camera Integration Test ===")
    
    camera = CameraSensor()
    
    try:
        print("1. Testing camera initialization...")
        # 检查摄像头是否能初始化
        assert camera is not None
        assert camera.cap is None  # 初始状态
        
        print("2. Testing first image capture...")
        image_data = await camera.capture_image()
        
        # 验证捕获结果
        assert image_data is not None, "Image capture returned None"
        assert isinstance(image_data, bytes), "Image data should be bytes"
        assert len(image_data) > 0, "Image data should not be empty"
        
        print(f"   ✓ Captured image: {len(image_data)} bytes")
        
        print("3. Testing second image capture...")
        image_data2 = await camera.capture_image()
        
        assert image_data2 is not None, "Second capture returned None"
        assert len(image_data2) > 0, "Second capture returned empty data"
        
        print(f"   ✓ Captured second image: {len(image_data2)} bytes")
        
        # 保存图像供检查（可选）
        try:
            with open("test/temp/integration_test_image.jpg", "wb") as f:
                f.write(image_data)
            print("   ✓ Saved test image to test/temp/integration_test_image.jpg")
        except Exception as e:
            print(f"   ⚠ Could not save test image: {e}")
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        raise
        
    finally:
        # 清理资源
        if hasattr(camera, 'cap') and camera.cap:
            camera.cap.release()
            print("   ✓ Camera resources released")

if __name__ == "__main__":
    # 可以直接运行这个测试
    os.environ['RUN_INTEGRATION'] = '1'
    asyncio.run(test_camera_integration())