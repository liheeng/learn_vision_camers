import cv2

cap = cv2.VideoCapture(0)  # 维特双目一般在 video0
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2560)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 切分左右（维特这款是左右并排）
    h, w = frame.shape[:2]
    w2 = w // 2
    left = frame[:, :w2]
    right = frame[:, w2:]

    cv2.imshow("WIT Left", left)
    cv2.imshow("WIT Right", right)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
