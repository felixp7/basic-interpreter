import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;
import java.util.SortedMap;
import java.util.TreeMap;
import java.util.LinkedList;

import java.util.Random;

import java.io.IOException;
import java.io.FileNotFoundException;
import java.io.InputStreamReader;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.PrintStream;

/** Extensible line-number Basic interpreter in under 1000 lines of Java. */
public class Basic {
	// Always try to match the longer operators first.
	public static final String RelOp[] = {"=", "<>", "<=", ">=", "<", ">"};
	
	public BufferedReader input =
		new BufferedReader(new InputStreamReader(System.in));
	public PrintStream output = System.out;
	public PrintStream error = System.err;
	
	public String line = "";
	public int cursor = 0;
	public String token = null;
	
	public Map<String, Double> variables =
		new HashMap<String, Double>();
	public final SortedMap<Integer, String> program =
		new TreeMap<Integer, String>();
	
	protected final List<Integer> addr = new ArrayList<Integer>();
	protected int crt_line = 0;
	protected boolean stop = false;
	
	protected final LinkedList<Double> dstack = new LinkedList<Double>();
	protected final LinkedList<Integer> rstack = new LinkedList<Integer>();

	protected final Map<String, String[]> function_args =
		new HashMap<String, String[]>();
	protected final Map<String, String> function_code =
		new HashMap<String, String>();
		
	protected Random rng = new Random();

	public Basic() {
		String args[] = new String[0];
		function_args.put("rnd", args);
		function_args.put("timer", args);
		function_args.put("pi", args);
		args = new String[]{"n"};
		function_args.put("int", args);
		function_args.put("abs", args);
		function_args.put("sqr", args);
		function_args.put("sin", args);
		function_args.put("cos", args);
		function_args.put("rad", args);
		function_args.put("deg", args);
		args = new String[]{"a", "b"};
		function_args.put("min", args);
		function_args.put("max", args);
		function_args.put("mod", args);
		function_args.put("hypot2", args);
		args = new String[]{"a", "b", "c"};
		function_args.put("hypot3", args);
		function_args.put("iif", args);
	}

	public void skip_whitespace() {
		while (cursor < line.length()
				&& Character.isWhitespace(line.charAt(cursor)))
			cursor++;
	}

	public boolean match_keyword() {
		// skip_whitespace()
		
		if (cursor >= line.length()
				|| !Character.isAlphabetic(line.charAt(cursor)))
			return false;
			
		final int mark = cursor;
		while (cursor < line.length()
				&& Character.isAlphabetic(line.charAt(cursor)))
			cursor++;
		token = line.substring(mark, cursor).toLowerCase();

		return true;
	}
	
	public void skip_digits() {
		while (cursor < line.length()
				&& Character.isDigit(line.charAt(cursor)))
			cursor++;
	}

	public boolean match_number() {
		skip_whitespace();

		final int mark = cursor;
		skip_digits();
		if (mark == cursor)
			return false;

		if (cursor < line.length() && line.charAt(cursor) == '.') {
			cursor++;
			skip_digits();
		}
		token = line.substring(mark, cursor);

		return true;
	}

	public boolean match_varname() {
		skip_whitespace();

		if (cursor >= line.length()
				|| !Character.isAlphabetic(line.charAt(cursor)))
			return false;
			
		final int mark = cursor;
		while (cursor < line.length()
				&& Character.isLetterOrDigit(
					line.charAt(cursor)))
			cursor++;
		token = line.substring(mark, cursor).toLowerCase();

		return true;
	}

	public boolean match_string() {
		skip_whitespace();

		if (cursor >= line.length() || line.charAt(cursor) != '"')
			return false;
			
		final int mark = cursor;
		cursor++; // Skip the opening double quote.
		if (cursor >= line.length())
			throw new RuntimeException(
				"Unclosed string");
		while (line.charAt(cursor) != '"') {
			cursor++;
			if (cursor >= line.length())
				throw new RuntimeException(
					"Unclosed string");
		}
		cursor++; // Skip the closing double quote.
		
		// Save string value without the double quotes.
		token = line.substring(mark + 1, cursor - 1);
		return true;
	}
	
	public boolean match(final String text) {
		skip_whitespace();
		if (line.startsWith(text, cursor)) {
			cursor += text.length();
			return true;
		} else {
			return false;
		}
	}

	public boolean match_nocase(final String kw) {
		final int mark = cursor;
		skip_whitespace();
		if (!match_keyword()) {
			cursor = mark;
			return false;
		} else if (!token.toLowerCase().equals(kw.toLowerCase())) {
			cursor = mark;
			return false;
		} else {
			return true;
		}
	}

	public boolean match_eol() {
		skip_whitespace();
		return cursor >= line.length();
	}
	
	public boolean match_relation() {
		skip_whitespace();
		for (int i = 0; i < Basic.RelOp.length; i++) {
			final String op = Basic.RelOp[i];
			if (line.startsWith(op, cursor)) {
				token = op;
				cursor += op.length();
				return true;
			}
		}
		return false;
	}

	public boolean match_add_sub() {
		if (match("+")) {
			token = "+";
			return true;
		} else if (match("-")) {
			token = "-";
			return true;
		} else {
			return false;
		}
	}

	public boolean match_mul_div() {
		if (match("*")) {
			token = "*";
			return true;
		} else if (match("/")) {
			token = "/";
			return true;
		} else if (match("\\")) {
			token = "\\";
			return true;
		} else {
			return false;
		}
	}

	public void parse_statement() {
		if (match_keyword())
			dispatch_statement();
		else
			throw new RuntimeException("Statement expected");
	}
	
	/** Extension point: override in a subclass to add more statements. */
	public void dispatch_statement() {		
		if (token.equals("let"))
			parse_let();
		else if (token.equals("if"))
			parse_if();
		else if (token.equals("goto"))
			parse_goto();
		else if (token.equals("print"))
			parse_print();
		else if (token.equals("input"))
			parse_input();
		else if (token.equals("for"))
			parse_for();
		else if (token.equals("next"))
			parse_next();
		else if (token.equals("gosub"))
			parse_gosub();
		else if (token.equals("return"))
			parse_return();
		else if (token.equals("do"))
			rstack.push(crt_line);
		else if (token.equals("loop"))
			parse_loop();
		else if (token.equals("rem"))
			cursor = line.length();
		else if (token.equals("def"))
			parse_def();
		else if (token.equals("randomize"))
			if (match_eol())
				rng = new Random();
			else
				rng.setSeed((long) parse_arithmetic());
		else if (token.equals("stop"))
			stop = true;
		else if (token.equals("end"))
			crt_line = addr.size();
		else
			throw new RuntimeException(
				"Unknown statement: " + token);
	}
	
	public void parse_let() {
		if (!match_varname())
			throw new RuntimeException("Variable expected");
			
		final String var_name = token;
		
		if (!match("="))
			throw new RuntimeException("'=' expected");

		variables.put(var_name, parse_expression());
	}
	
	public void parse_if() {
		final double condition = parse_expression();
		if (match_nocase("then")) {
			if (condition != 0) {
				skip_whitespace();
				parse_statement();
			} else {
				cursor = line.length();
			}
		} else {
			throw new RuntimeException("IF without THEN");
		}
	}
	
	public void parse_goto() {
		final int ln = (int) parse_arithmetic();
		if (addr.contains(ln))
			crt_line = addr.indexOf(ln);
		else
			throw new RuntimeException(
				"Line not found: " + ln);
	}

	public void parse_print() {
		if (match_eol()) {
			output.println();
			return;
		}
		String value = parse_printable();
		while (match(","))
			value += parse_printable();
		if (match(";"))
			output.print(value);
		else
			output.println(value);
	}

	public void parse_input() {
		final String prompt;
		if (match_string()) {
			prompt = token;
			if (!match(","))
				throw new RuntimeException("Comma expected");
		} else {
			prompt = "";
		}
		
		final String[] input_vars = parse_varlist();
		output.print(prompt);
		String[] data;
		try {
			String input_line = input.readLine();
			data = input_line.split(",");
		} catch (IOException e) {
			data = new String[0];
		}

		for (int i = 0; i < input_vars.length; i++) {
			final String v = input_vars[i];
			if (i >= data.length) {
				variables.put(v, 0.0);
				continue;
			}
			
			data[i] = data[i].trim();

			if (data[i].length() == 0) {
				variables.put(v, 0.0);
				continue;
			}

			try {
				variables.put(v, Double.parseDouble(data[i]));
			} catch (NumberFormatException e) {
				error.print("Can't parse number: " + data[i]);
				error.println(" Maybe you forgot a comma?");
				variables.put(v, 0.0);
			}
		}
	}

	public String[] parse_varlist() {
		if (!match_varname())
			throw new RuntimeException("Variable expected");
		final List<String> varlist = new ArrayList<String>();
		varlist.add(token);
		while (match(",")) {
			if (!match_varname())
				throw new RuntimeException(
					"Variable expected");
			varlist.add(token);
		}
		return varlist.toArray(new String[0]);
	}

	public void parse_for() {
		if (!match_varname())
			throw new RuntimeException("Variable expected");
		
		final String var_name = token;
		
		if (!match("="))
			throw new RuntimeException("'=' expected");

		variables.put(var_name, parse_arithmetic());
		
		if (!match_nocase("to"))
			throw new RuntimeException("'to' expected");

		final double limit = parse_arithmetic();
		
		final double step;
		if (match_nocase("step")) {
			step = parse_arithmetic();
			if (step == 0)
				throw new RuntimeException("Infinite loop");
		} else {
			step = 1;
		}

		rstack.push(crt_line);
		dstack.push(limit);
		dstack.push(step);
	}

	public void parse_next() {
		if (dstack.size() < 2)
			throw new RuntimeException("NEXT without FOR");
		
		if (!match_varname())
			throw new RuntimeException("Variable expected");

		final String var_name = token;

		if (!variables.containsKey(var_name))
			throw new RuntimeException(
				"Variable not found: " + var_name);
		
		variables.put(var_name,
			variables.get(var_name) + dstack.get(0));
		final boolean done;
		if (dstack.get(0) > 0)
			done = variables.get(var_name) > dstack.get(1);
		else if (dstack.get(0) < 0)
			done = variables.get(var_name) < dstack.get(1);
		else
			throw new RuntimeException("Infinite loop");
		
		if (done) {
			rstack.pop();
			dstack.pop();
			dstack.pop();
		} else {
			crt_line = rstack.get(0);
		}
	}

	public void parse_gosub() {
		final int ln = (int) parse_arithmetic();
		if (addr.contains(ln)) {
			rstack.push(crt_line);
			crt_line = addr.indexOf(ln);
		} else {
			throw new RuntimeException(
				"Line not found: " + ln);
		}
	}

	public void parse_return() {
		if (rstack.size() > 0)
			crt_line = rstack.pop();
		else
			throw new RuntimeException("RETURN without GOSUB");
	}

	public void parse_loop() {
		if (match_nocase("while")) {
			if (parse_expression() != 0)
				crt_line = rstack.getLast();
			else
				rstack.pop();
		} else if (match_nocase("until")) {
			if (parse_expression() == 0)
				crt_line = rstack.getLast();
			else
				rstack.pop();
		} else {
			throw new RuntimeException("Condition expected");
		}
	}
	
	public void parse_def() {
		if (!match_nocase("fn"))
			throw new RuntimeException("Missing 'fn'");
		if (!match_varname())
			throw new RuntimeException("Function name expected");

		final String name = token;

		if (function_args.containsKey(name))
			throw new RuntimeException(
				"Duplicate function: " + name);
		if (!match("("))
			throw new RuntimeException("Missing '('");
		
		final String[] args;
		if (match(")")) {
			args = new String[0];
		} else {
			args = parse_varlist();
			if (!match(")"))
				throw new RuntimeException("Missing ')'");
		}
		
		if (!match("="))
			throw new RuntimeException("Missing '='");
		
		function_args.put(name, args);
		function_code.put(name, line.substring(cursor));
		cursor = line.length();
	}
	
	public String parse_printable() {
		if (match_string())
			return token;
		else
			return String.format("%1g", parse_expression());
	}
	
	/** Extension point: override in a subclass to add new syntax. */
	public double parse_expression() {
		return parse_disjunction();
	}
	
	public double parse_disjunction() {
		double lside = parse_conjunction();
		while (match_nocase("or")) {
			final double rside =
				(parse_conjunction() != 0) ? -1 : 0;
			lside = (lside != 0 || rside != 0) ? -1 : 0;
		}
		return lside;
	}

	public double parse_conjunction() {
		double lside = parse_negation();
		while (match_nocase("and")) {
			final double rside =
				(parse_negation() != 0) ? -1 : 0;
			lside = (lside != 0 && rside != 0) ? -1 : 0;
		}
		return lside;
	}

	public double parse_negation() {
		if (match_nocase("not"))
			return (parse_comparison() == 0) ? -1 : 0;
		else
			// Leave purely arithmetic results intact
			return parse_comparison();
	}
	
	public double parse_comparison() {
		final double lside = parse_arithmetic();
		if (!match_relation()) {
			return lside;
		} else {
			final String op = token;
			final double rside = parse_arithmetic();
			if (op.equals("<="))
				return (lside <= rside) ? -1 : 0;
			else if (op.equals("<"))
				return (lside < rside) ? -1 : 0;
			else if (op.equals("="))
				return (lside == rside) ? -1 : 0;
			else if (op.equals("<>"))
				return (lside != rside) ? -1 : 0;
			else if (op.equals(">"))
				return (lside > rside) ? -1 : 0;
			else if (op.equals(">="))
				return (lside >= rside) ? -1 : 0;
			else
				throw new RuntimeException(
					"Unknown operator: " + op);
		}
	}

	public double parse_arithmetic() {
		double t1 = parse_term();
		while (match_add_sub()) {
			final String op = token;
			final double t2 = parse_term();
			if (op.equals("+"))
				t1 += t2;
			else if (op.equals("-"))
				t1 -= t2;
			else
				throw new RuntimeException(
					"Unknown operator: " + op);
		}
		return t1;
	}
	
	public double parse_term() {
		double t1 = parse_power();
		while (match_mul_div()) {
			final String op = token;
			final double t2 = parse_power();
			if (op.equals("*"))
				t1 *= t2;
			else if (op.equals("/"))
				t1 /= t2;
			else if (op.equals("\\"))
				t1 = Math.floor(t1 / t2);
			else
				throw new RuntimeException(
					"Unknown operator: " + op);
		}
		return t1;
	}
	
	public double parse_power() {
		final double t1 = parse_factor();
		if (match("^"))
			return Math.pow(t1, parse_power());
		else
			return t1;
	}
	
	public double parse_factor() {
		final double signum;
		if (match("-"))
			signum = -1;
		else if (match("+"))
			signum = 1;
		else
			signum = 1;
		
		if (match_number()) {
			return Double.valueOf(token) * signum;
		} else if (match_varname()) {
			final String name = token;
			if (function_args.containsKey(name)) {
				final Double args[] = parse_args();
				return call_fn(name, args) * signum;
			} else if (variables.containsKey(name)) {
				return variables.get(name) * signum;
			} else {
				throw new RuntimeException(
					"Var not found: " + name);
			}
		} else if (match("(")) {
			final double value = parse_expression();
			if (match(")"))
				return value * signum;
			else
				throw new RuntimeException("Missing ')'");
		} else {
			throw new RuntimeException("Expression expected");
		}
	}
	
	public Double[] parse_args() {
		if (match("(")) {
			if (match(")"))
				return new Double[0];
			final List<Double> args = new ArrayList<Double>();
			args.add(parse_expression());
			while (match(","))
				args.add(parse_expression());
			if (match(")"))
				return args.toArray(new Double[0]);
			else
				throw new RuntimeException("Missing ')'");
		} else {
			return new Double[0];
		}
	}

	public double call_fn(final String name, final Double[] args) {
		if (args.length != function_args.get(name).length)
			throw new RuntimeException("Bad argument count");
		else if (function_code.containsKey(name))
			return call_user_fn(name, args);
		else
			return call_builtin(name, args);
	}

	/** Extension point: override in a subclass to add more functions. */
	public double call_builtin(final String name, final Double[] args) {
		if (name.equals("timer"))
			return Double.valueOf(
				System.currentTimeMillis()) / 1000.0;
		else if (name.equals("rnd"))
			return rng.nextDouble();
		else if (name.equals("pi"))
			return Math.PI;
		else if (name.equals("int"))
			return args[0] >= 0 ?
				Math.floor(args[0]) : Math.ceil(args[0]);
		else if (name.equals("abs"))
			return Math.abs(args[0]);
		else if (name.equals("sqr"))
			return Math.sqrt(args[0]);
		else if (name.equals("sin"))
			return Math.sin(args[0]);
		else if (name.equals("cos"))
			return Math.cos(args[0]);
		else if (name.equals("rad"))
			return args[0] * (Math.PI / 180);
		else if (name.equals("deg"))
			return args[0] * (180 / Math.PI);
		else if (name.equals("min"))
			return Math.min(args[0], args[1]);
		else if (name.equals("max"))
			return Math.max(args[0], args[1]);
		else if (name.equals("mod"))
			return args[0] % args[1];
		else if (name.equals("hypot2"))
			return Math.sqrt(
				args[0] * args[0] +
				args[1] * args[1]);
		else if (name.equals("hypot3"))
			return Math.sqrt(
				args[0] * args[0] +
				args[1] * args[1] +
				args[2] * args[2]);
		else if (name.equals("iif"))
			return args[0] != 0 ? args[1] : args[2];
		else
			// Should never happen, but just in case
			throw new RuntimeException(
				"Unknown function: " + name);
	}

	public double call_user_fn(final String name, final Double[] args) {
		final String tmp_line = line;
		final int tmp_cursor = cursor;
		final Map<String, Double> tmp_variables = variables;
		
		line = function_code.get(name);
		cursor = 0;
		variables = new HashMap<String, Double>();
		final String argnames[] = function_args.get(name);
		for (int i = 0; i < argnames.length; i++)
			variables.put(argnames[i], args[i]);
		
		final double result;
		try {
			result = parse_expression();
		} finally {
			variables = tmp_variables;
			cursor = tmp_cursor;
			line = tmp_line;
		}
		return result;
	}

	public void run_program() {
		for (String i : function_code.keySet())
			function_args.remove(i);
		function_code.clear();
		dstack.clear();
		rstack.clear();
		addr.clear();
		addr.addAll(program.keySet());
		crt_line = 0;
		continue_program();
	}

	public void continue_program() {
		int line_num = 0;
		stop = false;
		try {
			while (crt_line < addr.size() && !stop) {
				line_num = addr.get(crt_line);
				line = program.get(line_num);
				crt_line++;
				cursor = 0;
				parse_statement();
			}
		} catch (RuntimeException e) {
			error.print(e);
			error.print(" in line ");
			error.print(line_num);
			error.print(" column ");
			error.println(cursor);
		}
	}
	
	public boolean stopped() { return stop; }
	
	public void list_program() {
		for (int i : program.keySet()) {
			output.print(i);
			output.print("\t");
			output.println(program.get(i));
		}
	}
	
	public void parse_line() {
		if (match_number()) {
			final int ln = (int) Double.parseDouble(token);
			program.put(ln, line.substring(cursor).trim());
		} else {
			parse_statement();
		}
	}
	
	public void load_file(final String fn) {
		try {
			final BufferedReader f =
				new BufferedReader(new FileReader(fn));
			String ln;
			do {
				ln = f.readLine();
				if (ln != null) {
					line = ln;
					cursor = 0;
					parse_line();
				}
			} while (ln != null);
			f.close();
		} catch (FileNotFoundException e) {
			error.println(e);
		} catch (IOException e) {
			error.println(e);
		}
	}
	
	public void save_file(final String fn) {
		try {
			final PrintStream f = new PrintStream(fn);
			for (Integer i : program.keySet()) {
				f.print(i);
				f.print("\t");
				f.println(program.get(i));
			}
			f.close();
		} catch (FileNotFoundException e) {
			error.println(e);
		}
	}
	
	public void command_loop(final String banner) {
		output.println(banner);
		boolean done = false;
		while (!done) {
			output.print("> ");
			try {
				line = input.readLine();
				if (line == null) break;
				if (line.length() == 0) continue;
			} catch (IOException e) {
				error.println(e);
				continue;
			}
			
			cursor = 0;
			
			if (Character.isDigit(line.charAt(0))) {
				parse_line();
			} else if (!match_keyword()) {
				error.println("Command expected");
			} else if (token.equals("bye")) {
				done = true;
			} else if (token.equals("list")) {
				list_program();
			} else if (token.equals("run")) {
				run_program();
			} else if (token.equals("continue")) {
				continue_program();
			} else if (token.equals("clear")) {
				variables.clear();
			} else if (token.equals("new")) {
				program.clear();
			} else if (token.equals("delete")) {
				if (match_number()) {
					final int line_num = (int)
						Double.parseDouble(token);
					program.remove(line_num);
				} else {
					error.println("Line # expected");
				}
			} else if (token.equals("load")) {
				if (match_string()) {
					load_file(token);
					output.println("File loaded");
				} else {
					error.println("String expected");
				}
			} else if (token.equals("save")) {
				if (match_string()) {
					save_file(token);
					output.println("File saved");
				} else {
					error.println("String expected");
				}
			} else {
				try {
					dispatch_statement();
				} catch (RuntimeException e) {
					error.print(e);
					error.print(" in column ");
					error.println(cursor);
				}
			}
		}
	}
	
	public static void main(String[] args) {
		Basic basic = new Basic();
		
		if (args.length > 0) {
			for (int i = 0; i < args.length; i++)
				basic.load_file(args[i]);
			basic.run_program();
			if (!basic.stop)
				return;
		}
		
		basic.command_loop(
			"Tinycat BASIC v1.1.1 READY\nType BYE to quit.");
	}
}
