import cv2
import numpy as np

# ---------- 相机参数（理论值，若标定结果中基线可用则优先使用）----------
BASELINE_MM = 65.0   # 基线 65mm（与参数表一致）
FOCAL_LEN_MM = 3.6   # 焦距 3.6mm
# 传感器尺寸：1/2.7'' 实际对角线约6.7mm，按16:9计算像素物理尺寸
SENSOR_WIDTH_MM = 5.2   # 近似值，更精确方法见下文
PIXEL_SIZE_MM = SENSOR_WIDTH_MM / 1920.0   # 单个像素宽度(mm)
FOCAL_LEN_PIX = FOCAL_LEN_MM / PIXEL_SIZE_MM   # 焦距对应的像素单位
# ----------------------------------------------------------------

# 从标定文件加载参数（若执行过标定脚本）
try:
    calib = np.load('stereo_calib.npz', allow_pickle=True)
    map1_l = calib['map1_l']
    map2_l = calib['map2_l']
    map1_r = calib['map1_r']
    map2_r = calib['map2_r']
    Q = calib['Q']          # 视差转深度的矩阵，优先使用
    baseline = float(calib['baseline'])
    # 如果能从Q矩阵中提取焦距和基线则优先
    fx = Q[2,3] if Q[2,3] != 0 else FOCAL_LEN_PIX
    cx = Q[0,3]
    cy = Q[1,3]
    print(f"加载标定文件成功，基线={baseline:.2f}mm，等效焦距fx={fx:.2f}像素")
except:
    print("未找到标定文件，将使用理论焦距和基线，但立体校正映射缺失，请先运行标定脚本！")
    exit()

# 图像尺寸（单目）
IMG_WIDTH, IMG_HEIGHT = 1920, 1080
FULL_WIDTH = IMG_WIDTH * 2   # 3840

# 打开USB相机（通常是设备0，也可能是1）
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FULL_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMG_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, 30)

# 创建立体匹配器（SGBM，效果较好）
window_size = 5
min_disp = 0          # 最小视差，通常为0
num_disp = 16*8       # 视差搜索范围，必须为16的倍数
block_size = 11       # 匹配块大小，奇数
stereo = cv2.StereoSGBM_create(
    minDisparity = min_disp,
    numDisparities = num_disp,
    blockSize = block_size,
    P1 = 8 * 3 * window_size ** 2,
    P2 = 32 * 3 * window_size ** 2,
    disp12MaxDiff = 1,
    uniquenessRatio = 10,
    speckleWindowSize = 100,
    speckleRange = 32,
    mode = cv2.STEREO_SGBM_MODE_SGBM_3WAY
)

def compute_depth_map(disp_map, fx, baseline, scale=16.0):
    """
    将原始视差图（单位为像素*16）转换为深度图（毫米）
    disp_map: SGBM输出的16倍视差图
    fx: 焦距（像素）
    baseline: 基线（毫米）
    """
    # 避免除零
    disp_map = np.float32(disp_map) / scale
    disp_map[disp_map <= 0.0] = 0.1
    depth_map = (fx * baseline) / disp_map
    return depth_map

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # 分割左右图像
    left_raw = frame[:, :IMG_WIDTH]
    right_raw = frame[:, IMG_WIDTH:]
    
    # 立体校正（使用预先计算的映射表）
    left_rect = cv2.remap(left_raw, map1_l, map2_l, cv2.INTER_LINEAR)
    right_rect = cv2.remap(right_raw, map1_r, map2_r, cv2.INTER_LINEAR)
    
    # 转为灰度图
    gray_left = cv2.cvtColor(left_rect, cv2.COLOR_BGR2GRAY)
    gray_right = cv2.cvtColor(right_rect, cv2.COLOR_BGR2GRAY)
    
    # 计算视差图
    disparity = stereo.compute(gray_left, gray_right).astype(np.float32)
    
    # 深度图（毫米）
    depth = compute_depth_map(disparity, fx, baseline)
    
    # 将深度图可视化（限制显示范围 0~5000mm）
    depth_vis = np.clip(depth / 5000.0 * 255, 0, 255).astype(np.uint8)
    depth_color = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)
    
    # 在左校正图上画一个十字并显示其距离
    center_x, center_y = IMG_WIDTH//2, IMG_HEIGHT//2
    cv2.circle(left_rect, (center_x, center_y), 5, (0,0,255), -1)
    distance = depth[center_y, center_x]
    cv2.putText(left_rect, f"{distance:.1f}mm", (center_x+10, center_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    
    # 显示结果
    cv2.imshow("Rectified Left", left_rect)
    cv2.imshow("Depth Map", depth_color)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        cv2.imwrite("disparity.png", disparity/16)  # 保存视差图
        print("已保存视差图")

cap.release()
cv2.destroyAllWindows()