# Loop-and-math benchmark
import time
start = time.process_time()
a = 1
for i in range(10000):
	a = a / 2 + a / 3
finish = time.process_time()
print(a)
print(finish - start)
