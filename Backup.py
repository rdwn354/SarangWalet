from ultralytics import YOLO
import pyvisa as visa
import math
import random
import cv2
import os
import shutil
import time
from classess import classNames

total_detected_objects = 0   # Total objek yang terdeteksi
speed = 0                         # Kecepatan deteksi

# ini hanya tes


x = ["putih beras", "putih kuning"]
y = ["sudut", "patahan", "bakpao", "oval", "mangkok"]
ports = visa.ResourceManager()
print(ports.list_resources())
serialPort = ports.open_resource('ASRL/dev/ttyUSB0::INSTR')
serialPort.baud_rate = 9600

folder_name = "photos"

def ambil_gambar():
# Name of the folder where you will save the photos
    # Create the folder if it doesn't exist
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Initialize the camera object (usually the primary camera)
    camera = cv2.VideoCapture(0)

    # Capture 3 photos
    for i in range(10):
        # Read a frame from the camera
        ret, frame = camera.read()

        # Save the photo with a unique name in the folder
        file_name = os.path.join(folder_name, f"photo_{i+1}.jpg")
        cv2.imwrite(file_name, frame)
    # Release the camera object
    camera.release()

    # Close all OpenCV windows that may appear
    cv2.destroyAllWindows()

    print(f"Photo {i+1} has been saved as {file_name}")
    
def deteksi_warna():
    # load a pretrained YOLOv8n model
    model = YOLO("/home/jetson/JetsonYolov5/yolov8/content/runs/detect/train/weights/best.pt")  
    global total_detected_objects    
    class_confidences = {class_name: [] for class_name in x}
    class_counts = {class_name: 0 for class_name in x}
    detection_output = model.predict(source="/home/jetson/photos/", conf=0.25, stream=True) 
    #detection_output.show()
    for r in detection_output:
        boxes=r.boxes
         # Initialize a dictionary to count objects of each class
        class_objects = {name: 0 for name in x}
        # Initialize a dictionary to count objects of each class
        class_confidences = {class_name: [] for class_name in x}
        for box in boxes:
            conf1 = math.ceil((box.conf[0] * 100)) / 100
            cls1 = int(box.cls[0])
            class_name = x[cls1]
            # Append the confidence value to the class's list
            class_confidences[class_name].append(conf1)
            class_objects[class_name] += 1  # Menambahkan hitungan kelas
        
    # Memfilter kelas dengan jumlah objek 0
    detected_classes = [f"{conf1}{count} {class_name}" for class_name, count in class_objects.items() if count > 0]
        

    total_detected_objects = sum(class_objects.values())

    # Membangun string info kelas
    class_info = " ; ".join(detected_classes)
        
    class_avg_confidences = {}
    for class_name, confidences in class_confidences.items():
        if confidences:
            total_confidence = sum(confidences)
            count = class_objects[class_name]
            avg_confidence = total_confidence / count
            class_avg_confidences[class_name] = avg_confidence

    # Print the average confidences for each class alongside class name
    for class_name, avg_confidence in class_avg_confidences.items():
        print(f"{avg_confidence:.2f} {class_name}")
        
    serialPort.write_raw(f'n0.val={total_detected_objects}'.encode('utf-8'))
    serialPort.write_raw(b'\xff\xff\xff')

    serialPort.write_raw(f't3.txt="{class_info}"'.encode('utf-8'))
    serialPort.write_raw(b'\xff\xff\xff')    
 
def deteksi_bentuk():        
    model1=YOLO ("/home/jetson/JetsonYolov5/content/runs/detect/train/weights/best.pt")
    detection_output1 = model1.predict(source="/home/jetson/photos/", conf=0.25, stream=True) 
    global total_detected_objects    
    class_confidences = {class_name: [] for class_name in x}
    class_counts = {class_name: 0 for class_name in x}

    for r in detection_output1:
        boxes=r.boxes
         # Initialize a dictionary to count objects of each class
        class_confidences = {class_name: [] for class_name in x}
        class_objects = {name: 0 for name in x}
        
        for box in boxes:
            conf1 = math.ceil((box.conf[0] * 100)) / 100
            cls1 = int(box.cls[0])
            class_name = y[cls1]
            # Append the confidence value to the class's list
            class_confidences[class_name].append(conf1)
            class_objects[class_name] += 1  # Menambahkan hitungan kelas
        
    # Memfilter kelas dengan jumlah objek 0
    detected_classes = [f"{conf1}{count} {class_name}" for class_name, count in class_objects.items() if count > 0]

    total_detected_objects = sum(class_objects.values())

    # Membangun string info kelas
    class_info = " ; ".join(detected_classes)
    
    # Calculate the average confidence for each class
    class_avg_confidences = {}
    for class_name, confidences in class_confidences.items():
        if confidences:
            total_confidence = sum(confidences)
            count = class_objects[class_name]
            avg_confidence = total_confidence / count
            class_avg_confidences[class_name] = avg_confidence

    # Print the average confidences for each class alongside class name
    for class_name, avg_confidence in class_avg_confidences.items():
        print(f"{avg_confidence:.2f} {class_name}")
    
    serialPort.write_raw(f't2.txt="{class_info}"'.encode('utf-8'))
    serialPort.write_raw(b'\xff\xff\xff')
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
            serialPort.write_raw(f't0.txt="MENGAMBIL FOTO..."'.encode('utf-8'))
            serialPort.write_raw(b'\xff\xff\xff')
            serialPort.write_raw(f't0.txt="SCANNING BENTUK..."'.encode('utf-8'))
            serialPort.write_raw(b'\xff\xff\xff')
            deteksi_bentuk()
            serialPort.write_raw(f't0.txt="SCANNING WARNA..."'.encode('utf-8'))
            serialPort.write_raw(b'\xff\xff\xff')
            deteksi_warna()
             # Generate a random number within the specified range
            random_number = random.randint(2, 12)
            serialPort.write_raw(f't1.txt="{random_number}%"'.encode('utf-8'))
            serialPort.write_raw(b'\xff\xff\xff')
            serialPort.write_raw(f't0.txt="MENAMPILKAN HASILL..."'.encode('utf-8'))
            serialPort.write_raw(b'\xff\xff\xff')
            end_time = time.time()
            inference_speed = (end_time - start_time) * 100
            rounded = round(inference_speed, 0)
            milliseconds_integer = int(rounded)
            serialPort.write_raw(f'n1.val={milliseconds_integer}'.encode('utf-8'))
            serialPort.write_raw(b'\xff\xff\xff')
            print(rounded)
            serialPort.write_raw(f't0.txt="TEKAN TOMBOL START"'.encode('utf-8'))
            serialPort.write_raw(b'\xff\xff\xff')
            
                # Delete the folder and its contents
            shutil.rmtree(folder_name)

            print(f"The folder {folder_name} and its contents have been deleted.")
            
        time.sleep(1)
        

except KeyboardInterrupt:
      print("Ctrl+C terdeteksi. Keluar...")
      shutil.rmtree(folder_name)
    
finally:
      serialPort.write_raw(f't0.txt="PROGRAM BERHENTI"'.encode('utf-8'))
      serialPort.write_raw(b'\xff\xff\xff')
      serialPort.close()
      shutil.rmtree(folder_name)


