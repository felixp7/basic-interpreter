10	rem Loop-and-math benchmark
20	let start = timer
30	let a = 1
40	for i = 1 to 10000
50	let a = a / 2 + a / 3
60	next i
70	let finish = timer
75	print a
80	print finish - start
