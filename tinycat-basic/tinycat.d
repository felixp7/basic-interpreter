import basic;

void main(string[] args) {
	Basic ctx = new Basic();
	
	if (args.length > 1) {
		foreach (i; args[1 .. $])
			ctx.loadFile(i);
		ctx.runProgram;
		if (!ctx.stop)
			return;
	}
	
	ctx.commandLoop("Tinycat BASIC v1.1.2 READY\nType BYE to quit.");
}
