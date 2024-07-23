from ultralytics import YOLO
import cv2
import pyvisa as visa
import time
import threading
import subprocess 
import math
import imutils
from classess import classNames

# Inisialisasi variabel-variabel
loop_jalan = False               # Status loop deteksi aktif/non-aktif
program_running = True           # Status program berjalan/berhenti
total_detected_objects = 0       # Total objek yang terdeteksi
speed = 0                         # Kecepatan deteksi

# Deklarasi array kelas objek
x = classNames
Y = classNames

# Jenis font untuk teks pada gambar
font = cv2.FONT_HERSHEY_SIMPLEX

# Inisialisasi komunikasi serial
ports = visa.ResourceManager()
print(ports.list_resources())     # Daftar sumber daya serial yang tersedia
serialPort = ports.open_resource('ASRL/dev/ttyUSB0::INSTR')
serialPort.baud_rate = 9600       # Pengaturan baud rate

# Inisialisasi model YOLO
model1 = None
model2 = None

# Inisialisasi kamera
cap = cv2.VideoCapture(0)

# Fungsi untuk membaca dan proses data serial
def read_serial():
    global loop_jalan, program_running, model1, model2

    while program_running:  # Melanjutkan membaca data serial selama program berjalan
        read = serialPort.read_bytes(serialPort.bytes_in_buffer)
        print(read)

        # Mengecek apakah tombol "stop" ditekan
        if read == b'e\x00\x04\x01\xff\xff\xff':
            if loop_jalan:  # Jika loop deteksi sedang berjalan
                loop_jalan = False
                if model1 is not None:
                    model1.close()
                if model2 is not None:
                    model2.close()
                # Menghentikan program
                program_running = False

        time.sleep(1)  # Menyesuaikan durasi tidur sesuai kebutuhan

# Fungsi untuk menjalankan model YOLO pertama
def loop_model1():
    for result1 in results1:
        boxes1 = result1.boxes

        # Inisialisasi kamus untuk menghitung objek dari setiap kelas
        class_objects = {name: 0 for name in x}

        # Memproses dan menghitung objek untuk setiap objek yang terdeteksi
        for box in boxes1:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
            conf0 = math.ceil((box.conf[0] * 100)) / 100
            cls0 = int(box.cls[0])
            class_name = x[cls0]
            class_objects[class_name] += 1  # Menambahkan hitungan kelas

        # Memfilter kelas dengan jumlah objek 0
        detected_classes = [f"{conf0}{count} {class_name}" for class_name, count in class_objects.items() if count > 0]

        #detected_classes = [f"{conf0}{count} {class_name}" for class_name, count in class_objects.items() if count > 0]

        total_detected_objects = sum(class_objects.values())

        # Membangun string info kelas
        class_info = " ; ".join(detected_classes)
        
        # Menampilkan kelas dan kepercayaan
        cv2.putText(frame, f'Kelas: {x[cls0]}, Kepercayaan: {conf0}', (x1, y1), font, 1, (0, 255, 0))

        # Mengirim hitungan untuk kelas yang terdeteksi ke display serial
        serialPort.write_raw(f'n0.val={total_detected_objects}'.encode('utf-8'))
        serialPort.write_raw(b'\xff\xff\xff')

        serialPort.write_raw(f't1.txt="{class_info}"'.encode('utf-8'))
        serialPort.write_raw(b'\xff\xff\xff')

# Fungsi untuk menjalankan model YOLO kedua
def loop_model2():
    for result2 in results2:
        boxes2 = result2.boxes

        # Inisialisasi kamus untuk menghitung objek dari setiap kelas
        class_objects = {name: 0 for name in x}

        # Memproses dan menghitung objek untuk setiap objek yang terdeteksi
        for box in boxes2:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cv2.rectangle(frame1, (x1, y1), (x2, y2), (0, 0, 255), 3)
            conf1 = math.ceil((box.conf[0] * 100)) / 100
            cls1 = int(box.cls[0])
            class_name = Y[cls1]
            class_objects[class_name] += 1  # Menambahkan hitungan kelas

            # Memfilter kelas dengan jumlah objek 0
            detected_classes = [f"{conf1}{count} {class_name}" for class_name, count in class_objects.items() if count > 0]

            # Membangun string info kelas
            class_info = " ; ".join(detected_classes)
            
            # Menampilkan kelas dan kepercayaan
            cv2.putText(frame1, f'Kelas: {Y[cls1]}, Kepercayaan: {conf1}', (x1, y1), font, 1, (0, 255, 0))

            # Mengirim hitungan untuk kelas yang terdeteksi ke display serial
            serialPort.write_raw(f't2.txt="{class_info}"'.encode('utf-8'))
            serialPort.write_raw(b'\xff\xff\xff')

try:
    # Memulai thread untuk membaca dan memproses data serial
    serial_thread = threading.Thread(target=read_serial)
    serial_thread.start()

    while program_running:  # Loop tak terbatas selama program berjalan

        # Membaca data dari port serial
        read = serialPort.read_bytes(serialPort.bytes_in_buffer)
        print(read)

        # Mengecek apakah tombol "start" ditekan
        if read == b'e\x00\x05\x01\xff\xff\xff':
            if not loop_jalan:  # Jika loop belum berjalan
                loop_jalan = True
                # Menginisialisasi model YOLO
                model1 = YOLO("yolov8s.pt")
                model2 = YOLO("yolov8n.pt")
                serialPort.write_raw(f't0.txt="PROGRAM BERJALAN..."'.encode('utf-8'))
                serialPort.write_raw(b'\xff\xff\xff')

                # Melakukan tindakan saat loop berjalan
        if loop_jalan and model1 is not None and model2 is not None:  # Mengecek jika kedua model sudah diinisialisasi 
            ret, frame = cap.read()
            frame1 = frame.copy()
            if not ret:
                break
            frame = imutils.resize(frame, width=1000, height=750)
            results1 = model1(frame, stream=True)
            results2 = model2(frame1, stream=True)
            start_time = time.time()
            loop_model1()
            loop_model2()
            end_time = time.time()
            inference_speed = (end_time - start_time) * 1000
            rounded = round(inference_speed, 2)
            serialPort.write_raw(f't3.txt="{rounded}"'.encode('utf-8'))
            serialPort.write_raw(b'\xff\xff\xff')
    
            cv2.imshow("jenis", frame)
            cv2.imshow("warna", frame1)

            if cv2.waitKey(1) & 0xFF == 27:
                break

except KeyboardInterrupt:
    print("Ctrl+C terdeteksi. Keluar...")

finally:
    serialPort.write_raw(f't0.txt="PROGRAM BERHENTI"'.encode('utf-8'))
    serialPort.write_raw(b'\xff\xff\xff')
    serial_thread.join()  # Menunggu thread serial selesai
    serialPort.close()

# Merestart program jika dihentikan dengan tombol "stop"
if not program_running:
    subprocess.Popen(["python", "last.py"])
