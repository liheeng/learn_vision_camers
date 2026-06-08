"""
pyorbbecsdk 预览（--mode depth | ir | both，默认 depth）

Depth + IR 无法硬件同步，FrameSet 交替到达。both 模式各自独立更新窗口。
三窗口完美同显请使用 OpenNI2: python app/astra_pro/test_astra_pro_with_openni2.py
"""

import cv2
import numpy as np
import sys
from pyorbbecsdk import Context, Pipeline, Config, OBSensorType


def show_frame(win_name, img, scale=1.0):
    """显示图像（自动缩放）"""
    h, w = img.shape[:2]
    cv2.imshow(win_name, cv2.resize(img, (int(w * scale), int(h * scale))))


def show_ir(ir_data):
    """显示 IR 帧（百分位裁剪 + JET 伪彩色）"""
    nz = ir_data[ir_data > 0]
    if len(nz) > 100:
        lo = int(np.percentile(nz, 5))
        hi = int(np.percentile(nz, 95))
    else:
        lo, hi = 0, 65535
    if hi <= lo:
        hi = lo + 1
    norm = np.clip((ir_data.astype(np.int32) - lo) * 255 // (hi - lo),
                   0, 255).astype(np.uint8)
    cm = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
    show_frame("IR", cm)


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
    mode = 'both'
    if '--mode' in sys.argv:
        i = sys.argv.index('--mode')
        if i + 1 < len(sys.argv) and sys.argv[i + 1] in ('depth', 'ir', 'both'):
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

    # IR / both 模式时启用 IR 流（同一分辨率 640x480）
    ir_w = ir_h = 0
    if mode in ('ir', 'both'):
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

            # ---- Depth 窗口（所有模式都尝试更新） ----
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

            # ---- IR 窗口（ir / both 模式尝试更新） ----
            if mode in ('ir', 'both'):
                # 先试 get_ir_frame()
                irf = frames.get_ir_frame()
                if irf is not None:
                    try:
                        w, h = irf.get_width(), irf.get_height()
                        raw = irf.get_data()
                        if len(raw) == w * h * 2:
                            ir = np.frombuffer(raw, dtype=np.uint16).reshape(h, w)
                            if ir.max() > 200:
                                show_ir(ir)
                    except Exception:
                        pass
                else:
                    # 回退：遍历 FrameSet 找 IR 数据
                    for fi in range(frames.get_frame_count()):
                        try:
                            f = frames.get_frame_by_index(fi)
                            if f is None:
                                continue
                            raw = f.get_data()
                            if len(raw) == ir_w * ir_h * 2:
                                ir = np.frombuffer(raw, dtype=np.uint16).reshape(ir_h, ir_w)
                                if ir.max() > 200:
                                    show_ir(ir)
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
