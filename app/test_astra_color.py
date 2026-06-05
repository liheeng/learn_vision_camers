"""Astra Pro 彩色流 — 纯 OpenNI2 方案"""
from openni import openni2
import numpy as np
import cv2
import time

openni2.initialize("/home/henry/git/AI-Projects/OpenNI_2.3/sdk/libs")
dev = openni2.Device.open_any()
print(f"✅ {dev.get_device_info().name}")

# 先启动深度流（Astra 深度必须先跑）
depth = dev.create_depth_stream()
depth.start()
print("✅ 深度流启动")

# 启动彩色流
color = dev.create_color_stream()
if color is None:
    print("❌ 彩色流创建失败")
    exit(1)

# 设置视频模式（YUY2, 640x480, 30fps）
try:
    from openni import VideoMode
    vm = VideoMode()
    vm.pixelFormat = 1  # YUYV
    vm.width = 640
    vm.height = 480
    vm.fps = 30
    color.set_video_mode(vm)
    print("✅ 设置彩色模式: 640x480 YUY2@30fps")
except Exception as e:
    print(f"⚠️ 设置视频模式失败: {e}，用默认模式")

color.start()
print("✅ 彩色流启动")

# 先读几帧深度 "预热" 设备
for i in range(10):
    depth.read_frame()
    time.sleep(0.05)
print("✅ 预热完成，尝试读彩色帧...")

# 尝试读彩色帧
for attempt in range(5):
    print(f"  尝试 {attempt+1}/5...", end=" ", flush=True)
    try:
        frame = color.read_frame()
        w, h = frame.width, frame.height
        data = np.array(frame.get_buffer_as_uint8())
        print(f"✅ {w}x{h}, {len(data)} bytes")

        # YUY2 -> BGR (手动转换，不依赖 cvtColor)
        # YUY2: 每 2 像素占 4 字节 [Y0,U,Y1,V]
        if len(data) == w * h * 2:  # YUY2
            yuv = data.reshape(h, w, 2)
            y = yuv[:, :, 0].astype(np.float32)
            u = yuv[:, ::2, 1].astype(np.float32)  # U 每 2 像素一个
            v = yuv[:, 1::2, 1].astype(np.float32)  # V 每 2 像素一个
            # 上采样 U/V 到全分辨率
            u = np.repeat(np.repeat(u, 2, axis=1), 1, axis=0)[:h, :w]
            v = np.repeat(np.repeat(v, 2, axis=1), 1, axis=0)[:h, :w]
            # YUV -> BGR
            r = y + 1.402 * (v - 128)
            g = y - 0.344 * (u - 128) - 0.714 * (v - 128)
            b = y + 1.772 * (u - 128)
            bgr = np.stack([b, g, r], axis=2).clip(0, 255).astype(np.uint8)
        else:
            bgr = data.reshape(h, w, 3)
            bgr = cv2.cvtColor(bgr, cv2.COLOR_RGB2BGR)

        print("  显示中, 按 q 退出")
        while True:
            depth.read_frame()
            frame = color.read_frame()
            data = np.array(frame.get_buffer_as_uint8())
            if len(data) == w * h * 2:
                yuv = data.reshape(h, w, 2)
                y = yuv[:, :, 0].astype(np.float32)
                u = yuv[:, ::2, 1].astype(np.float32)
                v = yuv[:, 1::2, 1].astype(np.float32)
                u = np.repeat(np.repeat(u, 2, axis=1), 1, axis=0)[:h, :w]
                v = np.repeat(np.repeat(v, 2, axis=1), 1, axis=0)[:h, :w]
                r = y + 1.402 * (v - 128)
                g = y - 0.344 * (u - 128) - 0.714 * (v - 128)
                b = y + 1.772 * (u - 128)
                bgr = np.stack([b, g, r], axis=2).clip(0, 255).astype(np.uint8)
            else:
                bgr = data.reshape(h, w, 3)
            cv2.imshow("Astra Color (OpenNI2)", bgr)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                color.stop()
                depth.stop()
                openni2.unload()
                cv2.destroyAllWindows()
                exit(0)
    except Exception as e:
        print(f"❌ {e}")

print("❌ 彩色流不可用")
depth.stop()
openni2.unload()
