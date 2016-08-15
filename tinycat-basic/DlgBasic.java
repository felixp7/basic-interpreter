import javax.swing.JOptionPane;
import java.io.IOException;

/** Example of how to extend Tinycat Basic with new language constructs. */
public class DlgBasic extends Basic {
	public DlgBasic() {
		super();
		function_args.put("pi", new String[0]);
	}
	
	public void dispatch_statement() {
		if (token.equals("alert"))
			parse_alert();
		else
			super.dispatch_statement();
	}
	
	public void parse_alert() {
		String value = parse_printable();
		while (match(","))
			value += parse_printable();
		JOptionPane.showMessageDialog(null, value);
	}
	
	public double parse_expression() {
		if (match_nocase("confirm")) {
			if (!match_string())
				throw new RuntimeException("String expected");
			final int answer =
				JOptionPane.showConfirmDialog(
					null, token, "DlgBasic asks:",
					JOptionPane.YES_NO_OPTION);
			return (answer == JOptionPane.YES_OPTION) ? -1 : 0;
		} else if (match_nocase("prompt")) {
			if (!match_string())
				throw new RuntimeException("String expected");
			final String answer =
				JOptionPane.showInputDialog(null, token);
			if (answer == null)
				return 0;
			else if (answer.matches("^\\d+(\\.\\d+)?$"))
				return Double.valueOf(answer);
			else
				return 0;
		} else {
			return super.parse_expression();
		}
	}

	public double call_builtin(final String name, final Double[] args) {
		if (name.equals("pi"))
			return Math.PI;
		else
			return super.call_builtin(name, args);
	}
	
	public static void main(String[] args) {
		Basic basic = new DlgBasic();
		
		if (args.length > 0) {
			for (int i = 0; i < args.length; i++)
				basic.load_file(args[i]);
			basic.run_program();
			if (!basic.stop)
				return;
		}
		
		System.out.println("Dialog BASIC v1.0 READY");
		boolean done = false;
		while (!done) {
			System.out.print("> ");
			try {
				basic.line = basic.input.readLine();
			} catch (IOException e) {
				System.err.println(e);
				continue;
			}
			
			basic.cursor = 0;
			
			if (Character.isDigit(basic.line.charAt(0))) {
				basic.parse_line();
			} else if (!basic.match_keyword()) {
				System.err.print("Command expected");
			} else if (basic.token.equals("bye")) {
				done = true;
			} else if (basic.token.equals("list")) {
				basic.list_program();
			} else if (basic.token.equals("run")) {
				basic.run_program();
			} else if (basic.token.equals("continue")) {
				basic.continue_program();
			} else if (basic.token.equals("clear")) {
				basic.variables.clear();
			} else if (basic.token.equals("new")) {
				basic.program.clear();
			} else if (basic.token.equals("delete")) {
				if (basic.match_number()) {
					final int line_num = (int)
						Double.parseDouble(
							basic.token);
					basic.program.remove(line_num);
				} else {
					System.err.println("Line # expected");
				}
			} else if (basic.token.equals("load")) {
				if (basic.match_string()) {
					basic.load_file(basic.token);
					System.out.println("File saved");
				} else {
					System.err.println("String expected");
				}
			} else if (basic.token.equals("save")) {
				if (basic.match_string()) {
					basic.save_file(basic.token);
					System.out.println("File loaded");
				} else {
					System.err.println("String expected");
				}
			} else {
				try {
					basic.dispatch_statement();
				} catch (RuntimeException e) {
					System.err.print(e);
					System.err.print(" in column ");
					System.err.println(basic.cursor);
				}
			}
		}
	}
}
