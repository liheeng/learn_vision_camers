"""
pyorbbecsdk 预览（--mode depth | ir，默认 depth）

由于 Astra Pro 不支持 Depth + IR 双流同时输出，一次只能选一个。
三窗口同显请使用 OpenNI2: python app/astra_pro/test_astra_pro_with_openni2.py
"""

import cv2
import numpy as np
import sys
from pyorbbecsdk import Context, Pipeline, Config, OBSensorType


def show_frame(win_name, img, scale=2.0):
    """显示图像（自动缩放）"""
    h, w = img.shape[:2]
    cv2.imshow(win_name, cv2.resize(img, (int(w * scale), int(h * scale))))


def normalize_display(data, lo=None, hi=None, colormap=cv2.COLORMAP_JET):
    """自适应归一化 + 伪彩色"""
    nz = data[data > 0]
    if lo is None:
        lo = int(nz.min()) if len(nz) > 100 else 0
    if hi is None:
        hi = int(nz.max()) if len(nz) > 100 else 65535
    if hi <= lo:
        hi = lo + 1
    norm = np.clip((data.astype(np.int32) - lo) * 255 // (hi - lo), 0, 255).astype(np.uint8)
    cm = cv2.applyColorMap(norm, colormap)
    if colormap != cv2.COLORMAP_JET:
        cm[data == 0] = (0, 0, 0)
    return cm


def main():
    # 解析 --mode
    mode = 'depth'
    if '--mode' in sys.argv:
        i = sys.argv.index('--mode')
        if i + 1 < len(sys.argv) and sys.argv[i + 1] in ('depth', 'ir'):
            mode = sys.argv[i + 1]

    ctx = Context()
    devices = ctx.query_devices()
    if devices.get_count() == 0:
        print("❌ No Orbbec device found")
        return

    device = devices.get_device_by_index(0)
    print(f"✅ {device.get_device_info().get_name()}")

    pipeline = Pipeline(device)
    config = Config()

    # Depth + IR 使用同一分辨率 640x480 以确保同步
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
    dw, dh = dpi.get_width(), dpi.get_height()
    print(f"✅ Depth: {dw}x{dh}@{dpi.get_fps()}fps")

    # IR 模式时启用 IR 流（同一分辨率 640x480）
    ir_w = ir_h = 0
    if mode == 'ir':
        try:
            ir_profiles = pipeline.get_stream_profile_list(OBSensorType.IR_SENSOR)
            irp = None
            for i in range(ir_profiles.get_count()):
                p = ir_profiles.get_stream_profile_by_index(i).as_video_stream_profile()
                if p.get_width() == dw and p.get_height() == dh and p.get_fps() == 30:
                    irp = ir_profiles.get_stream_profile_by_index(i)
                    break
            if irp is None:
                irp = ir_profiles.get_default_video_stream_profile()
            config.enable_stream(irp)
            iri = irp.as_video_stream_profile()
            ir_w, ir_h = iri.get_width(), iri.get_height()
            print(f"✅ IR: {ir_w}x{ir_h}@{iri.get_fps()}fps")
        except Exception as e:
            print(f"⚠️  IR: {e}")

    pipeline.start(config)
    print("✅ Pipeline started")

    # Color via OpenCV
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    try:
        while True:
            frames = pipeline.wait_for_frames(1000)
            if frames is None:
                continue

            if mode == 'depth':
                # ---- Depth 模式 ----
                df = frames.get_depth_frame()
                if df is not None:
                    try:
                        w, h = df.get_width(), df.get_height()
                        raw = df.get_data()
                        if len(raw) == w * h * 2:
                            d = np.frombuffer(raw, dtype=np.uint16).reshape(h, w)
                            d = (d.astype(np.float32) * df.get_depth_scale()).astype(np.uint16)
                            cm = normalize_display(d, lo=500, hi=8000)
                            cm[d == 0] = (0, 0, 0)
                            show_frame("Depth", cm)
                    except Exception:
                        pass

            else:
                # ---- IR 模式 ----
                # 遍历 FrameSet 中的帧，找数据量匹配 IR 分辨率的帧
                for fi in range(frames.get_frame_count()):
                    try:
                        f = frames.get_frame_by_index(fi)
                        if f is None:
                            continue
                        raw = f.get_data()
                        # Depth 和 IR 都是 640x480 16bit, 数据大小一样，无法区分
                        # 但深度值范围极小 (0-50)，IR 值范围大 (0-65535)，
                        # 所以 IR 模式的 FrameSet 中第一个帧通常就是 IR 数据
                        if len(raw) == ir_w * ir_h * 2:
                            ir = np.frombuffer(raw, dtype=np.uint16).reshape(ir_h, ir_w)
                            # 如果值范围 > 200，很可能是 IR 而非 Depth
                            if ir.max() > 200:
                                # 使用百分位裁剪，避免低值纯蓝淹没细节
                                nz = ir[ir > 0]
                                if len(nz) > 100:
                                    lo = int(np.percentile(nz, 5))
                                    hi = int(np.percentile(nz, 95))
                                else:
                                    lo, hi = 0, 65535
                                if hi <= lo:
                                    hi = lo + 1
                                norm = np.clip((ir.astype(np.int32) - lo) * 255 // (hi - lo),
                                               0, 255).astype(np.uint8)
                                cm = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
                                show_frame("IR", cm)
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
    main()
