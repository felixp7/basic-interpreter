import javax.swing.JOptionPane;
import java.io.IOException;

/** Example of how to extend Tinycat Basic with new language constructs. */
public class DlgBasic extends Basic {
	public DlgBasic() {
		super();
		function_args.put("e", new String[0]);
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
		if (name.equals("e"))
			return Math.E;
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
		
		basic.command_loop("Dialog BASIC v1.0 READY");
	}
}
