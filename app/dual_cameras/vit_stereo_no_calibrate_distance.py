import cv2
import numpy as np

# ========== 理论参数 (800x600) ==========
BASELINE_MM = 65.0
FOCAL_LEN_MM = 3.6
SENSOR_WIDTH_MM = 5.2
IMG_WIDTH, IMG_HEIGHT = 800, 600
FOCAL_LEN_PIX = (FOCAL_LEN_MM / SENSOR_WIDTH_MM) * IMG_WIDTH
print(f"像素焦距: {FOCAL_LEN_PIX:.2f} px")

# ========== 相机 ==========
FULL_WIDTH, FULL_HEIGHT = IMG_WIDTH*2, IMG_HEIGHT
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FULL_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FULL_HEIGHT)

# ========== 立体匹配 ==========
stereo = cv2.StereoSGBM_create(
    minDisparity=0, numDisparities=16*16, blockSize=9,
    P1=8*3*9, P2=32*3*9, disp12MaxDiff=1, uniquenessRatio=10,
    speckleWindowSize=100, speckleRange=32
)

def compute_depth(disp_map, f_pix, baseline):
    disp = np.float32(disp_map) / 16.0
    disp[disp <= 0] = 0.1
    return (f_pix * baseline) / disp

# ========== 鼠标回调 ==========
current_depth = None
def show_depth_on_click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and current_depth is not None:
        if 0 <= y < current_depth.shape[0] and 0 <= x < current_depth.shape[1]:
            dist = current_depth[y, x]
            print(f"点 ({x},{y}) 距离 = {dist:.1f} mm")

cv2.namedWindow("Left Image")
cv2.setMouseCallback("Left Image", show_depth_on_click)

print("启动... 左键点击图像任意点查看距离，按 q 退出")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    # 分割
    left = frame[:, :IMG_WIDTH]
    right = frame[:, IMG_WIDTH:]
    grayL = cv2.cvtColor(left, cv2.COLOR_BGR2GRAY)
    grayR = cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)

    disp = stereo.compute(grayL, grayR)
    depth = compute_depth(disp, FOCAL_LEN_PIX, BASELINE_MM)
    current_depth = depth   # 供回调使用

    # 显示左图，并在中心画个参考点（可选）
    left_show = left.copy()
    cv2.circle(left_show, (IMG_WIDTH//2, IMG_HEIGHT//2), 5, (0,0,255), -1)
    cv2.putText(left_show, f"Center: {depth[IMG_HEIGHT//2, IMG_WIDTH//2]:.1f}mm",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    cv2.imshow("Left Image", left_show)

    # 显示伪彩色深度图
    depth_vis = np.clip(depth / 5000.0 * 255, 0, 255).astype(np.uint8)
    depth_color = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)
    cv2.imshow("Depth Map", depth_color)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()