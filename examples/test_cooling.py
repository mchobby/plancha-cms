# Just read the temperature from MAX31855 and send it to the REPL
#
#
# See GitHub: __TODO__
#
# Compatible with:
#  * Raspberry-Pico : using the only Timer() available.
#
from max31855 import MAX31855
from machine import Pin, SPI
from os import uname
import time

# User LED on Pico
heater = None
if uname().sysname == 'rp2': # RaspberryPi Pico
	print( 'Attaching SPI to SPI(0) : GP5=CSn, GP4=Miso, GP6=Sck, GP7=Mosi')
	cs = Pin(5, Pin.OUT, value=True ) # SPI CSn
	spi = SPI(0, mosi=Pin.board.GP7, miso=Pin.board.GP4, sck=Pin.board.GP6, baudrate=5000000, polarity=0, phase=0)
else:
	raise Exception( 'Oups! plateform %s not supported' % uname().sysname )

# Setup MAX31855 : thermocouple reader
tmc = MAX31855( spi=spi, cs_pin= cs )
cooler = Pin( Pin.board.GP19, Pin.OUT, value=False )
cooler.on()

start = time.time()
while True:
	elapsed = time.time() - start # In seconds
	temp = tmc.temperature()
	print( elapsed, ",", temp )
	if temp<50:
		cooler.off()
	time.sleep(1)
