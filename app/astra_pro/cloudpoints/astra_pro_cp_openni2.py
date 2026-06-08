import cv2
import numpy as np
import open3d as o3d
from openni import openni2


def depth_to_pointcloud(depth_data, intrinsic_matrix, depth_scale=1000.0):
    """
    深度图转点云核心算法
    :param depth_data: 16位深度图 (H, W)
    :param intrinsic_matrix: 相机内参矩阵 (3,3)
    :param depth_scale: 深度缩放因子（毫米转米）
    :return: 点云数据 (N, 3)
    """
    h, w = depth_data.shape
    fx, fy = intrinsic_matrix[0, 0], intrinsic_matrix[1, 1]
    cx, cy = intrinsic_matrix[0, 2], intrinsic_matrix[1, 2]
    
    # 生成像素坐标网格
    u, v = np.meshgrid(np.arange(w), np.arange(h))
    u = u.flatten()
    v = v.flatten()
    
    # 获取深度值并过滤无效点
    z = depth_data.flatten() / depth_scale
    valid_mask = (z > 0) & (z < 5.0)  # 过滤0-5米
    
    # 计算3D坐标（核心公式）
    x = (u - cx) * z / fx
    y = (v - cy) * z / fy
    
    # 组合点云
    points = np.vstack((x, y, z)).T
    return points[valid_mask]


def main():
    # 1. 初始化OpenNI2
    openni2.initialize()
    
    # 2. 打开相机
    dev = openni2.Device.open_any()
    print(f"设备信息: {dev.get_device_info()}")
    
    # 3. 启用深度流（OpenNI2）和彩色流（OpenCV）
    try:
        dev.set_image_registration_mode(True)
    except Exception:
        print("Warning: image registration mode not supported on this device")
    depth_stream = dev.create_depth_stream()
    depth_stream.start()
    # 使用 OpenCV 读取彩色流，避免 OpenNI2 color stream 阻塞问题
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        # 自动探测可用摄像头
        cap = None
        for idx in range(0, 4):
            try:
                c = cv2.VideoCapture(idx)
                if c.isOpened():
                    cap = c
                    print(f"Auto-using OpenCV color device index: {idx}")
                    break
            except Exception:
                continue
    if cap is None:
        raise RuntimeError("无法打开彩色摄像头")
    
    # 4. 获取相机内参（关键！影响点云精度）
    intrinsic = np.array([[570.3, 0, 320],  # fx, 0, cx
                          [0, 570.3, 240],  # 0, fy, cy
                          [0, 0, 1]])       # 0, 0, 1
    
    # 5. 可视化准备
    vis = o3d.visualization.Visualizer()
    vis.create_window("Astra Pro Point Cloud (OpenNI2)")
    pcd = o3d.geometry.PointCloud()
    
    try:
        while True:
            # 6. 读取深度帧（OpenNI2）和彩色帧（OpenCV）
            depth_frame = depth_stream.read_frame()
            ret, color_frame_bgr = cap.read()
            if not ret:
                print("Warning: failed to grab color frame")
                continue
            
            # 7. 转换为numpy数组
            depth_data = np.array(depth_frame.get_buffer_as_uint16()).reshape(480, 640)
            color_frame_bgr = cv2.flip(color_frame_bgr, 1)
            color_data_rgb = cv2.cvtColor(color_frame_bgr, cv2.COLOR_BGR2RGB)
            
            # 8. 生成点云
            points = depth_to_pointcloud(depth_data, intrinsic)
            colors = color_data_rgb.reshape(-1, 3)[(depth_data.flatten() > 0) & (depth_data.flatten() < 5000)] / 255.0
            
            # 9. 显示
            pcd.points = o3d.utility.Vector3dVector(points)
            pcd.colors = o3d.utility.Vector3dVector(colors)
            
            vis.clear_geometries()
            vis.add_geometry(pcd)
            vis.poll_events()
            vis.update_renderer()
            
            cv2.imshow("Color", color_frame_bgr)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        # 10. 资源释放
        depth_stream.stop()
        cap.release()
        openni2.unload()
        vis.destroy_window()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()