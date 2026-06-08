from openni import openni2
openni2.initialize()
dev = openni2.Device.open_any()

# 打印彩色流支持的所有格式（Astra Pro 必显示 YUY2）
color_stream = dev.create_color_stream()
if color_stream is None:
    print("Failed to create color stream")
else:
    print("=== Astra Pro 支持的彩色格式 ===")
    sensor_info = color_stream.get_sensor_info()
    for m in sensor_info.videoModes:
        print(m)