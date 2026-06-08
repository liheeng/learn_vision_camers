"""
大白 Pro 深度 + IR 双流预览
参考 dabai_pro_depth_viewer.py 和 dabai_pro_infrared_viewer.py 修正。
"""

import cv2
import numpy as np
from pyorbbecsdk import Pipeline, Config, OBFormat, OBSensorType

MIN_DEPTH = 20    # 20mm
MAX_DEPTH = 10000  # 10000mm


def process_depth_frame(depth_frame):
    """处理深度帧：缩放+过滤+归一化+伪彩色"""
    width = depth_frame.get_width()
    height = depth_frame.get_height()
    scale = depth_frame.get_depth_scale()

    data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16).reshape(height, width)
    data = data.astype(np.float32) * scale
    data = np.where((data > MIN_DEPTH) & (data < MAX_DEPTH), data, 0)
    data = data.astype(np.uint16)

    # 归一化 + 伪彩色
    img = cv2.normalize(data, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    img = cv2.applyColorMap(img, cv2.COLORMAP_JET)
    return img


def process_ir_frame(ir_frame):
    """处理 IR 帧：兼容 Y8 / MJPG / Y16 格式"""
    width = ir_frame.get_width()
    height = ir_frame.get_height()
    raw = ir_frame.get_data()
    fmt = ir_frame.get_format()

    if fmt == OBFormat.Y8:
        data = np.frombuffer(raw, dtype=np.uint8).reshape(height, width, 1)
        dtype = cv2.CV_8U
        max_val = 255
    elif fmt == OBFormat.MJPG:
        data = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if data is None:
            return None
        dtype = cv2.CV_8U
        max_val = 255
    else:  # Y16 / 默认
        data = np.frombuffer(raw, dtype=np.uint16).reshape(height, width, 1)
        dtype = cv2.CV_16U
        max_val = 65535

    cv2.normalize(data, data, 0, max_val, cv2.NORM_MINMAX, dtype=dtype)
    img = cv2.cvtColor(data.astype(np.uint8 if max_val == 255 else np.uint16), cv2.COLOR_GRAY2RGB)
    return img


def main():
    pipeline = Pipeline()
    config = Config()

    # --- Depth 流 ---
    try:
        profiles = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        dp = profiles.get_default_video_stream_profile()
        print(f"Depth profile: {dp}")
        config.enable_stream(dp)
    except Exception as e:
        print(f"❌ Depth: {e}")
        return

    # --- IR 流 ---
    try:
        profiles = pipeline.get_stream_profile_list(OBSensorType.IR_SENSOR)
        ip = profiles.get_default_video_stream_profile()
        print(f"IR profile: {ip}")
        config.enable_stream(ip)
    except Exception as e:
        print(f"❌ IR: {e}")
        return

    pipeline.start(config)
    print("✅ 大白Pro 启动成功")

    while True:
        frames = pipeline.wait_for_frames(100)
        if frames is None:
            continue

        # Depth
        df = frames.get_depth_frame()
        if df:
            img = process_depth_frame(df)
            cv2.imshow("DaBai Pro Depth", img)

        # IR
        irf = frames.get_ir_frame()
        if irf:
            img = process_ir_frame(irf)
            if img is not None:
                cv2.imshow("DaBai Pro IR", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    pipeline.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()