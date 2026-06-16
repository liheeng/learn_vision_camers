from ultralytics import YOLO

model = YOLO("./model/yolo11n.pt")

results = model.predict(
    source="https://ultralytics.com/images/bus.jpg",
    device="mps",
)

print(results[0].speed)