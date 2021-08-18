# Control the plate temperature with a PID
#
# The aim is to learn the PID parameters
#
# See GitHub: __TODO__
#
# Compatible with:
#  * Raspberry-Pico : using the only Timer() available.
#
from lfpwm import LowFreqPWM
from max31855 import MAX31855
from pid import PID
from machine import Pin, SPI
from os import uname
import time

CUTOFF_TEMP = 270 # Cut PWM when temperature (°c) is reached

# User LED on Pico
heater = None
if uname().sysname == 'rp2': # RaspberryPi Pico
	print( 'Attaching Heater to Pin GP13' )
	heater = Pin(13)
	print( 'Attaching SPI to SPI(0) : GP5=CSn, GP4=Miso, GP6=Sck, GP7=Mosi')
	cs = Pin(5, Pin.OUT, value=True ) # SPI CSn
	spi = SPI(0, baudrate=5000000, polarity=0, phase=0)
else:
	raise Exception( 'Oups! plateform %s not supported' % uname().sysname )

# Setup pwm
pwm = LowFreqPWM( pin=heater, period=1.5, ton_ms=9, toff_ms=10 ) # period=1.5s, needs 9ms to get activated, 10ms to get it off
pwm.duty_ratio( 0 )
tmc = MAX31855( spi=spi, cs_pin= cs )
_target_temp  = 150 # Temperature to reach
_current_temp = tmc.temperature() # Global copy of temperature
_current_pwm  = 0 # Global copy of pwm ratio

def measure_temp():
	global tmc
	global _current_temp
	_current_temp = tmc.temperature()
	return _current_temp

def output_pwm(value):
	global pwm
	global _current_pwm
	_current_pwm = value
	return pwm.duty_ratio( int(value) )

# attaching PID
# dt=1500 ms, set_point=150°C, output from 0..100 (for PWM)
pid = PID(Kp=1.95, Ki=0.0125, Kd=4.5, dt=1000, setpoint=150, measure_func=measure_temp, output_func=output_pwm, output_min=0, output_max=100)

print( 'Target Temp: %s C' % _target_temp )
print( 'PID Started!' )
print( '-----------------------------------' )
print( 'Press CTRL-C to stop the PID ' )
print( '-----------------------------------' )



print(  "elapsed (sec)", ",", "ratio (%%)", ",", "temp (°c)" )
start = time.time()
try:
	while True:
		elapsed = time.time() - start # In seconds
		print( elapsed, ",", _current_pwm, ",", _current_temp )
		# CutOff temperature reached?
		if (_current_temp!=None) and (_current_temp >= CUTOFF_TEMP):
			print('CUTOFF reached! PID stopped!')
			pid.stop()
		time.sleep(1)
except:
	print('Stopping PID...')
	pid.stop()
	print('Stopped!')
