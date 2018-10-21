import core.time;
import std.stdio;

void main() {
	double start = cast(double) MonoTime.currTime.ticks
		/ cast(double) MonoTime.ticksPerSecond;
	double a = 1;
	for (double i = 1; i <= 10000; i++)
		a = a / 2 + a / 3;
	double finish = cast(double) MonoTime.currTime.ticks
		/ cast(double) MonoTime.ticksPerSecond;
	writeln(a);
	writeln(finish - start);
}
