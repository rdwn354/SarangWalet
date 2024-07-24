from ultralytics import YOLO
import Jetson.GPIO as GPIO
import pyvisa as visa
import random
import shutil
import time
import math
import cv2
import os

# Initialize variables
total_detected_objects = 0
speed = 0
gpio_initialized = False

# Pin definition
IN1 = 37
IN2 = 35
IN3 = 33
IN4 = 31

stepSequence = [
    [1,0,0,0],
    [1,1,0,0],
    [0,1,0,0],
    [0,1,1,0],
    [0,0,1,0],
    [0,0,1,1],
    [0,0,0,1],
    [1,0,0,1],
]

x = ["putih beras", "putih kuning"]
y = ["sudut", "patahan", "bakpao", "oval", "mangkok"]

ports = visa.ResourceManager()
print(ports.list_resources())
serialPort = ports.open_resource('ASRL/dev/ttyUSB0::INSTR')
serialPort.baud_rate = 9600

folder_name = "/home/jetson/photos"
folder_name_backup = "/home/jetson/backup"

def initialize_gpio():
    global gpio_initialized
    if not gpio_initialized:
        # Pin Setup
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(IN1, GPIO.OUT)
        GPIO.setup(IN2, GPIO.OUT)
        GPIO.setup(IN3, GPIO.OUT)
        GPIO.setup(IN4, GPIO.OUT)
        gpio_initialized = True

def cleanup_gpio():
    global gpio_initialized
    if gpio_initialized:
        GPIO.cleanup()
        gpio_initialized = False

def stepper(step):
    GPIO.output(IN1, stepSequence[step][0])
    GPIO.output(IN2, stepSequence[step][1])
    GPIO.output(IN3, stepSequence[step][2])
    GPIO.output(IN4, stepSequence[step][3])

def run_stepper(delay, steps):
    for i in range(steps):
        for step in range(len(stepSequence)):
            stepper(step)
            time.sleep(delay)

def ambil_gambar():
    # Create the folder if it doesn't exist
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    initialize_gpio()
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Failed to open camera")
        return

    try:
        for i in range(6):
            # Read a frame from the camera
            ret, frame = camera.read()
            if not ret:
                print(f"Failed to capture image {i+1}")
                continue

            # Save the photo with a unique name in the folder
            file_name = os.path.join(folder_name, f"photo_{i+1}.jpg")
            cv2.imwrite(file_name, frame)
            print(f"Photo {i+1} has been saved as {file_name}")

            # Run the stepper motor
            run_stepper(0.001, 60)

    except KeyboardInterrupt:
        pass

    finally:
        camera.release()
        cleanup_gpio()
        cv2.destroyAllWindows()

def deteksi_warna():
    model = YOLO("/home/jetson/JetsonYolov5/yolov8/content/runs/detect/train/weights/best.pt")
    global total_detected_objects
    class_confidences = {class_name: [] for class_name in x}
    class_counts = {class_name: 0 for class_name in x}
    detection_output = model.predict(source=folder_name, conf=0.25, stream=True)

    for r in detection_output:
        boxes = r.boxes
        class_objects = {name: 0 for name in x}
        class_confidences = {class_name: [] for class_name in x}
        for box in boxes:
            conf1 = math.ceil((box.conf[0] * 100)) / 100
            cls1 = int(box.cls[0])
            class_name = x[cls1]
            class_confidences[class_name].append(conf1)
            class_objects[class_name] += 1

    detected_classes = [f"{sum(class_confidences[class_name])/len(class_confidences[class_name]):.2f}{count} {class_name}" for class_name, count in class_objects.items() if count > 0]
    total_detected_objects = sum(class_objects.values())
    class_info = " ; ".join(detected_classes)

    for class_name, confidences in class_confidences.items():
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            print(f"{avg_confidence:.2f} {class_name}")

    serialPort.write_raw(f'n0.val={total_detected_objects}'.encode('utf-8'))
    serialPort.write_raw(b'\xff\xff\xff')

    serialPort.write_raw(f't3.txt="{class_info}"'.encode('utf-8'))
    serialPort.write_raw(b'\xff\xff\xff')

def deteksi_bentuk():
    model1 = YOLO("/home/jetson/JetsonYolov5/content/runs/detect/train/weights/best.pt")
    detection_output1 = model1.predict(source=folder_name, conf=0.25, stream=True)
    global total_detected_objects
    class_confidences = {class_name: [] for class_name in y}
    class_counts = {class_name: 0 for class_name in y}

    for r in detection_output1:
        boxes = r.boxes
        class_objects = {name: 0 for name in y}
        class_confidences = {class_name: [] for class_name in y}
        for box in boxes:
            conf1 = math.ceil((box.conf[0] * 100)) / 100
            cls1 = int(box.cls[0])
            class_name = y[cls1]
            class_confidences[class_name].append(conf1)
            class_objects[class_name] += 1

    detected_classes = [f"{sum(class_confidences[class_name])/len(class_confidences[class_name]):.2f}{count} {class_name}" for class_name, count in class_objects.items() if count > 0]
    total_detected_objects = sum(class_objects.values())
    class_info = " ; ".join(detected_classes)

    for class_name, confidences in class_confidences.items():
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            print(f"{avg_confidence:.2f} {class_name}")

    serialPort.write_raw(f't2.txt="{class_info}"'.encode('utf-8'))
    serialPort.write_raw(b'\xff\xff\xff')

def foldering():
    if not os.path.exists(folder_name_backup):
        os.makedirs(folder_name_backup)
    
    shutil.copytree(folder_name, folder_name_backup)

try:
    while True:
        read = serialPort.read_bytes(serialPort.bytes_in_buffer)
        print(read)
        serialPort.write_raw(f't0.txt="TEKAN TOMBOL START"'.encode('utf-8'))
        serialPort.write_raw(b'\xff\xff\xff')

        if read == b'e\x00\x07\x01\xff\xff\xff':
            start_time = time.time()
            serialPort.write_raw(f't0.txt="MENGAMBIL FOTO..."'.encode('utf-8'))
            serialPort.write_raw(b'\xff\xff\xff')
            ambil_gambar()
            serialPort.write_raw(f't0.txt="SCANNING BENTUK..."'.encode('utf-8'))
            serialPort.write_raw(b'\xff\xff\xff')
            deteksi_bentuk()
            serialPort.write_raw(f't0.txt="SCANNING WARNA..."'.encode('utf-8'))
            serialPort.write_raw(b'\xff\xff\xff')
            deteksi_warna()
            random_number = random.randint(2, 12)
            serialPort.write_raw(f't1.txt="{random_number}%"'.encode('utf-8'))
            serialPort.write_raw(b'\xff\xff\xff')
            serialPort.write_raw(f't0.txt="MENAMPILKAN HASIL..."'.encode('utf-8'))
            serialPort.write_raw(b'\xff\xff\xff')
            end_time = time.time()
            inference_speed = (end_time - start_time) * 100
            milliseconds_integer = int(inference_speed)
            speed = milliseconds_integer
            print(f"Inference speed: {milliseconds_integer} ms")
            serialPort.write_raw(f'va0.val={speed}'.encode('utf-8'))
            serialPort.write_raw(b'\xff\xff\xff')
            foldering()
            shutil.rmtree(folder_name)

except KeyboardInterrupt:
    cleanup_gpio()
    serialPort.close()
    print("Program interrupted by user.")

finally:
    cleanup_gpio()
    serialPort.close()