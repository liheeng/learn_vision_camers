from pyorbbecsdk import Pipeline


def check_dabai_pro_firmware():
    pipeline = Pipeline()
    try:
        # 获取设备列表
        device = pipeline.get_device()
        
        # 获取第一个设备信息
        device_info = device.get_device_info()
        fw_version = device_info.get_firmware_version()
        device_name = device_info.get_name()
        pid = device_info.get_pid()
        
        print(f"📷 设备名称: {device_name}")
        print(f"🔢 固件版本: {fw_version}")
        print(f"🆔 产品ID: {hex(pid)}")
        
        # 判断协议类型
        if fw_version.startswith("v2."):
            print("✅ 协议类型: UVC协议 (支持Orbbec SDK v2)")
            print("💡 提示: 无需安装专用驱动，即插即用")
        elif fw_version.startswith("v1."):
            print("✅ 协议类型: OpenNI协议 (支持OpenNI2/Orbbec SDK v1)")
            print("💡 提示: 需要安装奥比中光私有驱动")
        else:
            print("⚠️ 未知协议类型，请联系奥比中光客服")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        pipeline.stop()

if __name__ == "__main__":
    check_dabai_pro_firmware()