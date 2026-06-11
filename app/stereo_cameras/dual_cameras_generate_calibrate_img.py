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