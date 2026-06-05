import cv2
import numpy as np
from pyorbbecsdk import Context, Pipeline, Config, OBFormat, OBSensorType


def astra_pro_hybrid_mode():
    # Initialize context and device
    ctx = Context()
    device_list = ctx.query_devices()
    if device_list.get_count() == 0:
        print("❌ No Orbbec device found")
        return

    device = device_list.get_device_by_index(0)
    print(f"✅ Device: {device.get_device_info().get_name()}")

    # Create pipeline and configure streams
    pipeline = Pipeline(device)
    config = Config()
    
    # Get and enable depth stream
    try:
        depth_profiles = pipeline.get_stream_profile_list(OBSensorType.DEPTH_SENSOR)
        depth_profile = depth_profiles.get_default_video_stream_profile()
        config.enable_stream(depth_profile)
        print("✅ Depth stream enabled")
    except Exception as e:
        print(f"⚠️  Depth stream: {e}")
    
    # Get and enable IR stream if available
    try:
        ir_profiles = pipeline.get_stream_profile_list(OBSensorType.IR_SENSOR)
        ir_profile = ir_profiles.get_default_video_stream_profile()
        config.enable_stream(ir_profile)
        has_ir = True
        print("✅ IR stream enabled")
    except Exception as e:
        has_ir = False
        print(f"⚠️  IR stream: {e}")

    pipeline.start(config)
    print("✅ Pipeline started")
    
    # Fallback to OpenCV for color (UVC camera)
    cap = cv2.VideoCapture(0)  # Try device 0, can adjust to 1,2,...
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    try:
        while True:
            # Get frames from pipeline
            frames = pipeline.wait_for_frames(1000)
            if frames is None:
                continue

            # Depth
            depth_frame = frames.get_depth_frame()
            if depth_frame is not None:
                w, h = depth_frame.get_width(), depth_frame.get_height()
                depth_data = np.frombuffer(depth_frame.get_data(), dtype=np.uint16).reshape(h, w)
                
                # Adaptive normalization (auto-scale based on actual depth range)
                nz = depth_data[depth_data > 0]
                if len(nz) > 100:
                    lo, hi = int(nz.min()), int(nz.max())
                else:
                    lo, hi = 500, 8000
                if hi <= lo:
                    hi = lo + 1
                
                norm = ((depth_data.clip(lo, hi) - lo) * 255 // (hi - lo)).astype(np.uint8)
                depth_colormap = cv2.applyColorMap(norm, cv2.COLORMAP_JET)
                depth_colormap[depth_data == 0] = (0, 0, 0)
                # Scale up for better display (2x)
                depth_display = cv2.resize(depth_colormap, (depth_colormap.shape[1] * 4, depth_colormap.shape[0] * 4))
                cv2.imshow("Depth", depth_display)

            # IR (if available)
            if has_ir:
                ir_frame = frames.get_ir_frame()
                if ir_frame is not None:
                    w, h = ir_frame.get_width(), ir_frame.get_height()
                    ir_data = np.frombuffer(ir_frame.get_data(), dtype=np.uint16).reshape(h, w)
                    
                    # Adaptive normalization + colormap (same as depth)
                    nz_ir = ir_data[ir_data > 0]
                    if len(nz_ir) > 100:
                        lo_ir, hi_ir = int(nz_ir.min()), int(nz_ir.max())
                    else:
                        lo_ir, hi_ir = 0, 65535
                    if hi_ir <= lo_ir:
                        hi_ir = lo_ir + 1
                    
                    norm_ir = ((ir_data.clip(lo_ir, hi_ir) - lo_ir) * 255 // (hi_ir - lo_ir)).astype(np.uint8)
                    ir_colormap = cv2.applyColorMap(norm_ir, cv2.COLORMAP_JET)
                    # Scale up for better display (4x, same as depth)
                    ir_display = cv2.resize(ir_colormap, (ir_colormap.shape[1] * 4, ir_colormap.shape[0] * 4))
                    cv2.imshow("IR", ir_display)
                else:
                    print("⚠️  No IR frame data")

            # Color (from OpenCV)
            ret, color_bgr = cap.read()
            if ret:
                cv2.imshow("Color", color_bgr)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        pipeline.stop()
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    astra_pro_hybrid_mode()