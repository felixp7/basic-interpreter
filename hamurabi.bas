10	let population = 100
20	let land = 1000
30	let grain = 2800
40	let starved = 10
50	let immigrants = 5
60	let rats = 200
65	let planted = 300
70	let yield = int(rnd * 5) + 1
80	let price = int(rnd * 6) + 17
90	let year = 1
100	let plague = 0
200	do
210	gosub 1000
220	gosub 2000
230	gosub 3000
240	loop until population < 1
250	print "Hamurabi, I have bad news. Everyone is dead."
260	print "The city is lost."
270	print "If only you could try again..."
280	end
1000	print "Hamurabi, I beg to report that in year ", year
1010	if starved = 1 then goto 1040
1020	print starved, " people starved to death, and"
1030	goto 1050
1040	print "1 person starved to death, and"
1050	if immigrants = 1 then goto 1080
1060	print immigrants, " people came to the city."
1070	goto 1090
1080	print "1 person came to the city."
1090	if plague then print "The plague killed half of us."
1100	print "The population is now ", population, "."
1110	print "We harvested ", yield * planted, " bushels"
1120	print "at ", yield, " bushels of grain per acre."
1130	print "Rats destroyed ", rats, " bushels of grain,"
1140	print "leaving us with ", grain, " in the granary."
1150	print "The city owns ", land, " acres of land."
1160	print "Land is worth ", price, " bushels per acre."
1170	return
2000	input "How much land do you wish to buy? ", buying
2010	let buying = int(abs(buying))
2020	if buying = 0 then goto 2100
2030	if buying * price <= grain then goto 2060
2040	print "But, Hamurabi! We don't have enough grain!"
2050	goto 2000
2060	let land = land + buying
2070	let grain = grain - buying * price
2080	print "Very well, we are left with ", grain, " bushels."
2100	input "How much land do you wish to sell? ", selling
2110	let selling = int(abs(selling))
2120	if selling = 0 then goto 2200
2130	if selling <= land then goto 2160
2140	print "But, Hamurabi, we only have ", land, " acres!"
2150	goto 2100
2160	let land = land - selling
2170	let grain = grain + selling * price
2180	print "Very well, we now have ", grain, " bushels."
2200	input "How much grain should we feed our people? ", fed
2210	let fed = int(abs(fed))
2220	if fed <= grain then goto 2250
2230	print "But, Hamurabi! We only have ", grain, " bushels!"
2240	goto 2200
2250	let grain = grain - fed
2300	input "How many acres of land should we seed? ", planted
2310	let planted = int(abs(planted))
2320	if planted <= land then goto 2350
2330	print "But, Hamurabi! We only have ", land, " acres!"
2340	goto 2300
2350	if planted <= grain * 2 then goto 2380
2360	print "But, Hamurabi! We only have ", grain, " bushels!"
2370	goto 2300
2380	if planted <= population * 10 then goto 2410
2390	print "But, Hamurabi! We only have ", population, " people!"
2400	goto 2300
2410	return
3000	let yield = int(rnd * 5) + 1
3010	let grain = grain + yield * planted
3020	let rats = int(rnd * (grain * 0.07))
3030	let grain = grain - rats
3040	let starved = population - int(fed / 20)
3050	if starved < 0 then let starved = 0
3060	let population = population - starved
3070	if population <= 0 then goto 3140
3080	let immigrants1 = int(starved / 2)
3090	let immigrants2 = int((5 - yield) * grain / 600 + 1)
3100	let immigrants = immigrants1 + immigrants2
3105	if immigrants > 50 then let immigrants = 50
3106	if immigrants < 0 then let immigrants = 0
3110	let population = population + immigrants
3120	let plague = not int(rnd * 11)
3130	if plague then let population = int (population / 2)
3140	let price = int(rnd * 6) + 17
3150	let year = year + 1
3160	return
