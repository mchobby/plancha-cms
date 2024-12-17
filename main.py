from plancha import Plancha
from machine import reset
from micropython import alloc_emergency_exception_buf
import time

alloc_emergency_exception_buf( 100 )

COOLING_MIN_T = 35 # Cooling stops under 35°C
CRITICAL_T = 380 # Heating MUST STOP & booard resets

PROFILE_SUBSTEP_SEC = 5 # We make a temperature update every x second
PROFILE_SNCU = [(150,90),(180,90),(245,45),(245,30)] # (target Temp, time (in sec) to reach the temperature)


class App:
	def __init__( self ):
		self.p = Plancha()
		self.p.setup_pid( Kp=1.95, Ki=0.0125, Kd=4.5 )
		self.p.critical_temp = CRITICAL_T # PID will raise exception at 270°

	def smart_sleep_ms( self, ms ):
		""" Wait for given time or the encoder button pressed """
		_start = time.ticks_ms()
		while time.ticks_diff( time.ticks_ms(), _start )<ms:
			if self.p.enc.button:
				break
			time.sleep_ms( 50 )

	def cooling( self, cooling_stop_t=-1 ):
		# Cooling stop when:
		#   1. temperature falls under cooling_stop_t
        #   2. the button is pressed
		#
		# Cooling (NO automatic stop)
		self.p.lcd.clear()
		self.p.lcd.print( "Cooling...", (0,0) )
		self.p.enc.color = (0,0,255)
		self.p.cooling.on()
		# wait release
		while self.p.enc.button:
			pass
		while True:
			_t = self.p.temperature
			self.p.lcd.print( "temp: %3i C" % _t, (0,1) )
			if self.p.enc.button or (_t<cooling_stop_t ):
				while self.p.enc.button:
					pass
				self.p.cooling.off()
				break;
			self.smart_sleep_ms( 500 )



	def profile_heating( self, profile, progress_cb=None ):
		""" Follow a profile heating. See PROFILE_SN0 for info. 
		    progess_cb is called every PROFILE_SUBSTEP_SEC. Must be a function(str) to capture profile follower debug message. """
		current_temp = self.p.temperature
		phase_start_sec = time.time()
		phase_start_ms  = time.ticks_ms()
		previous_temp = None
		for target_temp, target_seconds in profile:
			if progress_cb!=None:
				#progress_cb( 'Profile Stage to %3i C in %i seconds' % (target_temp, target_seconds) )
				progress_cb( 'Phs %3i C..%3is' % (target_temp, target_seconds) )
			temp_delta_per_second = (target_temp-current_temp)/target_seconds
			# calculate temps to reach @ next_target_ms
			sub_target_temp = current_temp + temp_delta_per_second*PROFILE_SUBSTEP_SEC
			next_target_ms = time.ticks_add( phase_start_ms, PROFILE_SUBSTEP_SEC*1000 )
			# activate PID
			if progress_cb!=None:
				progress_cb( '%4is, set %3i' % (time.time()-phase_start_sec, int(sub_target_temp)) )
			# IF the phase maintains the temperature THEN set the Final temperature
			if target_temp==previous_temp:
				self.p.temperature = target_temp
			else:  # we apply a sub-step temperature
				self.p.temperature = int(sub_target_temp)


			while  True:
				if not(self.p.run_app):
					self.p.stop()
					return 

				if time.ticks_diff( next_target_ms, time.ticks_ms() ) < 0:
					# It is time to calculate the next iteration value
					sub_target_temp  += temp_delta_per_second*PROFILE_SUBSTEP_SEC
					next_target_ms = time.ticks_add( next_target_ms, PROFILE_SUBSTEP_SEC*1000 )
					# apply to PID
					if progress_cb!=None:
						progress_cb( '%3isec - %3i C' % (time.time()-phase_start_sec, int(sub_target_temp)) )
					# IF the phase maintains the temperature THEN skip sub-temps assignation
					if target_temp!=previous_temp:
						self.p.temperature = int(sub_target_temp)
				if (time.time()-phase_start_sec) >= target_seconds:
					if progress_cb!=None:
						progress_cb( '%4is end phase' % ( time.time()-phase_start_sec )  )
					current_temp = target_temp
					phase_start_sec = time.time()
					phase_start_ms  = time.ticks_ms()
					break # Lets process the next phase !
				self.smart_sleep_ms( 100 )
			previous_temp = target_temp # Remeber the previous phase temperature

		# Do not stop regulation but reduce it at 1°C 
		#    this will keeps logging the temperature while cooling
		self.p.temperature = 1

		# self.p.stop() # Stop the PID regulation!	
		

	def menu_loop( self ):
		# === Main Loop ===
		while self.p.run_app:
			self.p.enc.color = (0,255,0)
			menu = self.p.menu_select( [ ('PREHEAT','[Pre-Heat]',(0,0)), ('COOL','[Cool]',(10,0)), ('REFLOW','[Reflow]',(0,1))] )
			while self.p.enc.button:
					pass
			if not(self.p.run_app):
				break

			if menu=='PREHEAT':
				target_temp = self.p.int_select( "Pre-Heat temp?", "       %03i C", 100, imin=50, imax=250, istep=5 )
				val = self.p.confirm_select( "Pre-heat %3i C" % target_temp )
				# Wait button release
				while self.p.enc.button:
					pass

				if not( val ):
					continue # go to menu

				# Pre Heating
				self.p.lcd.clear()
				self.p.lcd.print( "Pre-heating...", (0,0) )
				self.p.enc.color = (255,0,0)
				self.p.temperature = target_temp # Will start the PID
				while True:
					self.p.lcd.print( "temp: %3i C" % self.p.temperature, (0,1) )
					if self.p.enc.button:
						self.p.stop()
						while self.p.enc.button:
							pass
						break
					self.smart_sleep_ms( 500 )
				# Cooling (with automatic stop)
				self.cooling( cooling_stop_t=COOLING_MIN_T )


			elif menu=='COOL':
				# Cooling (NO automatic stop)
				self.cooling()


			elif menu=='REFLOW':
				# Dictionnary of Reflow profile availables
				PROFILES = {'SnCu': PROFILE_SNCU }

				def update_lcd( msg ):
					# Called every PROFILE_SUBSTEP_SEC 
					self.p.lcd.print( msg, (0,1) )
				
				profile_code = self.p.menu_select( [ ('SnCu','[SnCu]',(0,0)) ] )
				# Wait button release
				while self.p.enc.button:
					pass

				val = self.p.confirm_select( "%s reflow ?" % profile_code )
				# Wait button release
				while self.p.enc.button:
					pass

				if not( val ):
					continue # go to menu

				self.p.lcd.clear()
				self.p.enc.color = (255,0,0)
				self.p.lcd.print( "%s reflow..." % profile_code, (0,0) )
				try:
					self.profile_heating( PROFILES[profile_code], progress_cb=update_lcd )
					# Cooling (with automatic stop)
					self.cooling( cooling_stop_t=100 )
				finally:
					self.p.stop() # Make sure PID is stopped! to avoid it to send a pulse. This will also stops the PID logging
				self.cooling( cooling_stop_t=COOLING_MIN_T )


	def run( self ):
		# Make sure we stop PID & restart microcontroler
		# when unexpected thing happen
		try:
			self.menu_loop()
		except:
			self.p.enc.color = (0,0,0)
			self.p.stop()
			reset()


if __name__ == '__main__':
	app = App()
	try:
		app.run()
	finally:
		app.p.lcd.print('Exit!', (0,1))
		app.p.enc.color = (0,0,0)