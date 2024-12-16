from plancha import Plancha
import time

COOLING_MIN_T = 35 # Cooling stops under 35°C
CRITICAL_T = 380 # Heating MUST STOP & booard resets

PROFILE_SN0 = [(150,90),(180,90),(245,45)] # (target Temp, time (in sec) to reach the temperature)
PROFILE_SUBSTEP_SEC = 5 # We make a temperature update every x second

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

	def profile_heating( self, profile ):
		""" Follow a profile heating """
		current_temp = self.p.temperature
		phase_start_sec = time.time()
		phase_start_ms  = time.ticks_ms()
		for target_temp, target_seconds in profile:
			print( 'Profile Stage to %3i C in %i seconds' % (target_temp, target_seconds) )
			temp_delta_per_second = (target_temp-current_temp)/target_seconds
			# calculate temps to reach @ next_target_ms
			sub_target_temp = current_temp + temp_delta_per_second*PROFILE_SUBSTEP_SEC
			next_target_ms = time.ticks_add( phase_start_ms, PROFILE_SUBSTEP_SEC*1000 )
			# activate PID
			print( 'time %4i, PID.set=%3i' % (time.time()-phase_start_sec, int(sub_target_temp)) )
			#self.p.temperature = int(sub_target_temp)
			while  True:
				if time.ticks_diff( next_target_ms, time.ticks_ms() ) < 0:
					# It is time to calculate the next iteration value
					sub_target_temp  += temp_delta_per_second*PROFILE_SUBSTEP_SEC
					next_target_ms = time.ticks_add( next_target_ms, PROFILE_SUBSTEP_SEC*1000 )
					# apply to PID
					print( 'time %4i, PID.set=%3i' % (time.time()-phase_start_sec, int(sub_target_temp)) )
					#self.p.temperature = int(sub_target_temp)
				if (time.time()-phase_start_sec) > target_seconds:
					current_temp = self.p.temperature
					phase_start_sec = time.time()
					phase_start_ms  = time.ticks_ms()
					break # Lets process the next phase !
				self.smart_sleep_ms( 100 )
			




	def run( self ):
		# === Main Loop ===
		while self.p.run_app:
			self.p.enc.color = (0,255,0)
			menu = self.p.menu_select( [ ('PREHEAT','[Pre-Heat]',(0,0)), ('COOL','[Cool]',(10,0)), ('SOLDER','[Solder]',(0,1))] )
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
				self.p.lcd.clear()
				self.p.lcd.print( "Cooling...", (0,0) )
				self.p.enc.color = (0,0,255)
				self.p.cooling.on()
				while True:
					_t = self.p.temperature
					self.p.lcd.print( "temp: %3i C" % _t, (0,1) )
					if self.p.enc.button or (_t<COOLING_MIN_T ):
						while self.p.enc.button:
							pass
						self.p.cooling.off()
						break;
					self.smart_sleep_ms( 500 )


			elif menu=='COOL':
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
					if self.p.enc.button:
						while self.p.enc.button:
							pass
						self.p.cooling.off()
						break;
					self.smart_sleep_ms( 500 )
				

			elif menu=='SOLDER':
				self.profile_heating( PROFILE_SN0 )

if __name__ == '__main__':
	app = App()
	try:
		app.run()
	finally:
		app.p.enc.color = (0,0,0)