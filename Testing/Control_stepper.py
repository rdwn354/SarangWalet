import Jetson.GPIO as GPIO
import time

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

# Pin Setup
GPIO.setmode(GPIO.BOARD)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)

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
        
if __name__ == "__main__":
    try:
        while True:
            run_stepper(0.001, 200)
            time.sleep(2)

    except KeyboardInterrupt:
        pass

    finally:
        GPIO.cleanup()
