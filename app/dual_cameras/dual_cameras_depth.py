import cv2
import numpy as np

# 加载标定参数
data = np.load("wit_stereo.npz")
mtxL, distL = data["mtxL"], data["distL"]
mtxR, distR = data["mtxR"], data["distR"]
R, T = data["R"], data["T"]

w, h = 1280, 720
R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
    mtxL, distL, mtxR, distR, (w, h), R, T
)

map1 = cv2.initUndistortRectifyMap(mtxL, distL, R1, P1, (w, h), cv2.CV_16SC2)
map2 = cv2.initUndistortRectifyMap(mtxR, distR, R2, P2, (w, h), cv2.CV_16SC2)

stereo = cv2.StereoBM_create(numDisparities=64, blockSize=15)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2560)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    hh, ww = frame.shape[:2]
    w2 = ww // 2
    left = frame[:, :w2]
    right = frame[:, w2:]

    left_rect = cv2.remap(left, map1[0], map1[1], cv2.INTER_LINEAR)
    right_rect = cv2.remap(right, map2[0], map2[1], cv2.INTER_LINEAR)

    grayL = cv2.cvtColor(left_rect, cv2.COLOR_BGR2GRAY)
    grayR = cv2.cvtColor(right_rect, cv2.COLOR_BGR2GRAY)

    disp = stereo.compute(grayL, grayR)
    disp_norm = cv2.normalize(disp, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

    cv2.imshow("Rect Left", left_rect)
    cv2.imshow("Disparity", disp_norm)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
