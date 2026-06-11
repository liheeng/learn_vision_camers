import cv2

cap = cv2.VideoCapture(0)  # Mac 一般是 0
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2560)  # 1280*2
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow("frame", frame)
    if cv2.waitKey(1) == 27:
        break
cap.release()