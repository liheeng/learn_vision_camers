import cv2
import numpy as np
import open3d as o3d
from openni import openni2


def get_astra_intrinsics():
    """Astra Pro 官方深度相机内参（640x480）"""
    return np.array([
        [525.0, 0, 319.5],
        [0, 525.0, 239.5],
        [0, 0, 1]
    ], dtype=np.float32)


def depth_to_points(depth_data, intrinsic, depth_scale=1000.0):
    """深度图转3D点云"""
    h, w = depth_data.shape
    fx, fy = intrinsic[0, 0], intrinsic[1, 1]
    cx, cy = intrinsic[0, 2], intrinsic[1, 2]

    # 生成像素坐标网格
    u, v = np.meshgrid(np.arange(w), np.arange(h))
    u = u.flatten()
    v = v.flatten()

    z = depth_data.flatten().astype(np.float32) / depth_scale

    # 过滤无效点（0 和 65535），保留 0.3~8m 的有效范围
    valid_mask = (z > 0.3) & (z < 8.0)

    # 计算3D坐标（不翻转y轴，保持Open3D默认坐标系）
    x = (u[valid_mask] - cx) * z[valid_mask] / fx
    y = (v[valid_mask] - cy) * z[valid_mask] / fy
    return np.stack([x, y, z[valid_mask]], axis=1)


def main():
    # 初始化OpenNI
    openni2.initialize()
    dev = openni2.Device.open_any()
    print("✅ 设备连接成功:", dev.get_device_info())

    # 启动深度流（最简模式）
    depth_stream = dev.create_depth_stream()
    depth_stream.start()
    print("✅ 深度流启动成功")

    # 点云可视化
    vis = o3d.visualization.Visualizer()
    vis.create_window("Astra Pro 完整点云", width=800, height=600)
    pcd = o3d.geometry.PointCloud()

    view_initialized = False

    byte_order_swapped = False  # 是否检测到需要字节交换

    try:
        while True:
            # 读取深度帧
            frame = depth_stream.read_frame()
            raw_u16 = np.array(frame.get_buffer_as_uint16()).reshape(480, 640)

            # 自动检测字节序：比较原始和交换后的有效点数量
            # 有效深度在 600~8000 (mm) 之间
            valid_orig = np.count_nonzero((raw_u16 > 600) & (raw_u16 < 8000))
            valid_swap = np.count_nonzero((raw_u16.byteswap() > 600) & (raw_u16.byteswap() < 8000))

            # 首次运行时选择正确字节序
            if not byte_order_swapped and valid_swap > valid_orig * 1.5:
                print(f"🔄 检测到字节序需交换: orig_valid={valid_orig}, swap_valid={valid_swap}")
                byte_order_swapped = True

            depth_data = raw_u16.byteswap() if byte_order_swapped else raw_u16

            # 调试：打印深度数据分布
            nz = np.count_nonzero(depth_data)
            valid_count = np.count_nonzero((depth_data > 300) & (depth_data < 8000))
            print(f"深度数据: min={depth_data.min()}, max={depth_data.max()}, "
                  f"non-zero={nz}, valid={valid_count}, swapped={byte_order_swapped}")

            # 生成点云
            points = depth_to_points(depth_data, get_astra_intrinsics())
            if len(points) == 0:
                print("⚠️  无有效点")
                continue

            # 打印点云范围
            print(f"点云: {len(points)} 点, "
                  f"x=[{points[:,0].min():.2f},{points[:,0].max():.2f}], "
                  f"y=[{points[:,1].min():.2f},{points[:,1].max():.2f}], "
                  f"z=[{points[:,2].min():.2f},{points[:,2].max():.2f}]")

            # 显示深度图（伪彩色，反转颜色让近处更亮）
            depth_vis = cv2.normalize(depth_data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
            depth_vis = cv2.applyColorMap(255 - depth_vis, cv2.COLORMAP_JET)
            cv2.imshow("Depth Map", depth_vis)

            # 更新点云：必须先设置 points，再设置 colors（确保数量匹配）
            pcd.points = o3d.utility.Vector3dVector(points)
            colors = np.zeros((len(points), 3))
            colors[:, 0] = np.clip(points[:, 2] / 8.0, 0, 1)  # 远红
            colors[:, 2] = 1 - np.clip(points[:, 2] / 8.0, 0, 1)  # 近蓝
            pcd.colors = o3d.utility.Vector3dVector(colors)

            vis.clear_geometries()
            vis.add_geometry(pcd)
            vis.poll_events()
            vis.update_renderer()

            # 首次添加几何体后再设置视角（否则会被重置）
            if not view_initialized:
                view_control = vis.get_view_control()
                view_control.set_front([0, 0, -1])
                view_control.set_lookat([0, 0, 1])
                view_control.set_up([0, -1, 0])
                view_initialized = True

            # 按q退出
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        depth_stream.stop()
        openni2.unload()
        vis.destroy_window()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
