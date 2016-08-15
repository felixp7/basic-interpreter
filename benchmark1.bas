10	rem Loop-and-math benchmark
20	let start = timer
30	let a = 1
40	for i = 1 to 1000
50	let a = a / 2 + a / 3
60	next i
65	print a
70	let finish = timer
80	print finish - start
