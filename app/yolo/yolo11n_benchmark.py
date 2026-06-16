import time
from ultralytics import YOLO

model = YOLO("./model/yolo11n.pt")
model.to("mps")

# 预热
for _ in range(10):
    model.predict(
        "https://ultralytics.com/images/bus.jpg",
        device="mps",
        verbose=False
    )

start = time.time()

for _ in range(100):
    model.predict(
        "https://ultralytics.com/images/bus.jpg",
        device="mps",
        verbose=False
    )

elapsed = time.time() - start

print("FPS =", 100 / elapsed)