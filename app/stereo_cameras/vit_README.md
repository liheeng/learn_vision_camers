维特400W双目视觉相机的测距原理，是基于“双目立体视觉”技术，通过模仿人眼的工作方式来获取物体的深度（距离）信息。

简单来说，整个过程可以分为三个核心环节：

核心原理：利用三角测量法，计算物体在左右两个相机画面中的位置差异（即“视差”），距离越近，差异越大。

关键公式：深度（距离） = (焦距 × 基线距离) / 视差。

实现步骤：通过相机标定校准内外参数、图像校正、立体匹配计算视差，最后代入公式深度计算。

🔬 核心原理：三角测量与视差
维特400W双目相机通过两个并排放置的摄像头（类似人的双眼）同时拍摄同一场景。由于两个摄像头的位置不同，同一个物体在左右两张照片中的位置会有细微的水平偏移，这个偏移量就是“视差 (Disparity)”。

这个原理背后是经典的三角测量法。如下图所示：
















当物体距离相机很近时，它在左右两张画面中的位置差异会很大（视差大）；当物体很远时，这种差异就会变得很小甚至难以察觉（视差小）。

📐 核心公式：Z = (f × b) / d
将上面发现的规律量化，就得到了双目测距的数学公式：

Z = (f × b) / d

在这个公式中：

Z (Depth): 所求的目标物体距离，单位通常为毫米（mm）。

f (Focal Length): 相机的焦距，是相机本身的固定参数。

b (Baseline): 两个摄像头光心之间的距离，称为基线，也是硬件固定参数。

d (Disparity): 视差，即目标物体在左右图像中成像点的水平位置差（单位：像素）。

⚙️ 实现步骤
要让相机测出距离，还需要以下四个关键步骤：

相机标定 (Camera Calibration)
这是保证精度的基础。通过拍摄多张已知尺寸的棋盘格标定板，计算出相机的“内参”（如焦距f、镜头畸变）和“外参”（如基线距离b）。这些参数是后续所有计算的基础。

图像校正 (Stereo Rectification)
为了让计算更简单，算法会对左右两张图像进行校正处理。其目的是让它们看起来就像是来自两个完全平行的相机，这样同一个点会出现在两张图像的同一水平线上，大大降低了“立体匹配”的难度。

立体匹配 (Stereo Matching)
这是最核心也最复杂的步骤。算法会像解谜一样，在右图中找到左图每一个像素点的对应位置，并计算出它们之间的水平偏移量（即视差d）。这个过程会生成一张“视差图”，图中每个像素点储存着该处的视差值，而非颜色值。

精度影响：在1米的距离上，精度可达到±3mm，但在远距离或弱纹理（如白墙）环境下，精度会有所下降。

深度计算 (Depth Calculation)
这是最后一步。将前面得到的 f、b 和 d 代入公式 Z = (f × b) / d 中，即可计算出物体的距离，并最终生成一张“深度图”或整个场景的“点云数据”。

💡 影响精度的因素
在评估或使用维特400W相机时，可以关注以下几点：

基线长度 (b)：基线越长，测距越远，精度也相对越高。通常在几厘米到十几厘米之间。

焦距 (f)：焦距越长（通常意味着更窄的视角），能探测的距离也更远。

分辨率：更高的分辨率（如400W像素）能为算法提供更丰富的细节，有助于提高匹配精度。

光线与纹理：光线充足且纹理丰富的场景下测距效果最好，而在弱光、纯色墙面等环境下，测距效果会受限，甚至无法测量。

有效测距范围：根据公开资料，维特的一款双目相机基线为75mm，其有效测距范围通常在0.6米到8米之间。

🎯 典型应用场景
基于它的原理，维特400W双目相机在以下场景中能发挥重要作用：

机器人导航与避障：帮助机器人感知周围环境，识别障碍物距离。

工业自动化：在流水线上对工件进行高精度的尺寸测量和定位抓取。

智能安防与交通：在停车场监控、客流统计等场景下，精准判断目标的位置和轨迹。

三维建模与感知：为人机交互、姿态识别等应用提供核心的三维数据。

✨ 总结与建议
总的来说，维特400W双目视觉相机的测距过程就是：两个摄像头模拟人眼，利用 “视差” 这一关键线索，通过几何公式计算出距离。

在实际使用中，建议重点关注：

标定环节：出厂或初次安装时的标定质量直接决定了最终数据的可靠性。

工作场景：尽量在光照充足、物体表面有纹理的环境下使用，以获得最佳的测距效果。

如果想了解更具体的技术参数、标定工具或开发案例，也欢迎继续提问。

这是相机参数，写个python代码，用opencv测距呢
我们收到用户提供的相机参数图片（内容已转文字）。用户要求写一个Python代码，用OpenCV进行双目测距。相机参数包括：基线65mm，焦距3.6mm，分辨率3840x1080（双1080P），像素尺寸需要推算（像面尺寸1/2.7''）。需要编写完整的双目测距代码，包括标定、立体匹配、计算深度等步骤。需要提供清晰的代码和解释。

我们要注意：用户期望的是"用opencv测距"，所以需要提供可运行的脚本，可能包括读取左右图像、立体匹配计算视差、转换为深度。由于没有提供标定数据，代码中应包含标定部分（读取棋盘格图像进行标定），或假设已有标定参数文件。更常见做法：提供标定和测距两个主要部分，但用户可能希望直接使用相机实时测距。因为相机是USB免驱动，OpenCV可以捕获左右图像（可能是单个USB设备输出拼接图像）。根据分辨率3840x1080，可能是左右并排图像，需要分割。

因此代码需要：

解析相机参数：基线b=65mm，焦距f=3.6mm，但焦距需要转换为像素单位（fx），这需要知道像素尺寸。传感器尺寸1/2.7''，对角线约6.7mm，具体宽高比？通常4:3，但分辨率是1920x1080每个传感器？双1080p总宽3840，每个1080p宽度1920，高度1080。传感器像面尺寸1/2.7''，英寸按16mm? 实际1英寸=16mm（传感器领域），所以1/2.7英寸≈5.93mm对角线。若宽高比16:9，则宽度≈5.17mm，高度≈2.91mm。那么像素尺寸 = 宽度/1920 ≈ 2.69e-3 mm/px。焦距3.6mm对应像素焦距 fx = 3.6 / 像素尺寸 ≈ 1338 px。基线65mm，单位统一。

在代码中，我们可以从参数直接计算fx，但更精确的方式是通过标定获得。我们为用户提供两种方式：提供标定脚本和实时测距脚本；或者直接使用理论焦距值。

根据用户要求，写一个完整示例：标定（采集棋盘格图像），然后实时双目测距。代码需要处理图像分割、立体匹配（SGBM）、视差到深度转换、显示深度图。

还需要考虑相机可能输出拼接图像，分割点为宽度一半。

提供代码及注释，并解释重要步骤。

注意：OpenCV的stereoBM或SGBM需要校正后的图像，所以标定后需要立体校正。整个流程较长，但可以简化：假设相机已标定好，加载标定参数。但用户没有标定参数，所以代码必须包含标定部分，否则无法运行。

我们将提供两个脚本：一个用于标定，另一个用于实时测距。或者单个脚本中可以选择模式。

由于对话是中文环境，代码注释用中文。输出深度信息。

还需要考虑相机的实际使用：手动调焦，可能需要用户先调好焦。

最终答案：提供Python代码，使用OpenCV，包含标定和测距两部分。给出详细说明。

我们开始写答案。

根据您提供的相机参数（基线65mm，焦距3.6mm，分辨率3840×1080），下面给出一个完整的Python双目测距代码。代码包含两个主要功能：

立体标定：拍摄棋盘格图像，计算左右相机的内参、畸变系数以及立体校正参数。

实时测距：加载标定结果，对USB相机采集的左右图像进行校正、立体匹配，计算深度图并显示指定点的距离。

由于相机通过USB输出一幅3840×1080的拼接图像（左右各1920×1080），代码会自动分割左右图像。

1. 标定脚本（保存为 stereo_calibrate.py）
首先准备棋盘格图像。将棋盘格打印在平整的硬板上，用相机从不同角度、距离拍摄20~30张，放入 calib_images 文件夹。棋盘格内角点数（如9×6）需要修改下面的参数。

python
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
2. 实时测距脚本（保存为 live_depth.py）
使用标定结果，对实时USB图像进行立体匹配和深度计算。

python
import cv2
import numpy as np

# ---------- 相机参数（理论值，若标定结果中基线可用则优先使用）----------
BASELINE_MM = 65.0   # 基线 65mm（与参数表一致）
FOCAL_LEN_MM = 3.6   # 焦距 3.6mm
# 传感器尺寸：1/2.7'' 实际对角线约6.7mm，按16:9计算像素物理尺寸
SENSOR_WIDTH_MM = 5.2   # 近似值，更精确方法见下文
PIXEL_SIZE_MM = SENSOR_WIDTH_MM / 1920.0   # 单个像素宽度(mm)
FOCAL_LEN_PIX = FOCAL_LEN_MM / PIXEL_SIZE_MM   # 焦距对应的像素单位
# ----------------------------------------------------------------

# 从标定文件加载参数（若执行过标定脚本）
try:
    calib = np.load('stereo_calib.npz', allow_pickle=True)
    map1_l = calib['map1_l']
    map2_l = calib['map2_l']
    map1_r = calib['map1_r']
    map2_r = calib['map2_r']
    Q = calib['Q']          # 视差转深度的矩阵，优先使用
    baseline = float(calib['baseline'])
    # 如果能从Q矩阵中提取焦距和基线则优先
    fx = Q[2,3] if Q[2,3] != 0 else FOCAL_LEN_PIX
    cx = Q[0,3]
    cy = Q[1,3]
    print(f"加载标定文件成功，基线={baseline:.2f}mm，等效焦距fx={fx:.2f}像素")
except:
    print("未找到标定文件，将使用理论焦距和基线，但立体校正映射缺失，请先运行标定脚本！")
    exit()

# 图像尺寸（单目）
IMG_WIDTH, IMG_HEIGHT = 1920, 1080
FULL_WIDTH = IMG_WIDTH * 2   # 3840

# 打开USB相机（通常是设备0，也可能是1）
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FULL_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMG_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, 30)

# 创建立体匹配器（SGBM，效果较好）
window_size = 5
min_disp = 0          # 最小视差，通常为0
num_disp = 16*8       # 视差搜索范围，必须为16的倍数
block_size = 11       # 匹配块大小，奇数
stereo = cv2.StereoSGBM_create(
    minDisparity = min_disp,
    numDisparities = num_disp,
    blockSize = block_size,
    P1 = 8 * 3 * window_size ** 2,
    P2 = 32 * 3 * window_size ** 2,
    disp12MaxDiff = 1,
    uniquenessRatio = 10,
    speckleWindowSize = 100,
    speckleRange = 32,
    mode = cv2.STEREO_SGBM_MODE_SGBM_3WAY
)

def compute_depth_map(disp_map, fx, baseline, scale=16.0):
    """
    将原始视差图（单位为像素*16）转换为深度图（毫米）
    disp_map: SGBM输出的16倍视差图
    fx: 焦距（像素）
    baseline: 基线（毫米）
    """
    # 避免除零
    disp_map = np.float32(disp_map) / scale
    disp_map[disp_map <= 0.0] = 0.1
    depth_map = (fx * baseline) / disp_map
    return depth_map

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # 分割左右图像
    left_raw = frame[:, :IMG_WIDTH]
    right_raw = frame[:, IMG_WIDTH:]
    
    # 立体校正（使用预先计算的映射表）
    left_rect = cv2.remap(left_raw, map1_l, map2_l, cv2.INTER_LINEAR)
    right_rect = cv2.remap(right_raw, map1_r, map2_r, cv2.INTER_LINEAR)
    
    # 转为灰度图
    gray_left = cv2.cvtColor(left_rect, cv2.COLOR_BGR2GRAY)
    gray_right = cv2.cvtColor(right_rect, cv2.COLOR_BGR2GRAY)
    
    # 计算视差图
    disparity = stereo.compute(gray_left, gray_right).astype(np.float32)
    
    # 深度图（毫米）
    depth = compute_depth_map(disparity, fx, baseline)
    
    # 将深度图可视化（限制显示范围 0~5000mm）
    depth_vis = np.clip(depth / 5000.0 * 255, 0, 255).astype(np.uint8)
    depth_color = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)
    
    # 在左校正图上画一个十字并显示其距离
    center_x, center_y = IMG_WIDTH//2, IMG_HEIGHT//2
    cv2.circle(left_rect, (center_x, center_y), 5, (0,0,255), -1)
    distance = depth[center_y, center_x]
    cv2.putText(left_rect, f"{distance:.1f}mm", (center_x+10, center_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    
    # 显示结果
    cv2.imshow("Rectified Left", left_rect)
    cv2.imshow("Depth Map", depth_color)
    
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        cv2.imwrite("disparity.png", disparity/16)  # 保存视差图
        print("已保存视差图")

cap.release()
cv2.destroyAllWindows()
3. 使用说明
3.1 环境准备
bash
pip install opencv-python opencv-contrib-python numpy
3.2 标定步骤
打印一张国际象棋棋盘格（例如9×6内角点，方格边长25mm）。

运行标定脚本前，创建 calib_images 文件夹，将相机对准棋盘格从不同角度拍摄20~30张清晰照片（建议包含边缘和倾斜角度），保存为jpg/png。

注意：相机输出的是3840×1080的拼接图像，拍摄时需要保证整幅图像包含棋盘格（左右相机都能看到）。

修改标定脚本中的 CHESSBOARD_SIZE 和 SQUARE_SIZE 为实际值。

运行 python stereo_calibrate.py，等待标定完成。

3.3 实时测距
确保 stereo_calib.npz 与脚本在同一目录。

运行 python live_depth.py。

窗口中央显示当前距离（单位mm）。按 q 退出，按 s 保存当前视差图。

4. 核心公式说明
双目测距公式：

Depth
=
f
⋅
b
d
Depth= 
d
f⋅b
​
 
其中：

f
f：焦距（像素），由标定得到的 fx 给出。

b
b：基线（毫米），实际为左右相机光心距离，标定得到的平移向量 T[0] 即为基线。

d
d：视差（像素），SGBM输出值需要除以16后使用。

代码中 compute_depth_map 函数实现了该公式，最终深度单位为毫米。

5. 影响精度的因素及改进建议
标定质量：足够多的清晰、多角度棋盘格图像是精度的基础。建议使用15~25张。

立体匹配参数：numDisparities 和 blockSize 需要根据实际场景微调。对于近距离（<2米）可以减小视差范围来加快速度。

相机同步：该USB相机通常是同步输出的，但若出现图像撕裂，可降低分辨率或帧率（例如降到15fps）。

光线与纹理：避免纯色墙面或无纹理区域，必要时可投射结构光或使用主动双目技术。

手动调焦：使用前请确保左右镜头均已精确对焦，两图清晰度一致。

6. 常见问题
Q：运行实时测距时提示“未找到标定文件”？
A：请先严格按照标定脚本生成 stereo_calib.npz 文件。如果不想进行完整标定，可手动创建包含 map1_l, map2_l 等键的假数据，但强烈建议完成标定。

Q：深度图出现大量黑色（无效）区域？
A：可能是视差范围设置不够。增大 numDisparities（如改为 16*16）。另外确保左右相机已经立体校正完毕。

Q：如何获取画面中任意点的距离？
A：修改代码中的鼠标回调函数，读取对应坐标的 depth 值即可。示例未加入，可自行扩展。

以上代码已根据您提供的参数编写，只需完成标定即可获得真实的毫米级距离。如果对标定过程不熟悉，建议多拍摄几组棋盘格图像并保持环境光照均匀。

可以没有标定直接测距吗
用户想知道的是，是否可以在不进行标定的情况下，直接使用OpenCV进行双目测距。这可能涉及到相机参数（如焦距、基线）是否可用，以及是否可以实现近似测距。为了全面回答这个问题，我需要同时进行多项搜索，以覆盖不同的方面：一是关于无需标定的双目测距通用方法，二是关于OpenCV中无需标定的立体视觉，三是关于使用相机规格参数进行近似测距，四是关于维特相机是否可以直接使用，五是关于无需标定的快速测距方法，六是关于无标定的近似深度估计。

搜索到 33 个网页
搜索结果显示，一些可能相关的页面，但需要进一步查看。为了全面了解无标定双目测距的可能性，我们需要同时打开这些相关的页面。

浏览 6 个页面
基于双目视觉的运动物体实时跟踪与测距
CN120869043A_一种基于目标检测的双目及多目测距方法在审
Getting depth map from stereo pair?
https://homepage.ntu.edu.tw/~lgchen/publication/paper/[C][2013][ISCE][Cheng-Yuan.Ko][1].pdf#1#1
opencv::calib3d::stereo_rectify_uncalibrated
查看全部
这些结果提供了一些关于无标定测距的方法。我的回答将涵盖几种方法：使用已知的相机规格进行近似测距、使用未标定立体校正、基于深度学习的方法、以及特定应用的方法。我还会提及相关的OpenCV函数，并最后给出总结。

可以，但不建议，而且无法获得标准的绝对深度值。

不进行标定而直接测距，本质上是在使用一个“未校准”的系统。虽然可以通过一些方法绕过完整的标定流程，但这会牺牲精度，并且得到的结果是相对的或低精度的。下面为你拆解几种可行的路径，以及它们的原理和局限。

1. 直接使用理论参数（最接近你的需求）
这个方法最直接：直接使用相机规格表中的“焦距 (3.6mm) ”和“基线 (65mm)”作为已知的精确参数，代入双目测距公式 Depth = (f * b) / d 进行计算。

优点：流程最简单，代码改动最小。

缺点与风险：

焦距单位不一致：相机规格中的焦距 3.6mm 是光学物理焦距，而测距公式中的 f 需要的是以像素为单位的焦距。直接使用会导致结果完全错误。

未考虑畸变：实际镜头存在畸变，尤其是广角镜头。不进行校正，远处的物体会在图像中扭曲，导致视差 d 计算错误。

精度差：忽略了个体相机差异和安装误差，仅适用于对精度要求极低的原型验证或演示。

如何将焦距转换为像素单位？
你需要用以下公式将 3.6mm 转换为像素单位 f_pixel：
f_pixel = (焦距(mm) / 传感器宽度(mm)) * 图像宽度(像素)
你的相机是 1/2.7'' 传感器，其宽度大约为 5.3mm，图像宽度是 1920 像素。计算出的 f_pixel 大约是 (3.6 / 5.3) * 1920 ≈ 1304 像素。

2. 使用 OpenCV 的未标定立体校正（更优的起点）
OpenCV 提供了 cv2.stereoRectifyUncalibrated() 函数，专门用于未标定的双目测距场景。

原理：它通过分析左右两张图像中的特征点对，计算出两个单应性矩阵（Homography Matrices），直接对图像进行校正，使其满足立体匹配的极线约束。整个过程不需要知道相机内参和相对位置。

优点：

流程简化：省去了打印棋盘格和繁琐的标定采集过程。

自动适应：算法能自动适应相机的相对姿态和部分畸变。

缺点：

结果并非绝对深度：此方法得到的深度是相对于某个参考平面的，输出的深度图是一个比例值（scale）而非毫米级的绝对值。你需要一个已知距离的物体来反推出真实尺度的缩放因子。

对低纹理敏感：如果场景缺乏特征点（如白墙），算法可能失效。

3. 特定场景的“免标定”方法
如果你有非常具体的应用场景，可以设计专门的算法绕过标定。

基于已知目标测距：比如做人脸测距，可以先通过人脸检测算法定位人脸在左右图中的位置和大小，然后直接使用 Depth = (f * b) / d 或根据人脸像素大小估算距离。这种方法在特定场景下有效，但通常不具备通用性。

借助深度学习：近年来有像 DUSt3R 这样的新方法，可以直接从任意两张未标定的图像中，通过神经网络端到端地恢复出场景的3D结构和相机参数。这种方法非常前沿，但计算量大，可能不适合实时应用。

总结对比与建议
方法	是否需标定	能否获得绝对深度	精度	实现难度
使用理论参数	否	是，理论值	很低	非常简单
cv2.stereoRectifyUncalibrated()	否	否（需比例缩放）	中等	中等
完整双目标定	是	是	高	较复杂
深度学习（如DUSt3R）	否	是	较高	高
总的来说，跳过标定的代价是牺牲精度或通用性。对于学习或快速原型验证，上述方法是可行的。但如果是为了得到可靠的深度数据，进行完整的双目标定依然是性价比最高的选择。

你目前主要想实现哪种精度的测量？如果是做快速原型验证或教学演示，用理论参数跑通流程；如果需要较高精度的距离数据，建议还是走标定流程。

来个无标定测距的代码
我们理解用户需求：不进行标定，直接使用相机理论参数进行双目测距（即使用理论焦距和基线，忽略畸变和校正）。需要提供可直接运行的Python代码，使用OpenCV，基于之前的相机参数（3840x1080分辨率，基线65mm，焦距3.6mm，1/2.7''传感器）。代码包括：从USB读取图像，分割左右图，计算视差（SGBM或BM），使用理论参数计算深度并显示。

注意：因为未标定，没有立体校正步骤，因此左右图像可能未对准，视差计算会受影响。但用户明确要求无标定测距，我们就直接实现理论公式，并提供使用说明和注意事项。

下面是一个无标定、直接使用理论参数的双目测距代码。它不需要打印棋盘格，也不需要进行任何标定步骤，仅依赖相机参数表中的基线、焦距和传感器尺寸来估算距离。

python
import cv2
import numpy as np

# ================== 理论参数（来自您的相机规格表） ==================
BASELINE_MM = 65.0          # 基线 65mm
FOCAL_LEN_MM = 3.6          # 物理焦距 3.6mm
SENSOR_WIDTH_MM = 5.2       # 1/2.7" 传感器宽度约 5.2mm (不同厂家略有差异，可微调)
IMG_WIDTH = 1920            # 单目图像宽度（像素）
# 计算像素焦距 = (物理焦距 / 传感器宽度) * 图像宽度
FOCAL_LEN_PIX = (FOCAL_LEN_MM / SENSOR_WIDTH_MM) * IMG_WIDTH
print(f"理论像素焦距: {FOCAL_LEN_PIX:.2f} px")

# ================== 相机设置 ==================
FULL_WIDTH = 3840           # 左右拼接总宽度
FULL_HEIGHT = 1080          # 高度
CAMERA_INDEX = 0            # 设备号，可能为0或1

# 打开相机
cap = cv2.VideoCapture(CAMERA_INDEX)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FULL_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FULL_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, 30)

# ================== 立体匹配器 (SGBM) ==================
# 视差范围：根据基线65mm，最近测距约0.2m，最远5m设定
# 视差d = f*b / Z，Z=0.2m时 d≈ 1304*65/200 ≈ 424；Z=5m时 d≈16.9
# 设置搜索范围 minDisparity=0, numDisparities=16*32=512
window_size = 5
min_disp = 0
num_disp = 16 * 32   # 512，覆盖到424以上
block_size = 11

stereo = cv2.StereoSGBM_create(
    minDisparity=min_disp,
    numDisparities=num_disp,
    blockSize=block_size,
    P1=8 * 3 * window_size ** 2,
    P2=32 * 3 * window_size ** 2,
    disp12MaxDiff=1,
    uniquenessRatio=10,
    speckleWindowSize=100,
    speckleRange=32,
    mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
)

def compute_depth(disparity_map, f_pix, baseline_mm):
    """
    将视差图（原始输出为16倍视差）转换为深度图（毫米）
    """
    # 转换回真实视差
    disp = np.float32(disparity_map) / 16.0
    # 避免除零和负值
    disp[disp <= 0.0] = 0.1
    depth = (f_pix * baseline_mm) / disp
    return depth

print("开始无标定实时测距...")
print("按 'q' 退出，按 's' 保存当前视差图")

while True:
    ret, frame = cap.read()
    if not ret:
        print("无法读取相机，请检查设备号或连接")
        break

    # 分割左右图像
    left_raw = frame[:, :IMG_WIDTH]
    right_raw = frame[:, IMG_WIDTH:]

    # 转为灰度图（立体匹配需要）
    gray_left = cv2.cvtColor(left_raw, cv2.COLOR_BGR2GRAY)
    gray_right = cv2.cvtColor(right_raw, cv2.COLOR_BGR2GRAY)

    # 计算视差图
    disparity = stereo.compute(gray_left, gray_right)

    # 计算深度图（毫米）
    depth_map = compute_depth(disparity, FOCAL_LEN_PIX, BASELINE_MM)

    # 为便于显示，将深度值裁剪到 0~5000mm 并映射为彩色图
    depth_vis = np.clip(depth_map / 5000.0 * 255, 0, 255).astype(np.uint8)
    depth_color = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)

    # 在左图上画十字并显示中心点的距离
    center_x, center_y = IMG_WIDTH//2, FULL_HEIGHT//2
    distance = depth_map[center_y, center_x]
    # 在左图像上绘制
    left_with_text = left_raw.copy()
    cv2.circle(left_with_text, (center_x, center_y), 5, (0,0,255), -1)
    cv2.putText(left_with_text, f"{distance:.1f} mm", (center_x+10, center_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    # 显示结果
    cv2.imshow("Left Image + Distance", left_with_text)
    cv2.imshow("Depth Map (color)", depth_color)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        cv2.imwrite("disparity_raw.png", disparity)
        cv2.imwrite("depth_raw.png", depth_map / np.max(depth_map) * 255)
        print("已保存视差图和深度图")

cap.release()
cv2.destroyAllWindows()
⚠️ 重要说明（无标定的局限）
精度较低
因为没有进行立体校正和畸变校正，左右图像在垂直方向上可能存在未对准，导致视差计算错误，最终深度值会有较大误差（可能偏差 20%~50%）。

有效测距范围
理论公式 Z = f*b/d 仍然成立，但实际能准确计算的范围受限于视差搜索范围（当前设置 numDisparities=512，最近约 0.2m，最远约 5m）。如果物体太近（<0.2m）或太远（>5m），视差会超出范围或过小，深度会不准确或无效。

传感器宽度参数需要微调
代码中 SENSOR_WIDTH_MM = 5.2 是典型 1/2.7" 传感器的宽度。不同厂商可能有细微差异（5.0~5.5mm），如果发现距离总是系统性偏大或偏小，可以调整此值。例如，如果测出 1 米远的物体显示 1.2 米，可以减小传感器宽度（如改为 4.5）来修正。

没有处理镜头畸变
相机尤其是广角镜头存在明显畸变，边缘区域的视差计算会严重失真，建议只关注图像中央区域的测量值。

必须手动对焦
确保两个镜头都已准确对焦，且左右图像清晰度一致。如果模糊，立体匹配会失败。

如何简单验证是否工作？
找一个距离相机大约 1 米（用卷尺量）的物体（例如一面纹理丰富的墙壁）。

运行代码，观察屏幕中央显示的距离数值，看是否接近 1000 mm。

如果偏差很大，尝试调整 SENSOR_WIDTH_MM（例如改为 4.8 或 5.5）。

如果希望稍微提高一点准确度（仍不标定）
可以加入 OpenCV 的图像校正步骤，使用 cv2.stereoRectifyUncalibrated 函数，但那样仍不需要标定板，而是通过实时图像中的特征点自动计算校正矩阵。需要额外代码，但会提升精度。如果需要该增强版本，请告诉我。

当前版本是完全无标定、最简单直接的实现，适合快速体验双目测距原理。

用800x600分辨率
我们注意到用户要求用800x600分辨率。原相机支持多种分辨率，其中MJPEG 1600x600 30FPS等。用户需要将分辨率改为800x600（可能是单目800x600，双目总宽1600）。需要调整代码中的图像尺寸参数。

需要修改：单目宽度/高度，总宽度。注意相机是否支持800x600？可以尝试设置分辨率，但不一定支持。用户可以选用640x240或其他。但既然用户要求800x600，我们可以按此编写，同时提示如果相机不支持请调整。

修改代码中的 IMG_WIDTH, IMG_HEIGHT, FULL_WIDTH。另外焦距像素计算也要根据新的宽度重新计算：焦距像素 = (物理焦距/传感器宽度)*图像宽度。

提供修改后的代码。

根据您的要求，将分辨率改为 800×600（单目），双目拼接图像总尺寸为 1600×600。代码已相应调整，包括：

图像尺寸、焦距像素重新计算。

匹配参数根据较低分辨率微调。

保留所有无标定测距逻辑。

python
import cv2
import numpy as np

# ================== 理论参数 ==================
BASELINE_MM = 65.0          # 基线 65mm
FOCAL_LEN_MM = 3.6          # 物理焦距 3.6mm
SENSOR_WIDTH_MM = 5.2       # 1/2.7" 传感器宽度约 5.2mm
IMG_WIDTH = 800             # 单目图像宽度（像素）
IMG_HEIGHT = 600            # 单目图像高度（像素）
# 根据新的分辨率计算像素焦距
FOCAL_LEN_PIX = (FOCAL_LEN_MM / SENSOR_WIDTH_MM) * IMG_WIDTH
print(f"理论像素焦距 (800x600): {FOCAL_LEN_PIX:.2f} px")

# ================== 相机设置 ==================
FULL_WIDTH = IMG_WIDTH * 2   # 1600
FULL_HEIGHT = IMG_HEIGHT     # 600
CAMERA_INDEX = 0             # 设备号，可能为0或1

cap = cv2.VideoCapture(CAMERA_INDEX)
# 尝试设置分辨率（相机可能不支持1600x600，若不支持则使用默认，需自行调整）
cap.set(cv2.CAP_PROP_FRAME_WIDTH, FULL_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FULL_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, 30)

# 检查实际设置的分辨率
actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
print(f"实际相机分辨率: {actual_width} x {actual_height}")
if actual_width != FULL_WIDTH or actual_height != FULL_HEIGHT:
    print("警告: 相机不支持1600x600，将使用实际分辨率，请手动调整代码中的IMG_WIDTH/HEIGHT")

# ================== 立体匹配器 (SGBM) ==================
# 视差范围计算: Z_min = 0.2m => d_max = f*b/200 ≈ 1304*65/200 ≈ 424
# 800宽度下像素焦距减小，d_max ≈ (1304*800/1920)*65/200 ≈ (543)*65/200 ≈ 176
# 所以设置 numDisparities = 16*16 = 256 足够
window_size = 3              # 分辨率降低，窗口可以小一点
min_disp = 0
num_disp = 16 * 16           # 256
block_size = 9               # 奇数，可调

stereo = cv2.StereoSGBM_create(
    minDisparity=min_disp,
    numDisparities=num_disp,
    blockSize=block_size,
    P1=8 * 3 * window_size ** 2,
    P2=32 * 3 * window_size ** 2,
    disp12MaxDiff=1,
    uniquenessRatio=10,
    speckleWindowSize=100,
    speckleRange=32,
    mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
)

def compute_depth(disparity_map, f_pix, baseline_mm):
    """将视差图（16倍）转换为深度图（毫米）"""
    disp = np.float32(disparity_map) / 16.0
    disp[disp <= 0.0] = 0.1
    depth = (f_pix * baseline_mm) / disp
    return depth

print("开始无标定实时测距 (800x600)...")
print("按 'q' 退出，按 's' 保存视差图")

while True:
    ret, frame = cap.read()
    if not ret:
        print("无法读取相机，请检查设备号或连接")
        break

    # 如果相机实际分辨率与设定不一致，需重新调整切分点；这里假设实际为1600x600
    h, w = frame.shape[:2]
    if w != FULL_WIDTH or h != FULL_HEIGHT:
        # 若相机不支持设定分辨率，按实际宽度的左半和右半切分（假设左右等宽）
        half = w // 2
        left_raw = frame[:, :half]
        right_raw = frame[:, half:]
        # 可选: 缩放到目标分辨率
        if left_raw.shape[1] != IMG_WIDTH:
            left_raw = cv2.resize(left_raw, (IMG_WIDTH, IMG_HEIGHT))
            right_raw = cv2.resize(right_raw, (IMG_WIDTH, IMG_HEIGHT))
    else:
        left_raw = frame[:, :IMG_WIDTH]
        right_raw = frame[:, IMG_WIDTH:]

    # 转为灰度图
    gray_left = cv2.cvtColor(left_raw, cv2.COLOR_BGR2GRAY)
    gray_right = cv2.cvtColor(right_raw, cv2.COLOR_BGR2GRAY)

    # 计算视差图
    disparity = stereo.compute(gray_left, gray_right)

    # 深度图
    depth_map = compute_depth(disparity, FOCAL_LEN_PIX, BASELINE_MM)

    # 可视化深度图（0~5000mm映射到0~255）
    depth_vis = np.clip(depth_map / 5000.0 * 255, 0, 255).astype(np.uint8)
    depth_color = cv2.applyColorMap(depth_vis, cv2.COLORMAP_JET)

    # 在左图上显示中心点距离
    center_x, center_y = IMG_WIDTH // 2, IMG_HEIGHT // 2
    distance = depth_map[center_y, center_x]
    left_with_text = left_raw.copy()
    cv2.circle(left_with_text, (center_x, center_y), 5, (0, 0, 255), -1)
    cv2.putText(left_with_text, f"{distance:.1f} mm", (center_x + 10, center_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # 显示
    cv2.imshow("Left + Distance", left_with_text)
    cv2.imshow("Depth Map", depth_color)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        cv2.imwrite("disparity_800x600.png", disparity)
        print("已保存视差图")

cap.release()
cv2.destroyAllWindows()
📌 分辨率说明与调整建议
相机是否支持 1600×600？
您的相机参数表中支持 1600×600 @ 30fps（MJPEG/YUY2），所以该分辨率是原生支持的，代码中的 cap.set 应该能成功。如果实际获得的分辨率不符，请检查驱动或尝试其他分辨率（如 1280×480）。

焦距像素计算
当图像宽度从 1920 降到 800，像素焦距等比例减小：

text
FOCAL_LEN_PIX(1920) ≈ 1304
FOCAL_LEN_PIX(800)  = 1304 * (800/1920) ≈ 543
代码已自动根据 IMG_WIDTH 重新计算。

视差搜索范围
由于分辨率降低，最大视差也相应减小（约 176 像素），设置 numDisparities=256 足够覆盖 0~200 像素范围，同时也提高了计算速度。

性能
800×600 的双目匹配计算量远小于 1920×1080，在普通 CPU 上也能达到 15~30fps。

🧪 验证方法
将相机对准一个距离约 1 米的物体（如墙面、纸箱），观察屏幕中央显示的距离数值是否接近 1000mm。如果偏差较大，可微调 SENSOR_WIDTH_MM（典型范围 5.0~5.5）。例如：

测得值偏大 → 减小 SENSOR_WIDTH_MM

测得值偏小 → 增大 SENSOR_WIDTH_MM

如果需要进一步提高精度（仍无需标定板），可以使用 cv2.stereoRectifyUncalibrated 进行自动校正，我可以为您提供增强版代码。

只能测中心点的距离吗
我们被问到“只能测中心点的距离吗？”用户希望知道是否只能测量中心点，还是可以测量任意点。我们需要解释代码中演示的是中心点，但可以修改为任意点（比如鼠标点击）。回答应该说明如何修改代码来获取任意点的距离，给出示例代码片段。

另外，要基于之前的无标定测距代码。回答要友好、实用。

不是的，代码示例中只演示了中心点的距离，但你可以轻松修改为测量图像中任意点的距离。

只需要获取鼠标点击的坐标，然后从深度图中读取该坐标处的深度值即可。下面是一个增强版的代码片段，它在左图像上添加鼠标回调功能：点击画面任意位置，就会在控制台打印该点的距离，并在图像上显示。

修改后的核心代码（在之前的 800×600 无标定代码基础上增加）
python
# 全局变量存放深度图
current_depth_map = None

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        if current_depth_map is not None and 0 <= y < current_depth_map.shape[0] and 0 <= x < current_depth_map.shape[1]:
            distance = current_depth_map[y, x]
            print(f"点击坐标 ({x}, {y}) 处的距离: {distance:.1f} mm")
            # 也可以在画面上临时显示文本，但需要实时刷新，更简单的是打印出来

# 在 cv2.imshow 之前添加窗口和回调
cv2.namedWindow("Left + Distance")
cv2.setMouseCallback("Left + Distance", mouse_callback)

# 然后在主循环中，每帧更新 current_depth_map
while True:
    # ... 计算 depth_map ...
    current_depth_map = depth_map   # 更新全局深度图
    
    # ... 显示 left_with_text 和 depth_color ...
    cv2.imshow("Left + Distance", left_with_text)
完整示例（整合到之前的无标定代码中）
python
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
关键点说明
cv2.setMouseCallback 将鼠标点击事件绑定到指定窗口。

在回调函数中，通过全局变量 current_depth 访问最新的深度图。

点击后，控制台会打印 (x, y) 坐标处的距离（单位：mm）。

你也可以在图像上动态绘制点击位置和距离，但为了代码清晰，此处仅打印。

扩展想法
连续显示跟随鼠标的距离：可以使用 cv2.EVENT_MOUSEMOVE 在鼠标移动时实时更新显示的文本。

保存点击坐标的距离：将坐标和距离写入 CSV 文件，方便记录。

限制有效距离：可以在深度图上设置一个阈值（如 200~5000mm），超出范围的标记为无效。

总之，双目测距可以得到整幅图像每个像素的深度值，只需从深度图中索引你想查询的点即可。

生成标准标定棋盘文件方便打印
我们生成一个标准标定棋盘格图像，可打印用于相机标定。需要提供可打印的PDF或图片，通常棋盘格有黑白方格，内角点数可选（如9x6、7x5等）。用户需要“生成标准标定棋盘文件”，输出应是一张图像，最好带尺寸说明。由于这里是文本对话，无法直接生成文件，但可以给出Python代码，让用户运行生成棋盘格图像（如PNG），并可调整参数（方格大小、内角点数）。同时给出打印建议。

注意：用户要求“方便打印”，所以需要明确打印尺寸，例如每个方格25mm或30mm等。建议提供代码和说明。

我将写出一个Python脚本，使用OpenCV生成棋盘格图像，并保存为图片或PDF。提供多种尺寸选项。

由于对话环境无法直接生成文件，我为您提供一段 Python 代码，运行后即可生成一张高精度的棋盘格标定板图像（PNG），您可以直接打印使用。

代码中可自定义：

内角点数（如 9×6）

单个方格边长（毫米）

打印分辨率（DPI）

生成图片后，按实际打印尺寸（例如每个方格 25mm）打印在平整的硬纸板或亚光相纸上即可。

python
import cv2
import numpy as np

# ========== 参数设置 ==========
# 棋盘格内角点数（列数, 行数）
chess_cols = 9   # 横向内角点数量
chess_rows = 6   # 纵向内角点数量

# 每个方格的物理尺寸（毫米）
square_size_mm = 25

# 输出图片的 DPI（用于指导打印，像素 = 毫米 * DPI / 25.4）
dpi = 300

# 添加白边（毫米）
margin_mm = 15

# 计算图像尺寸（像素）
# 棋盘格实际宽度 = (chess_cols+1) * square_size_mm  因为内角点数量比方格数少1
board_width_mm = (chess_cols + 1) * square_size_mm
board_height_mm = (chess_rows + 1) * square_size_mm

total_width_mm = board_width_mm + 2 * margin_mm
total_height_mm = board_height_mm + 2 * margin_mm

px_per_mm = dpi / 25.4
img_width = int(total_width_mm * px_per_mm)
img_height = int(total_height_mm * px_per_mm)

# 计算每个方格在图像中的像素边长
square_px = int(square_size_mm * px_per_mm)

print(f"生成棋盘格：{chess_cols+1} x {chess_rows+1} 个方格")
print(f"方格实际尺寸：{square_size_mm} mm × {square_size_mm} mm")
print(f"图像总尺寸：{img_width} x {img_height} 像素，{total_width_mm:.1f} x {total_height_mm:.1f} mm")
print(f"建议打印分辨率：{dpi} DPI，每方格边长 = {square_px} 像素")
print("打印时请确保打印尺寸与实际毫米尺寸一致，不要缩放！")

# 创建白色背景图像
img = np.ones((img_height, img_width), dtype=np.uint8) * 255

# 计算棋盘格起始坐标（居中）
start_x = int(margin_mm * px_per_mm)
start_y = int(margin_mm * px_per_mm)

# 绘制黑色方格
for row in range(chess_rows + 1):
    for col in range(chess_cols + 1):
        # 方格颜色：当 (行+列) 为偶数时画黑色
        if (row + col) % 2 == 0:
            x1 = start_x + col * square_px
            y1 = start_y + row * square_px
            x2 = x1 + square_px
            y2 = y1 + square_px
            cv2.rectangle(img, (x1, y1), (x2, y2), 0, -1)

# 可选：在四角添加标记圆点（辅助识别方向）
# 这里不强制添加，保持标准棋盘格

# 保存图片
filename = f"chessboard_{chess_cols+1}x{chess_rows+1}_{square_size_mm}mm_{dpi}dpi.png"
cv2.imwrite(filename, img)
print(f"棋盘格图片已保存为：{filename}")

# 同时生成一个 PDF 版本（需要 img2pdf 库，如未安装可注释）
try:
    import img2pdf
    with open(filename.replace('.png', '.pdf'), 'wb') as f:
        f.write(img2pdf.convert(filename))
    print("PDF 版本也已生成")
except ImportError:
    print("如需 PDF 输出，请安装 img2pdf：pip install img2pdf")
使用说明
安装依赖（只需 opencv-python 和 numpy）：

bash
pip install opencv-python numpy
如果想输出 PDF，再安装 img2pdf。

运行脚本：

bash
python generate_chessboard.py
会在当前目录生成 PNG 图片，文件名包含尺寸和 DPI 信息。

打印注意事项：

打印时务必 禁用“缩放以适合”，选择 实际大小 或 100% 尺寸。

使用 亚光相纸 或 普通纸贴在硬平板上，确保表面平整，无反光。

用直尺测量打印出的一个方格边长，确认是否为设定的 square_size_mm（如 25mm）。若有偏差，调整打印设置或微调代码中的 DPI 和毫米参数。

常见尺寸推荐
内角点数	方格边长	棋盘格大小	适用场景
9×6	25mm	约 250×175mm	小视野、近距离标定
9×6	30mm	约 300×210mm	通用标定
7×5	30mm	约 240×180mm	视野较小的相机
11×8	20mm	约 240×180mm	高精度、密集角点
对于您的维特 400W 双目相机（分辨率 3840×1080，FOV 90°），推荐使用 9×6 内角点，方格边长 25mm 或 30mm，打印在 A4 纸上即可，但要保证整个棋盘格充满左右相机的画面。

检查打印质量
用手机拍一张打印的棋盘格照片，放大检查边缘是否清晰、黑白对比是否明显。

将棋盘格放置在相机前不同角度、距离拍摄 20~30 张用于标定（标定代码见前面回答）。

如果您需要特定格式（如带有方向标识的圆形棋盘格或 ChArUco 板），我可以再提供相应生成代码。

