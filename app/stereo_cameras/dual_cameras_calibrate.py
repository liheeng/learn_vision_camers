import cv2
import numpy as np
import glob

chess = (8, 6)
square = 0.025

objp = np.zeros((chess[0] * chess[1], 3), np.float32)
objp[:, :2] = np.mgrid[0 : chess[0], 0 : chess[1]].T.reshape(-1, 2) * square

objpoints = []
leftpoints = []
rightpoints = []

imgs = sorted(glob.glob("calib_*.jpg"))

for f in imgs:
    frame = cv2.imread(f)
    h, w = frame.shape[:2]
    w2 = w // 2
    left = frame[:, :w2]
    right = frame[:, w2:]
    grayL = cv2.cvtColor(left, cv2.COLOR_BGR2GRAY)
    grayR = cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)

    retL, cornersL = cv2.findChessboardCorners(grayL, chess, None)
    retR, cornersR = cv2.findChessboardCorners(grayR, chess, None)
    if retL and retR:
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        cornersL = cv2.cornerSubPix(grayL, cornersL, (11, 11), (-1, -1), criteria)
        cornersR = cv2.cornerSubPix(grayR, cornersR, (11, 11), (-1, -1), criteria)
        objpoints.append(objp)
        leftpoints.append(cornersL)
        rightpoints.append(cornersR)

# 单目标定
retL, mtxL, distL, rvecsL, tvecsL = cv2.calibrateCamera(
    objpoints, leftpoints, grayL.shape[::-1], None, None
)
retR, mtxR, distR, rvecsR, tvecsR = cv2.calibrateCamera(
    objpoints, rightpoints, grayR.shape[::-1], None, None
)

# 双目标定
ret, mtxL, distL, mtxR, distR, R, T, E, F = cv2.stereoCalibrate(
    objpoints,
    leftpoints,
    rightpoints,
    mtxL,
    distL,
    mtxR,
    distR,
    grayL.shape[::-1],
    criteria=criteria,
    flags=cv2.CALIB_FIX_INTRINSIC,
)

# 保存参数（下次直接加载）
np.savez("wit_stereo.npz", mtxL=mtxL, distL=distL, mtxR=mtxR, distR=distR, R=R, T=T)
print("标定完成，参数已保存为 wit_stereo.npz")
