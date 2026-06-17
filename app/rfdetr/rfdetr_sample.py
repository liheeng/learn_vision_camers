import os
import cv2
import numpy as np
import torch
from rfdetr import RFDETRNano, RFDETRSmall, RFDETRLarge

# ====================== 【必看】根据你的硬件修改这里 ======================
# 摄像头配置
CAMERA_ID = 0  # 单USB双目摄像头设备ID
TOTAL_WIDTH = 2560  # 相机总宽度（左目+右目）
TOTAL_HEIGHT = 720  # 相机总高度
# 双目标定参数（示例值，必须替换为你自己的标定结果，否则深度不准）
FOCAL_LENGTH = 800.0  # 左目焦距（像素）
BASELINE = 65.0  # 双目基线（两镜头中心距离，单位：毫米）
# 立体校正映射表（标定后生成，无标定可先跳过校正）
RECTIFY_ENABLE = False  # 没标定先设为False，跑通后再开
map1x: np.ndarray | None = None
map1y: np.ndarray | None = None
map2x: np.ndarray | None = None
map2y: np.ndarray | None = None
# 模型配置
MODEL_NAME = "rfdetr-nano"  # 可选: rfdetr-nano / rfdetr-small / rfdetr-large
CONF_THRESHOLD = 0.4  # 置信度阈值
# 深度误检修正配置
FIX_CLOCK_FAN = True  # 开启：钟表误判为风扇的深度校验修正
DEPTH_STD_THRESHOLD = 5.0  # 深度方差阈值，大于则判定为立体物体（风扇）
# ======================================================================

# 开启MPS算子回退，避免个别算子不支持报错
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

# 自动选择设备：优先MPS，不可用则CPU
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"使用设备: {device} (Apple M5 Max)")

# 1. 加载RF-DETR模型并移至MPS
print(f"加载模型 {MODEL_NAME} ...")
model_map = {
    "rfdetr-nano": RFDETRNano,
    "rfdetr-small": RFDETRSmall,
    "rfdetr-large": RFDETRLarge,
}
model_class = model_map.get(MODEL_NAME)
if model_class is None:
    raise ValueError(f"未知模型名称: {MODEL_NAME}，可选: rfdetr-nano, rfdetr-small, rfdetr-large")
model = model_class(device=device)
print("模型加载完成")

# 2. 初始化单USB双目摄像头
cap = cv2.VideoCapture(CAMERA_ID)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, TOTAL_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, TOTAL_HEIGHT)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*"MJPG"))  # MJPG编码提升帧率
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    print("摄像头打开失败，请检查设备ID")
    exit()

# 3. 初始化SGBM立体匹配器
sgbm = cv2.StereoSGBM.create(
    minDisparity=0,
    numDisparities=64,  # 最大视差，必须是16的倍数
    blockSize=9,  # 匹配块大小，奇数
    P1=8 * 3 * 9**2,  # 平滑参数1
    P2=32 * 3 * 9**2,  # 平滑参数2
    disp12MaxDiff=1,
    uniquenessRatio=10,
    speckleWindowSize=100,
    speckleRange=2,
)


def split_stereo(frame):
    """单USB双目帧切分为左右目"""
    h, w = frame.shape[:2]
    half_w = w // 2
    imgL = frame[:, :half_w]
    imgR = frame[:, half_w:]
    return imgL, imgR


def compute_depth(imgL_rect, imgR_rect):
    """双目立体匹配计算深度图，单位：毫米"""
    disp = sgbm.compute(imgL_rect, imgR_rect).astype(np.float32) / 16.0
    # 视差转深度：深度 = 焦距 * 基线 / 视差
    depth_map = np.full_like(disp, 0.0, dtype=np.float32)
    valid_mask = disp > 1.0
    depth_map[valid_mask] = (FOCAL_LENGTH * BASELINE) / disp[valid_mask]
    return depth_map


def depth_verify_clock(depth_map, x1, y1, x2, y2):
    """深度方差校验：判断是平面钟表还是立体风扇"""
    roi = depth_map[y1:y2, x1:x2]
    valid_roi = roi[(roi > 0) & (roi < 10000)]  # 过滤无效值
    if len(valid_roi) < 20:
        return False, 0.0
    depth_std = float(np.std(valid_roi))
    return depth_std > DEPTH_STD_THRESHOLD, depth_std


print("开始运行，按 ESC 退出")
while True:
    ret, frame = cap.read()
    if not ret:
        print("读取帧失败")
        break

    # 步骤1：切分左右目
    imgL, imgR = split_stereo(frame)
    h, w = imgL.shape[:2]

    # 步骤2：立体校正（标定后开启）
    if RECTIFY_ENABLE and map1x is not None:
        imgL_rect = cv2.remap(imgL, map1x, map1y, cv2.INTER_LINEAR)
        imgR_rect = cv2.remap(imgR, map2x, map2y, cv2.INTER_LINEAR)
    else:
        imgL_rect, imgR_rect = imgL, imgR

    # 步骤3：计算深度图
    depth_map = compute_depth(imgL_rect, imgR_rect)

    # 步骤4：RF-DETR推理左图
    with torch.no_grad():
        dets = model.predict(imgL_rect, threshold=CONF_THRESHOLD)[0]

    # 步骤5：遍历检测结果，叠加深度+误检修正
    draw_img = imgL_rect.copy()
    xyxy = dets.xyxy  # type: ignore[attr-defined]
    confidence = dets.confidence  # type: ignore[attr-defined]
    class_id = dets.class_id  # type: ignore[attr-defined]
    for i in range(len(xyxy)):
        x1, y1, x2, y2 = map(int, xyxy[i])
        conf = float(confidence[i])
        cls_id = int(class_id[i])
        cls_name = str(dets.data["class_name"][i])

        # 计算目标深度（取中位数抗噪）
        roi_depth = depth_map[y1:y2, x1:x2]
        valid_depth = roi_depth[(roi_depth > 0) & (roi_depth < 10000)]
        dist_text = "深度无效"
        if len(valid_depth) > 20:
            dist = np.median(valid_depth)
            dist_text = f"{dist:.0f}mm"

        # 深度方差误检修正：识别为钟表但深度方差大 → 修正为风扇
        if FIX_CLOCK_FAN and cls_name == "clock":
            is_3d, std_val = depth_verify_clock(depth_map, x1, y1, x2, y2)
            if is_3d:
                cls_name = "fan(修正)"
                dist_text += f" 方差:{std_val:.1f}"

        # 绘制框和文本
        cv2.rectangle(draw_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{cls_name} {conf:.2f} {dist_text}"
        cv2.putText(
            draw_img,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

    # 显示结果
    cv2.imshow("RF-DETR + 双目深度 (M5 Max)", draw_img)

    # 按ESC退出
    if cv2.waitKey(1) & 0xFF == 27:
        break

# 释放资源
cap.release()
cv2.destroyAllWindows()
print("程序已退出")
