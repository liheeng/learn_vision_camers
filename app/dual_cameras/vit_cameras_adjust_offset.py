import cv2
import numpy as np

# ========== 相机固定参数 ==========
BASELINE = 0.065   # 基线 65mm
FOCAL = 640        # 像素焦距
W, H = 1280, 720

click_x, click_y = W // 2, H // 2
offset = 0         # 初始垂直偏移量

# 鼠标点击回调：点击画面取距离
def mouse_event(event, x, y, flags, param):
    global click_x, click_y
    if event == cv2.EVENT_LBUTTONDOWN:
        click_x, click_y = x, y

# SGBM 立体匹配器（效果优于 BM）
stereo = cv2.StereoSGBM_create(
    minDisparity=0,
    numDisparities=96,
    blockSize=9,
    P1=8 * 3 * 9**2,
    P2=32 * 3 * 9**2,
    disp12MaxDiff=1,
    uniquenessRatio=10,
    speckleWindowSize=100,
    speckleRange=2,
    preFilterCap=63,
    mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
)

# 打开双目相机
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, W * 2)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)

cv2.namedWindow("Left View")
cv2.setMouseCallback("Left View", mouse_event)

# --------------------------
# 键盘操作说明（打印到终端）
# --------------------------
print("=" * 50)
print("【操作指南】")
print("  i 键 → 右画面 向上移动 1px")
print("  k 键 → 右画面 向下移动 1px")
print("  q 键 → 退出程序")
print("  ⚠️  先鼠标点击「Alignment Check」窗口再按按键！")
print("=" * 50)

# 图像垂直平移函数（替代 np.roll，无卷边）
def shift_vertical(img, dy):
    h, w = img.shape[:2]
    new_img = np.zeros_like(img)
    if dy > 0:
        # 向上移 dy 像素：顶部空出黑边
        new_img[dy:, :] = img[:h-dy, :]
    elif dy < 0:
        # 向下移 |dy| 像素：底部空出黑边
        dy_abs = abs(dy)
        new_img[:h-dy_abs, :] = img[dy_abs:, :]
    else:
        new_img = img.copy()
    return new_img

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 切分左右画面
    h, w_frame = frame.shape[:2]
    half_w = w_frame // 2
    img_l = frame[:, :half_w]
    img_r = frame[:, half_w:]

    # 应用垂直偏移（无卷边，对齐更准）
    img_r_shift = shift_vertical(img_r, offset)

    # 拼接画面 + 三条绿色辅助水平线（对齐专用）
    combined = np.hstack((img_l, img_r_shift))
    for y_line in [H//4, H//2, 3*H//4]:
        cv2.line(combined, (0, y_line), (combined.shape[1], y_line), (0, 255, 0), 1)
    # 显示当前偏移值
    cv2.putText(combined, f"Offset: {offset}", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.imshow("Alignment Check", combined)

    # 灰度图 + 视差计算
    gray_l = cv2.cvtColor(img_l, cv2.COLOR_BGR2GRAY)
    gray_r = cv2.cvtColor(img_r_shift, cv2.COLOR_BGR2GRAY)
    disparity = stereo.compute(gray_l, gray_r)
    disp_float = disparity.astype(np.float32)

    # 滤波去噪
    disp_float = cv2.medianBlur(disp_float, 5)
    disp_float = cv2.GaussianBlur(disp_float, (5, 5), 0)

    # 深度计算
    valid_mask = disp_float > 1.0
    depth_map = np.zeros_like(disp_float)
    depth_map[valid_mask] = (FOCAL * BASELINE) / disp_float[valid_mask]

    # 读取点击位置距离
    if valid_mask[click_y, click_x]:
        dist = depth_map[click_y, click_x]
    else:
        dist = 0.0

    # 左画面 + 测距文字 + 点击红点
    cv2.circle(img_l, (click_x, click_y), 5, (0, 0, 255), -1)
    cv2.putText(img_l, f"Dist: {dist:.2f} m", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Left View", img_l)

    # 视差图可视化
    disp_norm = cv2.normalize(disp_float, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    cv2.imshow("Disparity", disp_norm)

    # ========== 键盘监听（Mac 稳定版） ==========
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        print(f"\n最终最优 Offset = {offset}")
        break
    elif key == ord('i'):
        offset += 1
        print(f"当前 Offset: {offset}")
    elif key == ord('k'):
        offset -= 1
        print(f"当前 Offset: {offset}")

cap.release()
cv2.destroyAllWindows()