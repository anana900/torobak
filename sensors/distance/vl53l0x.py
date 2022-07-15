import board
import busio
import adafruit_vl53l0x
from time import sleep

i2c  = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_vl53l0x.VL53L0X(i2c)
# sensor.measurement_timing_budget = 33000

while True:
    print(f"{sensor.range}")
    sleep(0.1)

