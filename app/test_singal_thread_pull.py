from openni import openni2
import numpy as np
import cv2
import time


def simple_astra_pro_capture():
    # 初始化 OpenNI2
    openni2.initialize()
    dev = openni2.Device.open_any()
    
    # 启动深度和IR流
    depth_stream = dev.create_depth_stream()
    depth_stream.start()
    ir_stream = dev.create_ir_stream()
    ir_stream.start()
    
    # 启动 UVC 彩色流
    cap = cv2.VideoCapture("/dev/video0")  # 替换为实际的设备路径
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUYV'))
    
    try:
        while True:
            # 获取深度帧
            depth_frame = depth_stream.read_frame()
            depth_data = np.array(depth_frame.get_buffer_as_uint16()).reshape(480, 640)
            
            # 获取IR帧
            ir_frame = ir_stream.read_frame()
            ir_data = np.array(ir_frame.get_buffer_as_uint16()).reshape(480, 640) / 65535.0
            
            # 获取彩色帧
            ret, color_bgr = cap.read()
            if not ret:
                print("⚠️  无法获取彩色帧")
                time.sleep(0.1)
                continue
            
            # 显示
            cv2.imshow("Depth", cv2.normalize(depth_data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U))
            cv2.imshow("IR", (ir_data * 255).astype(np.uint8))
            cv2.imshow("Color", color_bgr)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        depth_stream.stop()
        ir_stream.stop()
        openni2.unload()
        cap.release()
        cv2.destroyAllWindows()

simple_astra_pro_capture()