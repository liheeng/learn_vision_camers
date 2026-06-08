# from primesense import openni2
# Openni2 does not support Dabai Pro
import os

from openni import openni2
import cv2
import numpy as np

# ===================== Orbbec Astra 深度 + 红外 =====================
default_lib_path = "/home/henry/git/AI-Projects/vision_class/OpenNI_2.3.0/sdk/libs"
lib_path = os.getenv("OPENNI2_REDIST") or os.environ.setdefault("OPENNI2_REDIST", default_lib_path)
openni2.initialize(lib_path)
print("✅ OpenNI2 初始化成功")

try:
    device = openni2.Device.open_any()
    print(f"✅ 相机: {device.get_device_info().name}")

    # 深度流
    depth_stream = device.create_depth_stream()
    if depth_stream is None:
        raise RuntimeError("❌ 深度流创建失败")
    depth_stream.start()
    print("✅ 深度流启动成功")

    # 红外流
    ir_stream = device.create_ir_stream()
    has_ir = False
    if ir_stream is not None:
        ir_stream.start()
        has_ir = True
        print("✅ 红外流启动成功")
    else:
        print("⚠️  红外流不可用")

    # ===================== 主循环 =====================
    print("按 q 退出")

    first = True
    while True:
        d_frame = depth_stream.read_frame()
        w, h = d_frame.width, d_frame.height
        depth = np.array(d_frame.get_buffer_as_uint16()).reshape(h, w)

        if first:
            first = False
            print(f"[初始化] 深度: {w}x{h}, min={depth.min()}, max={depth.max()}")

        # 自适应范围
        nz = depth[depth > 0]
        if len(nz) > 100:
            lo, hi = int(nz.min()), int(nz.max())
            if hi <= lo:
                hi = lo + 1
        else:
            lo, hi = 500, 8000

        # 深度 JET
        norm = ((depth.clip(lo, hi) - lo) * 255 // (hi - lo)).astype(np.uint8)
        jet = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
        jet[depth == 0] = (0, 0, 0)

        # 深度灰度
        raw = cv2.cvtColor(np.right_shift(depth, 3).astype(np.uint8), cv2.COLOR_GRAY2BGR)

        # 红外（和 NiViewer 右边一样）
        if has_ir:
            ir_frame = ir_stream.read_frame()
            iw, ih = ir_frame.width, ir_frame.height
            ir_data = np.array(ir_frame.get_buffer_as_uint16()).reshape(ih, iw)
            # IR 伪彩色（类似热成像效果）
            ir_norm = np.right_shift(ir_data, 2).astype(np.uint8)
            ir_color = cv2.applyColorMap(ir_norm, cv2.COLORMAP_INFERNO)
            if (iw, ih) != (w, h):
                ir_color = cv2.resize(ir_color, (w, h))
        else:
            ir_color = np.zeros_like(jet)

        # 2x2 网格: 左上 JET | 右上 IR伪彩色 / 左下 Raw | 右下 空
        top = np.hstack((jet, ir_color))
        bot = np.hstack((raw, np.zeros_like(jet)))
        cv2.imshow("DabaiPro | Depth + IR", np.vstack((top, bot)))

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
except Exception as e:
    print(f"❌ 发生错误: {e}")

finally:
    if 'depth_stream' in locals() and depth_stream is not None:
        depth_stream.stop()
    if 'ir_stream' in locals() and ir_stream is not None:
        ir_stream.stop()
    openni2.unload()
    cv2.destroyAllWindows()
    print("✅ 程序已安全退出")