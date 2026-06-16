import cv2
from ultralytics import YOLO

# ========== 可修改配置 ==========
CAM_INDEX = 0               # 双目摄像头设备索引
MODEL_PATH = "./model/yolov8n.pt"   # 推荐轻量模型：yolo11n / yolov8n
DEVICE = "mps"              # Mac填mps，N卡填cuda，M5 Max填cpu
CONF_THRESH = 0.5           # 检测置信度阈值
# ================================

# 初始化YOLO模型
model = YOLO(MODEL_PATH)

# 打开双目摄像头
cap = cv2.VideoCapture(CAM_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2560)  # 双目一般左右并排，宽度是单目两倍
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
if not cap.isOpened():
    print("无法打开摄像头，请检查设备索引和权限")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("读取画面失败")
        break

    # 拆分左右目画面（左右各占一半宽度）
    h, w = frame.shape[:2]
    mid = w // 2
    left_frame = frame[:, :mid]
    right_frame = frame[:, mid:]

    # 对左目画面做YOLO检测（也可替换为右目，或两路都检测）
    results = model(
        left_frame,
        conf=CONF_THRESH,
        device=DEVICE,
        verbose=False  # 关闭每帧日志输出
    )

    # 自动绘制检测框、类别、置信度到左目画面
    left_annotated = results[0].plot()

    # 左右画面拼接显示：左侧带检测结果，右侧为原始画面
    display_frame = cv2.hconcat([left_annotated, right_frame])

    # 显示窗口，按 q 键退出
    cv2.imshow("Stereo YOLO | Left(Detect) / Right(Original)", display_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放资源
cap.release()
cv2.destroyAllWindows()