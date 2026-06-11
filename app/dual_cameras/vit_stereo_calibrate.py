import cv2
import numpy as np
import glob
import os

# 棋盘格参数（内角点数，例如7x6或9x6，请根据实际棋盘格修改）
CHESSBOARD_SIZE = (9, 6)   # 内角点列数，行数
SQUARE_SIZE = 25.0         # 棋盘格方格边长（mm）

# 相机图像尺寸（每个单目相机）
LEFT_WIDTH, LEFT_HEIGHT = 1920, 1080
RIGHT_WIDTH, RIGHT_HEIGHT = 1920, 1080
FRAME_WIDTH = LEFT_WIDTH + RIGHT_WIDTH   # 3840
FRAME_HEIGHT = LEFT_HEIGHT               # 1080

# 准备标定点
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
objp = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHESSBOARD_SIZE[0], 0:CHESSBOARD_SIZE[1]].T.reshape(-1, 2)
objp *= SQUARE_SIZE

# 存储左右相机对应的点
objpoints = []   # 世界坐标系中的3D点
imgpoints_l = [] # 左相机图像中的角点
imgpoints_r = [] # 右相机图像中的角点

# 读取图像（支持jpg,png）
images = glob.glob('calib_images/*.jpg') + glob.glob('calib_images/*.png')
print(f"找到 {len(images)} 张图像")

for fname in images:
    img_full = cv2.imread(fname)
    if img_full is None:
        continue
    # 分割左右图像
    left_img = img_full[:, :LEFT_WIDTH]
    right_img = img_full[:, LEFT_WIDTH:]
    
    gray_l = cv2.cvtColor(left_img, cv2.COLOR_BGR2GRAY)
    gray_r = cv2.cvtColor(right_img, cv2.COLOR_BGR2GRAY)
    
    # 查找棋盘格角点
    ret_l, corners_l = cv2.findChessboardCorners(gray_l, CHESSBOARD_SIZE, None)
    ret_r, corners_r = cv2.findChessboardCorners(gray_r, CHESSBOARD_SIZE, None)
    
    if ret_l and ret_r:
        objpoints.append(objp)
        # 亚像素精确化
        corners_l_sub = cv2.cornerSubPix(gray_l, corners_l, (11,11), (-1,-1), criteria)
        corners_r_sub = cv2.cornerSubPix(gray_r, corners_r, (11,11), (-1,-1), criteria)
        imgpoints_l.append(corners_l_sub)
        imgpoints_r.append(corners_r_sub)
        print(f"成功检测: {os.path.basename(fname)}")
    else:
        print(f"检测失败: {os.path.basename(fname)}")

print(f"有效图像对: {len(objpoints)}")

if len(objpoints) < 10:
    print("标定图像不足，请至少使用10张有效图像")
    exit()

# 单目标定（左相机）
ret_l, mtx_l, dist_l, rvecs_l, tvecs_l = cv2.calibrateCamera(
    objpoints, imgpoints_l, (LEFT_WIDTH, LEFT_HEIGHT), None, None)
# 右相机
ret_r, mtx_r, dist_r, rvecs_r, tvecs_r = cv2.calibrateCamera(
    objpoints, imgpoints_r, (RIGHT_WIDTH, RIGHT_HEIGHT), None, None)

print("\n左相机内参:\n", mtx_l)
print("左相机畸变系数:\n", dist_l)
print("右相机内参:\n", mtx_r)
print("右相机畸变系数:\n", dist_r)

# 双目立体标定（计算左右相机之间的旋转矩阵R、平移向量T）
flags = 0
flags |= cv2.CALIB_FIX_INTRINSIC   # 固定单目标定的内参
criteria_stereo = (cv2.TERM_CRITERIA_MAX_ITER + cv2.TERM_CRITERIA_EPS, 100, 1e-5)
ret, mtx_l, dist_l, mtx_r, dist_r, R, T, E, F = cv2.stereoCalibrate(
    objpoints, imgpoints_l, imgpoints_r,
    mtx_l, dist_l, mtx_r, dist_r,
    (LEFT_WIDTH, LEFT_HEIGHT), criteria=criteria_stereo, flags=flags)

print("\n立体标定结果:")
print("旋转矩阵 R:\n", R)
print("平移向量 T (mm):\n", T)

# 立体校正（生成映射表）
# alpha=0 时，裁剪掉不规则的边缘；alpha=1 时保留所有图像内容
R1, R2, P1, P2, Q, roi1, roi2 = cv2.stereoRectify(
    mtx_l, dist_l, mtx_r, dist_r,
    (LEFT_WIDTH, LEFT_HEIGHT), R, T, alpha=0)

# 计算校正映射
map1_l, map2_l = cv2.initUndistortRectifyMap(mtx_l, dist_l, R1, P1, (LEFT_WIDTH, LEFT_HEIGHT), cv2.CV_32FC1)
map1_r, map2_r = cv2.initUndistortRectifyMap(mtx_r, dist_r, R2, P2, (LEFT_WIDTH, LEFT_HEIGHT), cv2.CV_32FC1)

# 保存标定参数到文件
calib_data = {
    'mtx_l': mtx_l, 'dist_l': dist_l, 'mtx_r': mtx_r, 'dist_r': dist_r,
    'R': R, 'T': T, 'R1': R1, 'R2': R2, 'P1': P1, 'P2': P2, 'Q': Q,
    'map1_l': map1_l, 'map2_l': map2_l, 'map1_r': map1_r, 'map2_r': map2_r,
    'roi1': roi1, 'roi2': roi2,
    'baseline': abs(T[0])   # 提取基线距离（单位：毫米）
}
np.savez('stereo_calib.npz', **calib_data)
print("\n标定完成，参数已保存到 stereo_calib.npz")