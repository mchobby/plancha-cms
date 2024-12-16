from machine import Pin, I2C
from lcdi2c import LCDI2C

i2c = I2C( 0, sda=Pin.board.GP8, scl=Pin.board.GP9, freq=100000 )
lcd = LCDI2C( i2c, cols=16, rows=2 )
lcd.backlight()
lcd.clear()
lcd.print( "hello" )
lcd.print( '^', pos=(8,0) )
lcd.print( '>', pos=(9,1) )