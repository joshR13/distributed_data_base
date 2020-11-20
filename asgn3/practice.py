from VectorClocks import *

array = []
vectorClock = VectorClocks(array)

key = int('az12yu')

print(vectorClock.constHash(key))