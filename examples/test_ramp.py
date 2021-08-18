# Send a Low Frequency PWM to the hot plate and record the temperature curve
# to a serial line (at CSV format).
#
# The aim is to learn the temperature curve at various PWM ratio
#
# See GitHub: __TODO__
#
#
# Compatible with:
#  * Raspberry-Pico : using the only Timer() available.
#
from lfpwm import LowFreqPWM
from max31855 import MAX31855
from machine import Pin, SPI
from os import uname
import time

CUTOFF_TEMP = 150 # Cut PWM when temperature (°c) is reached

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
tmc = MAX31855( spi=spi, cs_pin= cs )

print( 'Ready!' )
print( '-----------------------------------' )
print( 'Start a temperature ramp test with:' )
print( '   test_ramp.start_ramp( 10 )' )
print( 'to test a ramp at 10% pwm.' )
print( 'The test ends at CUTOFF_TEMP = %s °C' % CUTOFF_TEMP )
print( 'Press CTRL-C or test_ramp.stop() to ' )
print( 'premature ends the test.' )
print( '-----------------------------------' )

def stop():
	global pwm
	pwm.duty_ratio( 0 )

def start_ramp( ratio, cuttoff_temp=CUTOFF_TEMP ): # from 0 to 100%
	global pwm
	global tmc
	print(  "elapsed (sec)", ",", "ratio (%%)", ",", "temp (°c)" )
	start = time.time()
	pwm.duty_ratio( ratio )
	try:
		while True:
			elapsed = time.time() - start # In seconds
			temp = tmc.temperature()
			print( elapsed, ",", ratio, ",", temp )
			# CutOff temperature reached?
			if (temp!=None) and (temp >= cuttoff_temp):
				ratio = 0
				pwm.duty_ratio( ratio )
			time.sleep(1)
	except:
		print('Stopping...')
		stop()
		raise
