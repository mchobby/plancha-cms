from machine import Pin


p = Pin( Pin.board.GP3, Pin.IN, Pin.PULL_UP )
if p.value()==False:
	print( "Run_app = RUN" )
else:
	print( "Run_app = STOP" )
