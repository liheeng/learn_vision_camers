"""OpenCV 直接读 Astra 彩色摄像头 (UVC)"""
import cv2
import sys

for idx in [0, 1]:
    print(f"尝试 /dev/video{idx} ...")

    # 不设任何参数，用默认后端
    cap = cv2.VideoCapture(idx)
    if not cap.isOpened():
        print(f"  ❌ 打不开")
        continue

    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"  ✅ {int(w)}x{int(h)}")

    print("  尝试读帧...")
    ret, frame = cap.read()
    if ret and frame is not None:
        print(f"  ✅ 读到帧: {frame.shape}")
        print("  显示中...按 q 退出")
        while True:
            ret, frame = cap.read()
            if not ret:
                print("  ⚠️ 断流")
                break
            cv2.imshow(f"Color /dev/video{idx}", frame)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                exit(0)
    else:
        print(f"  ❌ 读不到帧 (ret={ret})")

    cap.release()
    cv2.destroyAllWindows()

print("全部测试完毕")
