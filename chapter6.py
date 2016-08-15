#!/usr/bin/python3

from __future__ import division
from __future__ import print_function

line = ""
cursor = 0 # Index of current reading position
token = None # The last token matched, if any

def skip_whitespace():
	global cursor
	while cursor < len(line) and line[cursor].isspace():
		cursor += 1

def match_keyword():
	global cursor, token
	
	skip_whitespace()
	if cursor >= len(line) or not line[cursor].isalpha():
		return False
		
	mark = cursor
	while cursor < len(line) and line[cursor].isalpha():
		cursor += 1
	token = line[mark:cursor]
	return True

def match_number():
	global cursor, token
	
	skip_whitespace()
	if cursor >= len(line) or not line[cursor].isdigit():
		return False
		
	mark = cursor
	while cursor < len(line) and line[cursor].isdigit():
		cursor += 1
	if cursor < len(line) and line[cursor] == ".":
		cursor += 1
		while cursor < len(line) and line[cursor].isdigit():
			cursor += 1
	token = line[mark:cursor]
	return True

def match_varname():
	global cursor, token
	
	skip_whitespace()
	if cursor >= len(line) or not line[cursor].isalpha():
		return False
		
	mark = cursor
	while cursor < len(line) and line[cursor].isalnum():
		cursor += 1
	token = line[mark:cursor]
	return True

def match_string():
	global cursor, token
	
	skip_whitespace()
	if cursor >= len(line) or line[cursor] != '"':
		return False
		
	mark = cursor
	cursor += 1 # Skip the opening double quote.
	while line[cursor] != '"':
		cursor += 1
		if cursor >= len(line):
			raise IndexError("Unclosed string")
	cursor += 1 # Skip the closing double quote.
	
	# Save string value without the double quotes.
	token = line[mark + 1:cursor - 1]
	return True

def parse_statement():
	global cursor
	
	if not match_keyword():
		raise SyntaxError("Statement expected")
	
	stmt = token.lower()
		
	if stmt == "let":
		parse_let()
	elif stmt == "print":
		parse_print()
	elif stmt == "input":
		parse_input()
	elif stmt == "if":
		parse_if()
	elif stmt == "goto":
		parse_goto()
	elif stmt == "gosub":
		parse_gosub()
	elif stmt == "return":
		parse_return()
	elif stmt == "end":
		parse_end()
	elif stmt == "stop":
		parse_stop()
	elif stmt == "rem":
		cursor = len(line)
	else:
		raise SyntaxError("Unknown statement")

variables = {}

def parse_let():
	if not match_varname():
		raise SyntaxError("Variable expected")
		
	var_name = token.lower()
	
	if not match("="):
		raise SyntaxError("'=' expected")

	variables[var_name] = parse_disjunction()

def match(text):
	global cursor
	skip_whitespace()
	if line.startswith(text, cursor):
		cursor += len(text)
		return True
	else:
		return False

def match_eol():
	skip_whitespace()
	return cursor >= len(line)

def parse_print():
	if match_eol():
		print()
		return
	value = str(parse_value())
	while match(","):
		value += str(parse_value())
	print(value)

def parse_value():
	global token
	if match_string():
		return token
	else:
		return parse_disjunction()

def parse_expression():
	t1 = parse_term()
	while match_add_sub():
		op = token
		t2 = parse_term()
		if op == "+":
			t1 += t2
		elif op == "-":
			t1 -= t2
		else:
			raise SyntaxError(op)
	return t1
	
def parse_term():
	t1 = parse_factor()
	while match_mul_div():
		op = token
		t2 = parse_factor()
		if op == "*":
			t1 *= t2
		elif op == "/":
			t1 /= t2
		else:
			raise SyntaxError(op)
	return t1

def parse_factor():
	global token
	
	if match("-"):
		signum = -1
	else:
		signum = 1
	
	if match_number():
		return float(token) * signum
	elif match_varname():
		token = token.lower()
		if token in variables:
			return variables[token] * signum
		else:
			raise NameError("Var not found")
	elif match("("):
		value = parse_expression()
		if match(")"):
			return value * signum
		else:
			raise SyntaxError("Missing ')'")
	else:
		raise SyntaxError("Expression expected")

def match_add_sub():
	global token
	if match("+"):
		token = "+"
		return True
	elif match("-"):
		token = "-"
		return True
	else:
		return False

def match_mul_div():
	global token
	if match("*"):
		token = "*"
		return True
	elif match("/"):
		token = "/"
		return True
	else:
		return False

def parse_if():
	global cursor
	condition = parse_disjunction()
	if match_nocase("then"):
		if condition != 0:
			parse_statement()
		else:
			cursor = len(line)
	else:
		raise SyntaxError("IF without THEN")
	
def parse_comparison():
	lside = parse_expression()
	if not match_relation():
		return lside
	else:
		op = token
		rside = parse_expression()
		if op == "<=":
			return -(lside <= rside)
		elif op == "<":
			return -(lside < rside)
		elif op == "=":
			return -(lside == rside)
		elif op == "<>":
			return -(lside != rside)
		elif op == ">":
			return -(lside > rside)
		elif op == ">=":
			return -(lside >= rside)

def match_relation():
	global token
	for op in ["=", "<>", "<=", ">=", "<", ">"]:
		if match(op):
			token = op
			return True
	return False

def parse_disjunction():
	lside = parse_conjunction()
	while match_nocase("or"):
		rside = -(parse_conjunction() != 0)
		lside = -(lside != 0 or rside != 0)
	return lside

def parse_conjunction():
	lside = parse_negation()
	while match_nocase("and"):
		rside = -(parse_negation() != 0)
		lside = -(lside != 0 and rside != 0)
	return lside
	
def parse_negation():
	if match_nocase("not"):
		return -(parse_comparison() == 0)
	else:
		# Leave purely arithmetic results intact
		return parse_comparison()

def match_nocase(kw):
	global cursor
	mark = cursor
	if not match_keyword():
		cursor = mark
		return False
	elif token.lower() != kw.lower():
		cursor = mark
		return False
	else:
		return True

def parse_input():
	if match_string():
		prompt = token
		if not match(","):
			raise SyntaxError("Comma expected")
	else:
		prompt = ""
	input_vars = parse_varlist()
	data = input(prompt).split(",")
	for i in range(len(input_vars)):
		v = input_vars[i]
		if i < len(data):
			variables[v] = float(data[i])
		else:
			variables[v] = 0

def parse_varlist():
	if not match_varname():
		raise SyntaxError("Var expected")
	varlist = [token]
	while match(","):
		if not match_varname():
			raise SyntaxError("Var expected")
		varlist.append(token)
	return varlist

def parse_block():
	parse_statement()
	while match(":"):
		parse_statement()
	if not match_eol():
		raise SyntaxError("End of line expected")

program = {}

def parse_line():
	global cursor
	skip_whitespace()
	mark = cursor
	while cursor < len(line) and line[cursor].isdigit():
		cursor += 1
	if cursor > mark:
		linenum = int(line[mark:cursor])
		skip_whitespace()
		program[linenum] = line[cursor:]
	else:
		parse_block()

def list_program():
	addr = sorted(program.keys())
	for i in addr:
		print(i, program[i], sep="\t")

addr = []
crt_line = -1
stop = False

def run_program():
	global addr, crt_line
	addr = sorted(program.keys())
	crt_line = 0
	continue_program()

def continue_program():
	global crt_line, line, cursor, stop
	stop = False
	while crt_line < len(addr) and not stop:
		line_num = addr[crt_line]
		line = program[line_num]
		crt_line += 1
		cursor = 0
		parse_block()

def parse_goto():
	global crt_line, cursor
	line_num = int(parse_expression())
	if line_num in addr:
		crt_line = addr.index(line_num)
		cursor = len(line)
	else:
		raise ValueError("Line not found")

stack = []

def parse_gosub():
	global crt_line, cursor
	line_num = int(parse_expression())
	if line_num in addr:
		stack.append(crt_line)
		crt_line = addr.index(line_num)
		cursor = len(line)
	else:
		raise ValueError("Line not found")

def parse_return():
	global crt_line, cursor
	if len(stack) > 0:
		crt_line = stack.pop()
		cursor = len(line)
	else:
		raise RuntimeError("Stack underflow")

def parse_end():
	global crt_line, cursor
	crt_line = len(addr)
	cursor = len(line)

def parse_stop():
	global cursor, stop
	stop = True
	cursor = len(line)

def parse_delete():
	line_num1 = parse_expression()
	if match(","):
		line_num2 = parse_expression()
		addr = sorted(program.keys())
		for i in addr:
			if line_num1 <= i <= line_num2:
				del program[i]
	else:
		del program[line_num1]
		
def save_program():
	if not match_string():
		raise SyntaxError("Filename expected")
	addr = sorted(program.keys())
	with open(token, "w") as f:
		for i in addr:
			print(
				i,
				program[i],
				sep="\t",
				file=f)

def load_program():
	global line, cursor
	if not match_string():
		raise SyntaxError("Filename expected")
	with open(token, "r") as f:
		for i in f:
			line = i.strip()
			cursor = 0
			parse_line()

print("Basic v0.5 READY\n")
done = False
while not done:
	line = input("> ")
	cursor = 0
	if match_nocase("bye"):
		done = True
	elif match_nocase("list"):
		list_program()
	elif match_nocase("run"):
		run_program()
	elif match_nocase("continue"):
		continue_program()
	elif match_nocase("clear"):
		variables.clear()
	elif match_nocase("new"):
		program.clear()
	elif match_nocase("delete"):
		parse_delete()
	elif match_nocase("save"):
		save_program()
	elif match_nocase("load"):
		load_program()
	else:
		try:
			parse_line()
		except Exception as e:
			print(e,
				"in column",
				cursor)
