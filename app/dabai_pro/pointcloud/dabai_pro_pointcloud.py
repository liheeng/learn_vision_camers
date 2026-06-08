"""
大白 Pro 实时点云预览（pyorbbecsdk）
深度 + IR 双流，按深度着色（无彩色摄像头）。
"""

import cv2
import numpy as np
import open3d as o3d
from pyorbbecsdk import Pipeline, Config, OBSensorType

MIN_DEPTH = 20    # 20mm
MAX_DEPTH = 10000  # 10000mm

# 大白 Pro 640x400 深度相机内参（估算值）
INTRINSICS = np.array([
    [640.0, 0, 400],  # cx 调大，使点云居中
    [0, 640.0, 200],
    [0, 0, 1]
], dtype=np.float64)


def depth_to_pointcloud(depth_mm, intrinsic=INTRINSICS, stride=1):
    """深度图（毫米）转点云 (N, 3)，单位米"""
    h, w = depth_mm.shape
    depth_small = depth_mm[::stride, ::stride]
    sh, sw = depth_small.shape
    fx, fy = intrinsic[0, 0], intrinsic[1, 1]
    cx, cy = intrinsic[0, 2], intrinsic[1, 2]

    u, v = np.meshgrid(np.arange(sw), np.arange(sh))
    u = u.flatten()
    v = v.flatten()

    d = depth_small.flatten().astype(np.float32)
    z = d / 1000.0  # mm → m
    mask = (z > 0.1) & (z < 8.0)

    u_map = u[mask] * stride + stride // 2
    v_map = v[mask] * stride + stride // 2

    x = (u_map - cx) * z[mask] / fx
    y = -(v_map - cy) * z[mask] / fy
    return np.stack([x, y, z[mask]], axis=1)


def process_depth_frame(depth_frame):
    """读取深度帧并返回毫米数据"""
    w, h = depth_frame.get_width(), depth_frame.get_height()
    scale = depth_frame.get_depth_scale()
    data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16).reshape(h, w)
    data = data.astype(np.float32) * scale
    data = np.where((data > MIN_DEPTH) & (data < MAX_DEPTH), data, 0)
    return data.astype(np.uint16)


def main():
    pipeline = Pipeline()
    config = Config()

    # Depth 流
    try:
        profiles = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        dp = profiles.get_default_video_stream_profile()
        print(f"Depth: {dp}")
        config.enable_stream(dp)
    except Exception as e:
        print(f"❌ Depth: {e}")
        return

    pipeline.start(config)
    print("✅ 大白Pro 启动成功")

    # Open3D
    vis = o3d.visualization.Visualizer()
    vis.create_window("DaBai Pro Point Cloud", width=800, height=600)
    opt = vis.get_render_option()
    opt.point_size = 4.0
    opt.background_color = np.array([0.1, 0.1, 0.1])
    pcd = o3d.geometry.PointCloud()
    view_init = False

    cv2.namedWindow("Depth Preview", cv2.WINDOW_NORMAL)
    frame_count = 0

    try:
        while True:
            frames = pipeline.wait_for_frames(100)
            if frames is None:
                continue

            df = frames.get_depth_frame()
            if df is None:
                continue

            depth_mm = process_depth_frame(df)

            frame_count += 1
            if frame_count <= 3:
                nz = np.count_nonzero(depth_mm)
                print(f"Depth: {depth_mm.min()}-{depth_mm.max()}mm nz={nz}")

            # 每 2 帧更新点云
            if frame_count % 2 == 0:
                points = depth_to_pointcloud(depth_mm)
                if len(points) > 0:
                    if frame_count <= 3:
                        print(f"  -> {len(points)} pts  "
                              f"x=[{points[:,0].min():.2f},{points[:,0].max():.2f}]m "
                              f"z=[{points[:,2].min():.2f},{points[:,2].max():.2f}]m")

                    # 按深度着色（近蓝远红）
                    colors = np.zeros((len(points), 3))
                    colors[:, 2] = np.clip(1 - points[:, 2] / 5.0, 0, 1)  # 近蓝
                    colors[:, 0] = np.clip(points[:, 2] / 5.0, 0, 1)      # 远红

                    if view_init:
                        pcd.points = o3d.utility.Vector3dVector(points)
                        pcd.colors = o3d.utility.Vector3dVector(colors)
                        vis.update_geometry(pcd)
                    else:
                        pcd.points = o3d.utility.Vector3dVector(points)
                        pcd.colors = o3d.utility.Vector3dVector(colors)
                        vis.add_geometry(pcd)
                        center = pcd.get_axis_aligned_bounding_box().get_center()
                        vc = vis.get_view_control()
                        vc.set_front([0, 0, 1])
                        vc.set_lookat(center)
                        vc.set_up([0, 1, 0])
                        vc.set_zoom(0.6)
                        view_init = True

                vis.poll_events()
                vis.update_renderer()
                if view_init:
                    vis.get_view_control().rotate(0.3, 0)

            # Depth 预览
            img = cv2.normalize(depth_mm, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            cm = cv2.applyColorMap(img, cv2.COLORMAP_JET)
            cv2.imshow("Depth Preview", cm)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        pipeline.stop()
        vis.destroy_window()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
