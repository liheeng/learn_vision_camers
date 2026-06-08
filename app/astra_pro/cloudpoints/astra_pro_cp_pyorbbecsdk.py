"""
pyorbbecsdk 实时点云预览
基于 test_astra_pro_with_pyorbbecsdk.py，用 Open3D 显示点云。
"""

import cv2
import numpy as np
import open3d as o3d
from pyorbbecsdk import Context, Pipeline, Config, OBSensorType

# Astra Pro 640x480 深度相机内参（与 OpenNI2 版一致）
INTRINSICS = np.array([
    [525.0, 0, 319.5],
    [0, 525.0, 239.5],
    [0, 0, 1]
], dtype=np.float64)


def depth_to_pointcloud(depth_raw, intrinsic=INTRINSICS, stride=1):
    """深度图转点云 (N, 3)。自动适配 pyorbbecsdk（小值）和 OpenNI2（大值）"""
    h, w = depth_raw.shape
    depth_small = depth_raw[::stride, ::stride]
    sh, sw = depth_small.shape
    fx, fy = intrinsic[0, 0], intrinsic[1, 1]
    cx, cy = intrinsic[0, 2], intrinsic[1, 2]

    u, v = np.meshgrid(np.arange(sw), np.arange(sh))
    u = u.flatten()
    v = v.flatten()

    d = depth_small.flatten().astype(np.float32)
    # 自动判断：小值（pyorbbecsdk）直接使用，大值（OpenNI2 mm）转米
    d_max = d.max()
    if d_max > 500:
        z = d / 1000.0  # mm → m
        mask = (z > 0.3) & (z < 3.0)
    else:
        z = d / d_max * 3.0 if d_max > 0 else d  # 归一化到 0-3m
        mask = z > 0.01

    u_map = u[mask] * stride + stride // 2
    v_map = v[mask] * stride + stride // 2

    x = (u_map - cx) * z[mask] / fx
    y = -(v_map - cy) * z[mask] / fy
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

    # Open3D
    vis = o3d.visualization.Visualizer()
    vis.create_window("Astra Pro Point Cloud (pyorbbecsdk)", width=800, height=600)
    opt = vis.get_render_option()
    opt.point_size = 5.0
    opt.background_color = np.array([0.1, 0.1, 0.1])
    pcd = o3d.geometry.PointCloud()
    view_init = False

    cv2.namedWindow("Depth Preview", cv2.WINDOW_NORMAL)
    frame_count = 0

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
                d_u16 = np.fliplr(d_u16)  # 水平翻转，对齐彩色摄像头
                scale = df.get_depth_scale()
                raw_max = float(d_u16.max())
                if raw_max > 500:
                    depth_mm = (d_u16.astype(np.float32) * scale).astype(np.uint16)
                else:
                    # 原始值过小（非 mm 单位），直接当作相对深度使用
                    depth_mm = d_u16
            except Exception:
                continue

            frame_count += 1
            if frame_count <= 3:
                print(f"Depth: min={depth_mm.min()} max={depth_mm.max()} "
                      f"nz={np.count_nonzero(depth_mm)}")

            # 每 2 帧更新点云
            if frame_count % 2 == 0:
                points = depth_to_pointcloud(depth_mm)
                if len(points) > 0:
                    if frame_count <= 3:
                        print(f"  -> {len(points)} points  "
                              f"x=[{points[:,0].min():.2f},{points[:,0].max():.2f}]m "
                              f"y=[{points[:,1].min():.2f},{points[:,1].max():.2f}]m "
                              f"z=[{points[:,2].min():.2f},{points[:,2].max():.2f}]m")

                    # 彩色着色
                    pc_colors = None
                    ret, color_bgr = cap.read()
                    if ret:
                        color_bgr = cv2.flip(color_bgr, 1)
                        color_rgb = cv2.cvtColor(color_bgr, cv2.COLOR_BGR2RGB)
                        col = color_rgb.reshape(-1, 3).astype(np.float32) / 255.0
                        mask = (depth_mm.flatten() > 300) & (depth_mm.flatten() < 3000)
                        col = col[mask]
                        if len(col) == len(points):
                            pc_colors = o3d.utility.Vector3dVector(col)

                    if view_init:
                        pcd.points = o3d.utility.Vector3dVector(points)
                        if pc_colors is not None:
                            pcd.colors = pc_colors
                        vis.update_geometry(pcd)
                    else:
                        pcd.points = o3d.utility.Vector3dVector(points)
                        if pc_colors is not None:
                            pcd.colors = pc_colors
                        vis.add_geometry(pcd)
                        bounds = pcd.get_axis_aligned_bounding_box()
                        center = bounds.get_center()
                        vc = vis.get_view_control()
                        vc.set_front([0, 0, 1])
                        vc.set_lookat(center)
                        vc.set_up([0, 1, 0])
                        vc.set_zoom(0.5)
                        view_init = True

                vis.poll_events()
                vis.update_renderer()
                if view_init:
                    ctr = vis.get_view_control()
                    ctr.rotate(0.3, 0)

            # ---- 深度图预览（自适应） ----
            d_disp = depth_mm.astype(np.float32)
            nz = d_disp[d_disp > 0]
            if len(nz) > 100:
                lo, hi = float(nz.min()), float(nz.max())
            else:
                lo, hi = 0.0, 50.0
            if hi <= lo:
                hi = lo + 1.0
            norm = np.clip((d_disp - lo) * 255.0 // (hi - lo), 0, 255).astype(np.uint8)
            cm = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
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
