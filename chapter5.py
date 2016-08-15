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

def run_program():
	global addr, crt_line, line, cursor
	addr = sorted(program.keys())
	crt_line = 0
	while crt_line < len(addr):
		line_num = addr[crt_line]
		line = program[line_num]
		crt_line += 1
		cursor = 0
		parse_block()

def parse_goto():
	global crt_line
	line_num = int(parse_expression())
	if line_num in addr:
		crt_line = addr.index(line_num)
	else:
		raise ValueError("Line not found")

stack = []

def parse_gosub():
	global crt_line
	line_num = int(parse_expression())
	if line_num in addr:
		stack.append(crt_line)
		crt_line = addr.index(line_num)
	else:
		raise ValueError("Line not found")

def parse_return():
	global crt_line
	if len(stack) > 0:
		crt_line = stack.pop()
	else:
		raise RuntimeError("Stack underflow")

def parse_end():
	global crt_line
	crt_line = len(addr)

test = ['10 print "main program"',
	'20 gosub 100',
	'25 print "and back"',
	'30 end',
	'100 print "sub #1"',
	'110 gosub 200',
	'120 return',
	'200 print "sub #2"',
	'210 return',
	'1000 REM end program']
for i in test:
	line = i
	cursor = 0
	parse_line()

list_program()
run_program()
