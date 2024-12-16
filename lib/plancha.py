# Access to all the components
#
from machine import Pin, SPI, I2C, reset
from lcdi2c import LCDI2C
from lfpwm import LowFreqPWM
from pid import PID
from max31855 import MAX31855
from i2cenc import I2CEncoder
import time

class Plancha():
	""" Class for the Plancha-CMS """
	def __init__(self):
		self._run_app = Pin( Pin.board.GP3, Pin.IN, Pin.PULL_UP )
		self.heater   = Pin( Pin.board.GP13, Pin.OUT, value=False )
		self.cooling  = Pin( Pin.board.GP19, Pin.OUT, value=False )
		self.critical_temp = 270 # will stop PID and reset board if reached!

		# --- Buses ---
		# SPI(0)
		self._spi_cs  = Pin( Pin.board.GP5, Pin.OUT, value=True ) # SPI CSn
		self._spi = SPI(0, mosi=Pin.board.GP7, miso=Pin.board.GP4, sck=Pin.board.GP6, baudrate=5000000, polarity=0, phase=0)
		# I2C(0)
		self._i2c = I2C( 0, sda=Pin.board.GP8, scl=Pin.board.GP9 )

		# --- Components ---
		# Thermocouple
		self.tmc = MAX31855( spi=self._spi, cs_pin=self._spi_cs )
		# LCD & encoder
		self.lcd = LCDI2C( self._i2c, cols=16, rows=2 )
		self.enc = I2CEncoder(self._i2c)
		# Low Frequency PWM for SSR relay
		self._pwm = LowFreqPWM( pin=self.heater, period=1.5, ton_ms=9, toff_ms=10 ) # period=1.5s, needs 9ms to get activated, 10ms to get it off
		self._pid = None
		self._pid_start = time.time() # Last change of PID setpoint()


		# --- Initialize ---
		# lcd
		self.lcd.backlight()
		self.lcd.clear()
		self.lcd.print( "Plancha CMS", (2,0) )
		self.lcd.print( "temp: %3i C" % self.tmc.temperature(), (0,1) )
		# encoder
		self.enc.color = (0,255,0) # Rouge


	def setup_pid( self, Kp, Ki, Kd ):
		def measure_temp(): # PID callbacks
			_t = self.tmc.temperature()
			if (self._pid != None) and (self._pid.setpoint>0):
				print( "%i, %i, %i" % (time.time()-self._pid_start, self._pid.setpoint, _t) ) # DeltaTime_since_temps_set, temp_setpoint, current_temps
			if _t >= self.critical_temp:
				self._pid.stop()  # Make it rebooting!
				self.heater.off()
				print( 'Reset board now!' )
				reset()
			return _t
		def output_pwm(value):
			return self._pwm.duty_ratio( int(value) )
		self._pid = PID(Kp=Kp, Ki=Ki, Kd=Kd, dt=1000, setpoint=100, measure_func=measure_temp, output_func=output_pwm, output_min=0, output_max=100)
		self._pid.stop()

	@property
	def run_app(self):
		""" Check the Run App """
		return self._run_app.value()==False

	@property
	def temperature( self ):
		return self.tmc.temperature()

	@temperature.setter
	def temperature( self, value ):
		# Initialize the PID destination
		if self._pid == None:
			raise Exception( "setup_pid() must be called first.")
		self._pid.set( value )# A Zero value will stop the PID
		self._pid_start = time.time()

	def stop( self ):
		""" Stop Any PID running and controling the Heater """
		if self._pid == None:
			raise Exception( "setup_pid() must be called first.")
		self._pid.stop() # Will set PID the setpoint to 0
		self._pid_start = time.time()
		self.heater.off() # Be sure we did stop it!

	def menu_select( self, options, clear=True ):
		""" options are [ (code,label,(x,y)) ]	"""
		if clear:
			self.lcd.clear()
		iPos = 0
		for key, label, xy_pos in options:
			if iPos != 0:
				label = label.replace('[',' ').replace(']',' ')
			self.lcd.print( label, xy_pos )
			iPos += 1

		idx = 0 # Current position in the menu
		curr_enc = self.enc.position
		while True:
			if self.enc.button:
				return options[idx][0] # return the Key
			if self.enc.position == curr_enc:
				continue
			_dir = 1 if self.enc.position > curr_enc else -1 
			# clear current label
			self.lcd.print( options[idx][1].replace('[',' ').replace(']',' '), options[idx][2] )
			idx = idx + _dir 
			# limit the new value
			if idx > len(options)-1:
				idx = 0
			elif idx < 0:
				idx = len(options)-1
			# select new label
			self.lcd.print( options[idx][1], options[idx][2] )
			time.sleep_ms( 100 )
			curr_enc = self.enc.position


	def int_select( self, label, format_str, value, imin=0, imax=250, istep=5 ):
		""" options are [ (code,label,(x,y)) ]	"""
		self.lcd.clear()
		self.lcd.print( label, (0,0) )
		self.lcd.print( format_str % value, (0,1) )

		# Wait release of the button
		while self.enc.button:
			pass

		curr_enc = self.enc.position
		while True:
			if self.enc.button:
				return value # return the Key
			if self.enc.position == curr_enc:
				continue
			_dir = 1 if self.enc.position > curr_enc else -1 
			# Write the new value
			value = value + _dir*istep
			# limit the new value
			if value >= imax:
				value = imax
			if value <= imin:
				value = imin
			# Print the new value
			self.lcd.print( format_str % value, (0,1) )
			time.sleep_ms( 100 )
			curr_enc = self.enc.position

	def confirm_select( self, label ):
		""" Response True/False """
		self.lcd.clear()
		self.lcd.print( label[:15], (0,0) )
		# Wait release of the button
		while self.enc.button:
			pass
		# Request confirmation
		return self.menu_select( [(True,'[Yes]',(0,1)), (False,'[No]',(12,1)) ], clear=False )