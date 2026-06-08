"""
pyorbbecsdk 实时点云预览
基于 test_astra_pro_with_pyorbbecsdk.py，用 Open3D 显示点云。
"""

import cv2
import numpy as np
import open3d as o3d
from pyorbbecsdk import Context, Pipeline, Config, OBSensorType

# Astra Pro 640x480 深度相机内参
INTRINSICS = np.array([
    [570.3, 0, 320],
    [0, 570.3, 240],
    [0, 0, 1]
], dtype=np.float64)


def depth_to_pointcloud(depth_mm, intrinsic=INTRINSICS, stride=2):
    """深度图（毫米）转点云 (N, 3)，单位米。stride=2 表示每 2 像素取 1 个，降低点数"""
    h, w = depth_mm.shape
    # 降采样
    depth_small = depth_mm[::stride, ::stride]
    sh, sw = depth_small.shape
    fx, fy = intrinsic[0, 0], intrinsic[1, 1]
    cx, cy = intrinsic[0, 2], intrinsic[1, 2]

    u, v = np.meshgrid(np.arange(sw), np.arange(sh))
    u = u.flatten()
    v = v.flatten()

    z = depth_small.flatten().astype(np.float32) / 1000.0
    mask = (z > 0.3) & (z < 5.0)

    # 像素坐标映射回原始分辨率
    u_map = (u[mask] * stride + stride // 2)
    v_map = (v[mask] * stride + stride // 2)

    x = (u_map - cx) * z[mask] / fx
    y = (v_map - cy) * z[mask] / fy
    return np.stack([x, y, z[mask]], axis=1)


def main():
    ctx = Context()
    devices = ctx.query_devices()
    if devices.get_count() == 0:
        print("❌ No Orbbec device found")
        return

    device = devices.get_device_by_index(0)
    print(f"✅ {device.get_device_info().get_name()}")

    pipeline = Pipeline(device)
    config = Config()

    # Depth 640x480 Y12
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
    print(f"✅ Depth: {dpi.get_width()}x{dpi.get_height()}@{dpi.get_fps()}fps")

    pipeline.start(config)
    print("✅ Pipeline started")

    # Color via OpenCV（用于点云着色）
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Open3D 可视化
    vis = o3d.visualization.Visualizer()
    vis.create_window("Astra Pro Point Cloud (pyorbbecsdk)", width=800, height=600)
    pcd = o3d.geometry.PointCloud()
    view_initialized = False

    # 跳帧：每 3 帧更新一次点云（提升性能）
    frame_skip = 0
    cv2.namedWindow("Depth Preview", cv2.WINDOW_NORMAL)

    try:
        while True:
            frames = pipeline.wait_for_frames(1000)
            if frames is None:
                continue

            # ---- 读取深度帧 ----
            df = frames.get_depth_frame()
            if df is None:
                continue

            try:
                w, h = df.get_width(), df.get_height()
                raw = df.get_data()
                if len(raw) != w * h * 2:
                    continue

                d_u16 = np.frombuffer(raw, dtype=np.uint16).reshape(h, w)
                depth_mm = (d_u16.astype(np.float32) * df.get_depth_scale()).astype(np.uint16)
            except Exception:
                continue

            frame_skip += 1
            update_pc = (frame_skip % 3 == 0)

            # ---- 点云（跳帧更新） ----
            if update_pc:
                if frame_skip <= 6:
                    print(f"Depth: min={depth_mm.min()} max={depth_mm.max()} "
                          f"nz={np.count_nonzero(depth_mm)}")
                    points = depth_to_pointcloud(depth_mm)
                    print(f"  -> {len(points)} points")
                else:
                    points = depth_to_pointcloud(depth_mm)
                if len(points) > 0:
                    # ---- 从彩色图取色 ----
                    ret, color_bgr = cap.read()
                    if ret:
                        color_small = cv2.resize(color_bgr, (320, 240))
                        color_rgb = cv2.cvtColor(color_small, cv2.COLOR_BGR2RGB)
                        colors = color_rgb.reshape(-1, 3).astype(np.float32) / 255.0
                        depth_small = depth_mm[::2, ::2]
                        mask = (depth_small.flatten() > 300) & (depth_small.flatten() < 5000)
                        colors = colors[mask]
                        if len(colors) == len(points):
                            pcd.colors = o3d.utility.Vector3dVector(colors)

                    # ---- 更新 Open3D ----
                    pcd.points = o3d.utility.Vector3dVector(points)
                    vis.clear_geometries()
                    vis.add_geometry(pcd)

                vis.poll_events()
                vis.update_renderer()

                if not view_initialized and len(points) > 0:
                    vc = vis.get_view_control()
                    vc.set_front([0, 0, -1])
                    vc.set_lookat([0, 0, 1])
                    vc.set_up([0, -1, 0])
                    view_initialized = True

            # ---- 深度图预览（每帧都更新） ----
            cm = cv2.applyColorMap(
                np.clip((depth_mm.astype(np.int32) - 500) * 255 // 7500, 0, 255).astype(np.uint8),
                cv2.COLORMAP_JET)
            cm[depth_mm == 0] = (0, 0, 0)
            cv2.imshow("Depth Preview", cv2.resize(cm, (640, 480)))

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        pipeline.stop()
        cap.release()
        vis.destroy_window()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
