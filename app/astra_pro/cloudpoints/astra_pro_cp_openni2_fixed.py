"""
Astra Pro 点云 — 基于 OpenNI2（深度数据正确）
"""

import cv2
import numpy as np
import open3d as o3d
from openni import openni2

# Astra Pro 640x480 深度相机内参
INTRINSICS = np.array([
    [525.0, 0, 319.5],
    [0, 525.0, 239.5],
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

    z = depth_small.flatten().astype(np.float32) / 1000.0
    mask = (z > 0.3) & (z < 3.0)  # 室内场景聚焦 3m 内

    u_map = u[mask] * stride + stride // 2
    v_map = v[mask] * stride + stride // 2

    x = (u_map - cx) * z[mask] / fx
    y = -(v_map - cy) * z[mask] / fy  # 取反：图像顶部 → 正 y（上方）
    return np.stack([x, y, z[mask]], axis=1)


def main():
    openni2.initialize()
    dev = openni2.Device.open_any()
    print(f"✅ {dev.get_device_info()}")

    # 深度流
    depth_stream = dev.create_depth_stream()
    depth_stream.start()
    print("✅ Depth stream started")

    # Color via OpenCV
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Open3D
    vis = o3d.visualization.Visualizer()
    vis.create_window("Astra Pro Point Cloud (OpenNI2)", width=800, height=600)
    opt = vis.get_render_option()
    opt.point_size = 5.0
    opt.background_color = np.array([0.1, 0.1, 0.1])
    pcd = o3d.geometry.PointCloud()
    view_init = False

    cv2.namedWindow("Depth Preview", cv2.WINDOW_NORMAL)
    frame_count = 0

    try:
        while True:
            # 读取深度帧 — 直接用 uint16 读取，更准确
            dframe = depth_stream.read_frame()
            raw_u16 = np.array(dframe.get_buffer_as_uint16()).reshape(480, 640)
            # 自动检测字节序
            raw_swp = raw_u16.byteswap()
            nz_orig = np.count_nonzero((raw_u16 > 300) & (raw_u16 < 5000))
            nz_swp = np.count_nonzero((raw_swp > 300) & (raw_swp < 5000))
            depth_mm = raw_swp if nz_swp > nz_orig else raw_u16

            frame_count += 1
            if frame_count <= 3:
                print(f"Depth: min={depth_mm.min()} max={depth_mm.max()} "
                      f"nz={np.count_nonzero(depth_mm)}")

            # 每 2 帧更新一次点云
            if frame_count % 2 == 0:
                points = depth_to_pointcloud(depth_mm)
                if len(points) > 0:
                    if frame_count <= 3:
                        print(f"  -> {len(points)} points")
                        print(f"  x=[{points[:,0].min():.2f},{points[:,0].max():.2f}]m "
                              f"y=[{points[:,1].min():.2f},{points[:,1].max():.2f}]m "
                              f"z=[{points[:,2].min():.2f},{points[:,2].max():.2f}]m")

                    # 彩色着色
                    pc_colors = None
                    ret, color_bgr = cap.read()
                    if ret:
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

            # 深度预览
            norm = np.clip((depth_mm.astype(np.int32) - 500) * 255 // 2500, 0, 255).astype(np.uint8)
            cm = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
            cm[depth_mm == 0] = (0, 0, 0)
            cv2.imshow("Depth Preview", cv2.resize(cm, (640, 480)))

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        depth_stream.stop()
        openni2.unload()
        cap.release()
        vis.destroy_window()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
