"""诊断 Astra 彩色流 — 多种方案"""
from openni import openni2
import cv2
import numpy as np

lib_path = "/home/henry/git/AI-Projects/OpenNI_2.3/sdk/libs"
openni2.initialize(lib_path)
print("✅ OpenNI2 初始化成功")

def try_read_color(device, label):
    """尝试读取彩色帧，带超时提示"""
    print(f"\n{'='*40}")
    print(f"方案: {label}")

    try:
        color_stream = device.create_color_stream()
        if color_stream is None:
            print("❌ create_color_stream 返回 None")
            return False

        # 尝试设置视频模式
        try:
            modes = color_stream.get_supported_video_modes()
            print(f"   支持的彩色模式: {len(modes)} 种")
            for m in modes[:3]:
                print(f"     {m.width}x{m.height} @ {m.fps}fps "
                      f"pixel={m.pixelFormat}")
            # 设第一个模式
            color_stream.set_video_mode(modes[0])
            print(f"   设置模式: {modes[0].width}x{modes[0].height}")
        except Exception as e:
            print(f"   ⚠️ 无法设置视频模式: {e}")

        color_stream.start()
        print("   ✅ 彩色流启动")

        import time
        start = time.time()
        print("   ⏳ read_frame...")
        frame = color_stream.read_frame()
        elapsed = time.time() - start
        print(f"   ✅ 成功! {frame.width}x{frame.height} ({elapsed:.1f}s)")
        color_stream.stop()
        return True
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return False

try:
    device = openni2.Device.open_any()
    print(f"📷 {device.get_device_info().name}")

    # 方案1: 纯彩色流，不碰深度
    try_read_color(device, "纯彩色流(不开深度)")

except Exception as e:
    print(f"❌ {e}")
finally:
    try:
        openni2.unload()
    except:
        pass
    print("✅ 结束")
