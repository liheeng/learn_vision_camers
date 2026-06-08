from openni import openni2
import numpy as np
import cv2
import time
import argparse
import os
from datetime import datetime

DEVICE_INFO = {}
WINDOW_NAME_DEPTH = 'Depth Image'
WINDOW_NAME_COLOR = 'Color Image'
WINDOW_NAME_IR = 'IR Image'
COLOR_MAP_TYPE = 8  # 可以尝试不同的色彩映射, 有0~11种渲染的模式,8 色彩鲜艳，2的色彩正常，0和11为黑白色
ALPHA_VALUE = 0.17
MAX_DISTANCE_CM = 800  # 最大有效距离，单位为厘米
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.5
FONT_COLOR = (0, 0, 0)
FONT_THICKNESS = 1
last_click_time = 0
click_x, click_y = -1, -1
distance_text = ""

dpt = None


def mousecallback(event, x, y, flags, param):
    global click_x, click_y, distance_text, last_click_time
    if event == cv2.EVENT_LBUTTONDOWN:  # 单击事件，需要双击事件就是cv2.EVENT_LBUTTONDBLCLK
        click_x, click_y = x, y
        if dpt is None:
            return
        distance = dpt[y, x] / 10.0  # 若深度值是以毫米为单位，转换为厘米
        distance_text = f"Dis: {distance:.2f} cm"
        last_click_time = time.time()


click_x, click_y = -1, -1
distance_text = ""
last_click_time = 0


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description='OpenNI depth+color+IR viewer')
        parser.add_argument('--color-index', type=int, default=None,
                            help='OpenCV color device index to use (overrides auto-probe)')
        parser.add_argument('--out-dir', type=str, default='captures', help='Directory to save screenshots')
        args = parser.parse_args()

        os.makedirs(args.out_dir, exist_ok=True)

        openni2.initialize()
        dev = openni2.Device.open_any()
        print(dev.get_device_info())
        depth_stream = dev.create_depth_stream()
        dev.set_image_registration_mode(True)
        depth_stream.start()
        
        # Infrared stream
        ir_stream = None
        try:
            ir_stream = dev.create_ir_stream()
            ir_stream.start()
        except Exception:
            ir_stream = None

        # Fall back to OpenCV VideoCapture for color (probe a few indices)
        cap = None
        if args.color_index is not None:
            try:
                c = cv2.VideoCapture(args.color_index)
                if c.isOpened():
                    cap = c
                    print(f"Using OpenCV color device index: {args.color_index}")
                else:
                    print(f"Requested color index {args.color_index} not available")
            except Exception:
                pass

        if cap is None:
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
            print("Warning: no OpenCV color device found; color window will be empty")
        
        cv2.namedWindow(WINDOW_NAME_DEPTH)
        cv2.namedWindow(WINDOW_NAME_COLOR)
        cv2.namedWindow(WINDOW_NAME_IR)
        cv2.setMouseCallback(WINDOW_NAME_DEPTH, mousecallback)

        while True:
            dframe = depth_stream.read_frame()
            dframe_data = np.array(dframe.get_buffer_as_triplet()).reshape([480, 640, 2])
            dpt1 = np.asarray(dframe_data[:, :, 0], dtype='float32')
            dpt2 = np.asarray(dframe_data[:, :, 1], dtype='float32')

            dpt2 *= 255
            dpt = dpt1 + dpt2
            dim_gray = cv2.convertScaleAbs(dpt, alpha=ALPHA_VALUE)
            # 对深度图像进行渲染
            depth_colormap = cv2.applyColorMap(dim_gray, COLOR_MAP_TYPE)

            if click_x >= 0 and click_y >= 0 and (time.time() - last_click_time) < 5:
                depth_colormap = cv2.putText(depth_colormap, distance_text, (click_x, click_y), FONT, FONT_SCALE,
                                             FONT_COLOR, FONT_THICKNESS, cv2.LINE_AA)

            cv2.imshow(WINDOW_NAME_DEPTH, depth_colormap)

            # IR frame (if available)
            ir_display = None
            if ir_stream is not None:
                try:
                    ir_frame = ir_stream.read_frame()
                    ir_data = np.array(ir_frame.get_buffer_as_uint16()).reshape([480, 640])
                    # normalize for display
                    ir_display = cv2.normalize(ir_data, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
                    cv2.imshow(WINDOW_NAME_IR, ir_display)
                except Exception:
                    pass

            # Color: use OpenCV capture if available
            if cap is not None:
                try:
                    ret, frame = cap.read()
                    if ret:
                        frame = cv2.flip(frame, 1)
                        cv2.imshow(WINDOW_NAME_COLOR, frame)
                except Exception:
                    frame = None

            key = cv2.waitKey(1)
            if key & 0xFF == ord(' '):
                break
            # press 's' to save current depth colormap, color and IR images
            if key & 0xFF == ord('s'):
                ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                depth_path = os.path.join(args.out_dir, f'depth_{ts}.png')
                cv2.imwrite(depth_path, depth_colormap)
                if 'frame' in locals() and frame is not None:
                    color_path = os.path.join(args.out_dir, f'color_{ts}.png')
                    cv2.imwrite(color_path, frame)
                if ir_stream is not None and 'ir_data' in locals():
                    ir_path = os.path.join(args.out_dir, f'ir_{ts}.png')
                    # save IR as 16-bit PNG if possible
                    try:
                        cv2.imwrite(ir_path, ir_data.astype(np.uint16))
                    except Exception:
                        # fallback to 8-bit display image
                        cv2.imwrite(ir_path, ir_display)
                print(f'Saved depth -> {depth_path}')

        depth_stream.stop()
        if ir_stream is not None:
            try:
                ir_stream.stop()
            except Exception:
                pass
        dev.close()
        openni2.unload()
        try:
            if cap is not None:
                cap.release()
        except Exception:
            pass
        cv2.destroyAllWindows()

    except Exception as e:
        print(f"An error occurred: {e}")