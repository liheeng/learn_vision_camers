from pyorbbecsdk import Pipeline, Config, OBFormat, OBSensorType
import cv2
import numpy as np


def main():
    # 1. 初始化SDK管道（大白Pro专用）
    pipeline = Pipeline()
    config = Config()

    # ===================== 大白Pro 核心配置 =====================
    # 仅支持：深度流 + IR流，无彩色流！
    # 分辨率：640×400 @30fps（大白Pro原生分辨率）
    
    # 获取并启用 深度流，优先使用默认 profile
    try:
        depth_profile_list = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        try:
            depth_profile = depth_profile_list.get_default_video_stream_profile()
        except Exception:
            depth_profile = depth_profile_list.get_video_stream_profile(640, 400, OBFormat.Y16, 30)
        config.enable_stream(depth_profile)
        print("✅ Depth stream enabled")
    except Exception as e:
        print(f"❌ Depth stream enable failed: {e}")
        return

    # 获取并启用 IR流，优先使用默认 profile
    try:
        ir_profile_list = pipeline.get_stream_profile_list(OBSensorType.IR_SENSOR)
        try:
            ir_profile = ir_profile_list.get_default_video_stream_profile()
        except Exception:
            ir_profile = ir_profile_list.get_video_stream_profile(640, 400, OBFormat.Y16, 30)
        config.enable_stream(ir_profile)
        print("✅ IR stream enabled")
    except Exception as e:
        print(f"❌ IR stream enable failed: {e}")
        return

    # 2. 启动相机
    try:
        pipeline.start(config)
        print("✅ 大白Pro 启动成功！深度 + IR 流已开启")
    except Exception as e:
        print(f"❌ 启动失败：{e}")
        return

    # 3. 循环读取帧
    print("按 q 退出")
    while True:
        # 等待获取一帧数据（同步深度+IR）
        frames = pipeline.wait_for_frames(100)
        if frames is None:
            continue

        # ============= 读取深度帧 =============
        depth_frame = frames.get_depth_frame()
        if depth_frame:
            # 转换为numpy数组
            depth_data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16)
            depth_data = depth_data.reshape(400, 640)
            # 深度图可视化（归一化+伪彩色）
            depth_show = cv2.normalize(depth_data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
            depth_show = cv2.applyColorMap(depth_show, cv2.COLORMAP_JET)
            cv2.imshow("DaBai Pro 深度图", depth_show)

        # ============= 读取IR红外帧 =============
        ir_frame = frames.get_ir_frame()
        if ir_frame:
            ir_data = np.frombuffer(ir_frame.get_data(), dtype=np.uint16)
            ir_data = ir_data.reshape(400, 640)
            # IR图可视化
            ir_show = cv2.normalize(ir_data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
            cv2.imshow("DaBai Pro IR红外图", ir_show)

        # 退出按键
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 4. 释放资源
    pipeline.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()