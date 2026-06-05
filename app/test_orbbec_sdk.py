"""
Orbbec SDK 替代 OpenNI2 的迁移指南

═══════════════════════════════════════════
第 1 步: 安装 Orbbec SDK
═══════════════════════════════════════════
"""
# ---- Linux (推荐方式) ----
# 1. 下载最新 deb 包:
#    https://github.com/orbbec/OrbbecSDK/releases
#    选择: orbbecsdk_<version>_amd64.deb
#
# 2. 安装:
#    sudo dpkg -i orbbecsdk_*.deb
#    sudo apt install -f
#
# 3. 安装 Python 绑定:
#    pip install pyorbbecsdk
#
# 4. 验证:
#    python -c "from pyorbbecsdk import Context; print('OK')"

# ---- 或者用 udev 规则（免 root 访问 USB）----
# sudo cp /usr/lib/OrbbecSDK/scripts/99-orbbec.rules /etc/udev/rules.d/
# sudo udevadm control --reload-rules
# sudo udevadm trigger

# ═══════════════════════════════════════════
# 第 2 步: API 对照表
# ═══════════════════════════════════════════
"""
OpenNI2                          →  Orbbec SDK
──────────────────────────────────────────────────
openni2.initialize(path)         →  不需要 (库已系统安装)
Device.open_any()                →  Context().query_devices().get_device(0)
dev.create_depth_stream()        →  Pipeline + Config.enable_depth_stream()
stream.start()                   →  pipeline.start(config)
stream.read_frame()              →  pipeline.wait_for_frames()
frame.get_buffer_as_uint16()     →  depth_frame.get_data()  # numpy array
depth_frame.width                →  depth_frame.get_width()
dev.create_color_stream()        →  config.enable_color_stream()
openni2.unload()                 →  pipeline.stop()
"""

# ═══════════════════════════════════════════
# 第 3 步: 等价示例代码
# ═══════════════════════════════════════════

import cv2
import numpy as np

try:
    from pyorbbecsdk import Context, Config, Pipeline
    from pyorbbecsdk import FormatConvertFilter, OBFormat

    ctx = Context()
    device_list = ctx.query_devices()
    if device_list.get_count() == 0:
        raise RuntimeError("未检测到 Orbbec 设备")

    device = device_list.get_device(0)
    print(f"✅ 设备: {device.get_device_info().get_name()}")

    pipeline = Pipeline(device)
    config = Config()

    # 启用深度流 (640x480, 30fps)
    config.enable_depth_stream(640, 480, 30, OBFormat.Y16)
    # 启用彩色流 (640x480, 30fps)
    config.enable_color_stream(640, 480, 30, OBFormat.RGB)

    pipeline.start(config)
    print("✅ 流已启动")

    # 格式转换器 (Y16 深度 → RGB 显示用)
    depth_filter = FormatConvertFilter()

    print("按 q 退出")
    while True:
        frames = pipeline.wait_for_frames(1000)  # 1000ms 超时
        if frames is None:
            continue

        # --- 深度 ---
        depth_frame = frames.get_depth_frame()
        if depth_frame is not None:
            w, h = depth_frame.get_width(), depth_frame.get_height()
            depth_data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16).reshape(h, w)

            # JET 映射
            nz = depth_data[depth_data > 0]
            lo = int(nz.min()) if len(nz) > 100 else 500
            hi = int(nz.max()) if len(nz) > 100 else 8000
            if hi <= lo:
                hi = lo + 1
            norm = ((depth_data.clip(lo, hi) - lo) * 255 // (hi - lo)).astype(np.uint8)
            jet = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
            jet[depth_data == 0] = (0, 0, 0)
        else:
            jet = np.zeros((480, 640, 3), dtype=np.uint8)

        # --- 彩色 ---
        color_frame = frames.get_color_frame()
        if color_frame is not None:
            cw, ch = color_frame.get_width(), color_frame.get_height()
            color_data = np.frombuffer(color_frame.get_data(), dtype=np.uint8).reshape(ch, cw, 3)
            color_bgr = cv2.cvtColor(color_data, cv2.COLOR_RGB2BGR)
        else:
            color_bgr = np.zeros((480, 640, 3), dtype=np.uint8)

        # 拼接显示
        gray = cv2.cvtColor(np.right_shift(depth_data, 3).astype(np.uint8), cv2.COLOR_GRAY2BGR)
        left = np.vstack((jet, gray))
        right = cv2.resize(color_bgr, (640, 480)) if color_bgr.shape[:2] != (480, 640) else color_bgr
        # 左右拼接需要同高 → color 放右边单行
        top_row = np.hstack((jet, right))
        bot_row = np.hstack((gray, np.zeros_like(right)))
        display = np.vstack((top_row, bot_row))

        cv2.imshow("Orbbec Astra | Depth + Color", display)
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    pipeline.stop()

except ImportError:
    print("❌ pyorbbecsdk 未安装")
    print("   pip install pyorbbecsdk")
    print("   并安装 OrbbecSDK deb 包: https://github.com/orbbec/OrbbecSDK/releases")

except Exception as e:
    print(f"❌ 错误: {e}")

finally:
    cv2.destroyAllWindows()
    print("✅ 结束")
