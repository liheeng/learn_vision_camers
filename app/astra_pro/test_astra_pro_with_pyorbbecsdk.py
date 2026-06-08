"""
⚠️  pyorbbecsdk 限制：Astra Pro 不支持 Depth + IR 双流同时输出。
    只能选其一显示（Depth 或 IR）。需要三窗口同显请使用 OpenNI2 方案：
    python app/astra_pro/test_astra_pro_with_openni2.py
"""

import cv2
import numpy as np
from pyorbbecsdk import Context, Pipeline, Config, OBSensorType


def astra_pro_preview():
    """pyorbbecsdk 预览（Depth 或 IR 二选一 + Color）"""
    ctx = Context()
    device_list = ctx.query_devices()
    if device_list.get_count() == 0:
        print("❌ No Orbbec device found")
        return

    device = device_list.get_device_by_index(0)
    print(f"✅ Device: {device.get_device_info().get_name()}")

    pipeline = Pipeline(device)
    config = Config()

    # Depth 流 (640x480 Y12)
    depth_profiles = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
    dp = None
    for i in range(depth_profiles.get_count()):
        p = depth_profiles.get_stream_profile_by_index(i).as_video_stream_profile()
        if p.get_width() == 640 and p.get_height() == 480 and p.get_fps() == 30:
            fmt = str(p.get_format())
            if 'Y12' in fmt:
                dp = depth_profiles.get_stream_profile_by_index(i)
                break
    if dp is None:
        dp = depth_profiles.get_default_video_stream_profile()
    config.enable_stream(dp)
    dpi = dp.as_video_stream_profile()
    print(f"✅ Depth: {dpi.get_width()}x{dpi.get_height()}@{dpi.get_fps()}fps {dpi.get_format()}")

    # IR 流 — 用 320x240 Y10 降低 USB 带宽占用
    ir_ok = False
    ir_w, ir_h = 0, 0
    try:
        ir_profiles = pipeline.get_stream_profile_list(OBSensorType.IR_SENSOR)
        irp = None
        for i in range(ir_profiles.get_count()):
            p = ir_profiles.get_stream_profile_by_index(i).as_video_stream_profile()
            if p.get_width() == 320 and p.get_height() == 240 and p.get_fps() == 30:
                irp = ir_profiles.get_stream_profile_by_index(i)
                break
        if irp is None:
            irp = ir_profiles.get_default_video_stream_profile()
        config.enable_stream(irp)
        iri = irp.as_video_stream_profile()
        ir_w, ir_h = iri.get_width(), iri.get_height()
        ir_ok = True
        print(f"✅ IR: {ir_w}x{ir_h}@{iri.get_fps()}fps {iri.get_format()}")
    except Exception as e:
        print(f"⚠️  IR unavailable: {e}")

    pipeline.start(config)
    print("✅ Pipeline started")

    # Color via OpenCV
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    depth_debug = True

    try:
        while True:
            frames = pipeline.wait_for_frames(1000)
            if frames is None:
                continue

            # --- Depth (via safe accessor) ---
            depth_frame = frames.get_depth_frame()
            if depth_frame is not None:
                try:
                    w, h = depth_frame.get_width(), depth_frame.get_height()
                    raw = depth_frame.get_data()
                    # 获取深度缩放系数（Y11/Y12 等格式需要乘以该系数得到毫米）
                    scale = depth_frame.get_depth_scale()
                    bits = depth_frame.get_pixel_available_bit_size()
                    if len(raw) == w * h * 2:
                        d_u16 = np.frombuffer(raw, dtype=np.uint16).reshape(h, w)
                        # 应用缩放系数得到毫米值
                        d = (d_u16.astype(np.float32) * scale).astype(np.uint16)
                        nz = d[d > 0]
                        if depth_debug:
                            print(f"Depth: {w}x{h} {bits}bit scale={scale:.4f}, "
                                  f"raw[{d_u16.min()}-{d_u16.max()}] "
                                  f"mm[{d.min()}-{d.max()}] "
                                  f"non-zero={np.count_nonzero(d)}")
                            depth_debug = False
                        if len(nz) > 100:
                            lo, hi = int(nz.min()), int(nz.max())
                        else:
                            lo, hi = 500, 8000
                        if hi <= lo:
                            hi = lo + 1
                        norm = ((d.clip(lo, hi) - lo) * 255 // (hi - lo)).astype(np.uint8)
                        cm = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
                        cm[d == 0] = (0, 0, 0)
                        cv2.imshow("Depth", cv2.resize(cm, (cm.shape[1] * 2, cm.shape[0] * 2)))
                except Exception:
                    pass

            # --- IR (via safe accessor, always None on Astra Pro) ---
            if ir_ok:
                try:
                    ir_frame = frames.get_ir_frame()
                    if ir_frame is not None:
                        w, h = ir_frame.get_width(), ir_frame.get_height()
                        raw = ir_frame.get_data()
                        if len(raw) == w * h * 2:
                            ir = np.frombuffer(raw, dtype=np.uint16).reshape(h, w)
                            nz = ir[ir > 0]
                            if len(nz) > 100:
                                lo, hi = int(nz.min()), int(nz.max())
                            else:
                                lo, hi = 0, 65535
                            if hi <= lo:
                                hi = lo + 1
                            norm = ((ir.clip(lo, hi) - lo) * 255 // (hi - lo)).astype(np.uint8)
                            cm = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
                            cv2.imshow("IR", cv2.resize(cm, (cm.shape[1] * 2, cm.shape[0] * 2)))
                except Exception:
                    pass

            # Color (from OpenCV)
            ret, color_bgr = cap.read()
            if ret:
                cv2.imshow("Color", color_bgr)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        pipeline.stop()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    astra_pro_preview()
