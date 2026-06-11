import cv2

# 遍历设备 0~5，找到左右摄像头
for i in range(6):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"设备 {i} 可用")
        cap.release()
        break
