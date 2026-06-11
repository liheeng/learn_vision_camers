import cv2
import numpy as np

# ================== 理论参数 ==================
BASELINE_MM = 65.0          # 基线 65mm
FOCAL_LEN_MM = 3.6          # 物理焦距 3.6mm
SENSOR_WIDTH_MM = 5.2       # 1/2.7" 传感器宽度约 5.2mm
IMG_WIDTH = 800             # 单目图像宽度（像素）
IMG_HEIGHT = 600            # 单目图像高度（像素）
# 根据新的分辨率计算像素焦距
FOCAL_LEN_PIX = (FOCAL_LEN_MM / SENSOR_WIDTH_MM) * IMG_WIDTH
print(f"理论像素焦距 (800x600): {FOCAL_LEN_PIX:.2f} px")

# ================== 相机设置 ==================
FULL_WIDTH = IMG_WIDTH * 2   # 1600
FULL_HEIGHT = IMG_HEIGHT     # 600
CAMERA_INDEX = 0             # 设备号，可能为0或1

cap = cv2.VideoCapture(CAMERA_INDEX)
# 尝试设置分辨率（相机可能不支持1600x600，若不支持则使用默认，需自行调整）
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FULL_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FULL_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, 30)

# 检查实际设置的分辨率
actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
print(f"实际相机分辨率: {actual_width} x {actual_height}")
if actual_width != FULL_WIDTH or actual_height != FULL_HEIGHT:
    print("警告: 相机不支持1600x600，将使用实际分辨率，请手动调整代码中的IMG_WIDTH/HEIGHT")

# ================== 立体匹配器 (SGBM) ==================
# 视差范围计算: Z_min = 0.2m => d_max = f*b/200 ≈ 1304*65/200 ≈ 424
# 800宽度下像素焦距减小，d_max ≈ (1304*800/1920)*65/200 ≈ (543)*65/200 ≈ 176
# 所以设置 numDisparities = 16*16 = 256 足够
window_size = 3              # 分辨率降低，窗口可以小一点
min_disp = 0
num_disp = 16 * 16           # 256
block_size = 9               # 奇数，可调

stereo = cv2.StereoSGBM_create(
    minDisparity=min_disp,
    numDisparities=num_disp,
    blockSize=block_size,
    P1=8 * 3 * window_size ** 2,
    P2=32 * 3 * window_size ** 2,
    disp12MaxDiff=1,
    uniquenessRatio=10,
    speckleWindowSize=100,
    speckleRange=32,
    mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
)

def compute_depth(disparity_map, f_pix, baseline_mm):
    """将视差图（16倍）转换为深度图（毫米）"""
    disp = np.float32(disparity_map) / 16.0
    disp[disp <= 0.0] = 0.1
    depth = (f_pix * baseline_mm) / disp
    return depth

print("开始无标定实时测距 (800x600)...")
print("按 'q' 退出，按 's' 保存视差图")

while True:
    ret, frame = cap.read()
    if not ret:
        print("无法读取相机，请检查设备号或连接")
        break

    # 如果相机实际分辨率与设定不一致，需重新调整切分点；这里假设实际为1600x600
    h, w = frame.shape[:2]
    if w != FULL_WIDTH or h != FULL_HEIGHT:
        # 若相机不支持设定分辨率，按实际宽度的左半和右半切分（假设左右等宽）
        half = w // 2
        left_raw = frame[:, :half]
        right_raw = frame[:, half:]
        # 可选: 缩放到目标分辨率
        if left_raw.shape[1] != IMG_WIDTH:
            left_raw = cv2.resize(left_raw, (IMG_WIDTH, IMG_HEIGHT))
            right_raw = cv2.resize(right_raw, (IMG_WIDTH, IMG_HEIGHT))
    else:
        left_raw = frame[:, :IMG_WIDTH]
        right_raw = frame[:, IMG_WIDTH:]

    # 转为灰度图
    gray_left = cv2.cvtColor(left_raw, cv2.COLOR_BGR2GRAY)
    gray_right = cv2.cvtColor(right_raw, cv2.COLOR_BGR2GRAY)

    # 计算视差图
    disparity = stereo.compute(gray_left, gray_right)

    # 深度图
    depth_map = compute_depth(disparity, FOCAL_LEN_PIX, BASELINE_MM)

    # 可视化深度图（0~5000mm映射到0~255）
    depth_vis = np.clip(depth_map / 5000.0 * 255, 0, 255).astype(np.uint8)
    depth_color = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)

    # 在左图上显示中心点距离（自动转换单位）
    center_x, center_y = IMG_WIDTH // 2, IMG_HEIGHT // 2
    distance = depth_map[center_y, center_x]
    if distance > 1000:
        disp_text = f"{distance / 1000:.2f} m"
    elif distance > 10:
        disp_text = f"{distance / 10:.1f} cm"
    else:
        disp_text = f"{distance:.1f} mm"
    left_with_text = left_raw.copy()
    cv2.circle(left_with_text, (center_x, center_y), 5, (0, 0, 255), -1)
    cv2.putText(left_with_text, disp_text, (center_x + 10, center_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # 显示
    cv2.imshow("Left + Distance", left_with_text)
    cv2.imshow("Depth Map", depth_color)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        cv2.imwrite("disparity_800x600.png", disparity)
        print("已保存视差图")

cap.release()
cv2.destroyAllWindows()