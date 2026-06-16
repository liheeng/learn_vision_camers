from ultralytics import YOLO

model = YOLO("./model/yolov8n.pt")

results = model.predict(
    source="https://ultralytics.com/images/bus.jpg",
    device="mps",
)

print(results[0].speed)