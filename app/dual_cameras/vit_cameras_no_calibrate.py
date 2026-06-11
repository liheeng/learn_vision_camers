import cv2
import numpy as np

# 固定参数（无需标定）
BASELINE = 0.065    # 基线 6cm
FOCAL = 360        # 估算焦距(像素)
W, H = 1280, 720

# 初始化双目匹配器
stereo = cv2.StereoBM_create(numDisparities=64, blockSize=15)

# 打开相机
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, W*2)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 切分左右画面
    h, w = frame.shape[:2]
    half_w = w // 2
    img_l = frame[:, :half_w]
    img_r = frame[:, half_w:]

    # 转灰度做匹配
    gray_l = cv2.cvtColor(img_l, cv2.COLOR_BGR2GRAY)
    gray_r = cv2.cvtColor(img_r, cv2.COLOR_BGR2GRAY)

    # 计算视差图
    disparity = stereo.compute(gray_l, gray_r)
    disp_float = disparity.astype(np.float32)

    # 计算深度（过滤无效视差）
    depth_map = np.zeros_like(disp_float)
    valid_mask = disp_float > 1.0
    depth_map[valid_mask] = (FOCAL * BASELINE) / disp_float[valid_mask]

    # 取画面中心像素距离（直观查看）
    center_y, center_x = H//2, W//2
    center_dist = depth_map[center_y, center_x]

    # 显示信息
    cv2.putText(img_l, f"Dist: {center_dist:.2f} m", (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.imshow("Left View", img_l)

    # 视差图可视化
    disp_norm = cv2.normalize(disparity, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    cv2.imshow("Disparity", disp_norm)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()