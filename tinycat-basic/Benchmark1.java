class Benchmark1 {
	public static void main(String[] args) {
		final double start =
			Double.valueOf(System.currentTimeMillis()) / 1000.0;
		double a = 1;
		for (int i = 0; i < 10000; i++)
			a = a / 2.0 + a / 3.0;
		final double finish =
			Double.valueOf(System.currentTimeMillis()) / 1000.0;
		System.out.println(a);
		System.out.println(finish - start);
	}
}
