import openni
import cv2
import numpy as np
import open3d as o3d

# ===================== 初始化 =====================
openni.initialize()
print("✅ OpenNI2 初始化成功")

try:
    # 打开相机
    device = openni.Device.open_any()
    print(f"✅ 相机已连接: {device.get_device_info().name}")

    # 创建数据流
    depth_stream = device.create_depth_stream()
    color_stream = device.create_color_stream()

    # 配置分辨率 640x480
    depth_stream.set_video_mode(openni.VideoMode(
        pixel_format=openni.PIXEL_FORMAT_DEPTH_1_MM,
        width=640, height=480, fps=30
    ))
    color_stream.set_video_mode(openni.VideoMode(
        pixel_format=openni.PIXEL_FORMAT_RGB888,
        width=640, height=480, fps=30
    ))

    # 启动 + 图像对齐
    depth_stream.start()
    color_stream.start()
    device.set_image_registration_mode(openni.IMAGE_REGISTRATION_DEPTH_TO_COLOR)

    # 相机内参（大白Pro默认）
    intrinsic = o3d.camera.PinholeCameraIntrinsic(640,480, 570,570,320,240)
    vis = o3d.visualization.Visualizer()
    vis.create_window("点云")
    pcd = o3d.geometry.PointCloud()
    first_frame = True

    # ===================== 主循环 =====================
    while True:
        # 读取帧
        d_frame = depth_stream.read_frame()
        c_frame = color_stream.read_frame()

        # 格式转换
        depth = np.array(d_frame.get_buffer_as_uint16()).reshape(480,640)
        color = np.array(c_frame.get_buffer_as_uint8()).reshape(480,640,3)
        color_bgr = cv2.cvtColor(color, cv2.COLOR_RGB2BGR)

        # 深度图可视化
        depth_show = cv2.normalize(depth, None,0,255,cv2.NORM_MINMAX,dtype=cv2.CV_8U)
        depth_show = cv2.applyColorMap(depth_show, cv2.COLORMAP_JET)

        # 点云生成
        depth_m = depth.astype(np.float32)/1000.0
        rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
            o3d.geometry.Image(color), o3d.geometry.Image(depth_m),
            depth_scale=1.0, depth_trunc=10.0, convert_rgb_to_intensity=False
        )
        new_pcd = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd, intrinsic)
        new_pcd.transform([[1,0,0,0],[0,-1,0,0],[0,0,-1,0],[0,0,0,1]])

        # 更新点云窗口
        if first_frame:
            vis.add_geometry(new_pcd)
            first_frame=False
        else:
            vis.remove_geometry(pcd)
            vis.add_geometry(new_pcd)
        pcd = new_pcd
        vis.poll_events()
        vis.update_renderer()

        # 显示图像
        cv2.imshow("深度图", depth_show)
        cv2.imshow("彩色图", color_bgr)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    # 释放资源
    depth_stream.stop()
    color_stream.stop()
    openni.shutdown()
    cv2.destroyAllWindows()
    vis.destroy_window()
    print("✅ 程序安全退出")
