#!/usr/bin/python3

"""Embeddable line-number Basic interpreter in under 1000 lines of Python."""

from __future__ import division
from __future__ import print_function

import math
import random
import time

try:
	import readline
except ImportError as e:
	print("(Command line editing is unavailable.)\n")

line = ""
cursor = 0 # Index of current reading position
token = None # The last token matched, if any

def skip_whitespace():
	global cursor
	while cursor < len(line) and line[cursor].isspace():
		cursor += 1

def match_keyword():
	global cursor, token
	
	#skip_whitespace()
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
	if cursor >= len(line):
		raise IndexError("Unclosed string")
	while line[cursor] != '"':
		cursor += 1
		if cursor >= len(line):
			raise IndexError("Unclosed string")
	cursor += 1 # Skip the closing double quote.
	
	# Save string value without the double quotes.
	token = line[mark + 1:cursor - 1]
	return True

def parse_statement():
	if not match_keyword():
		raise SyntaxError("Statement expected")
	
	stmt = token.lower()
		
	if stmt in statements:
		statements[stmt]()
	else:
		raise SyntaxError("Unknown statement: " + stmt)

variables = {}

def parse_rem():
	global cursor
	cursor = len(line)

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
	value = parse_value()
	while match(","):
		value += parse_value()
	if match(";"):
		print(value, end="")
	else:
		print(value)

def parse_value():
	global token
	if match_string():
		return token
	else:
		return "{:1g}".format(parse_disjunction())

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
	t1 = parse_power()
	while match_mul_div():
		op = token
		t2 = parse_power()
		if op == "*":
			t1 *= t2
		elif op == "/":
			t1 /= t2
		elif op == "\\":
			t1 //= t2
		else:
			raise SyntaxError("Unknown operator: " + op)
	return t1

def parse_power():
	t1 = parse_factor()
	if match("^"):
		return t1 ** parse_power()
	else:
		return t1

function_args = {
	"timer": [],
	"rnd": [],
	"pi": [],
	"int": ["n"],
	"abs": ["n"],
	"sqr": ["n"],
	"sin": ["n"],
	"cos": ["n"],
	"rad": ["n"],
	"deg": ["n"],
	"min": ["a", "b"],
	"max": ["a", "b"],
	"mod": ["a", "b"],
	"hypot2": ["a", "b"],
	"hypot3": ["a", "b", "c"],
	"iif": ["a", "b", "c"],
}

def parse_factor():
	global token
	
	if match("-"):
		signum = -1
	else:
		signum = 1
	
	if match_number():
		return float(token) * signum
	elif match_varname():
		name = token.lower()
		if name in function_args:
			args = parse_args()
			return call_fn(name, args) * signum
		elif name in variables:
			return variables[name] * signum
		else:
			raise NameError("Var not found: " + name)
	elif match("("):
		value = parse_disjunction()
		if match(")"):
			return value * signum
		else:
			raise SyntaxError("Missing ')'")
	else:
		raise SyntaxError("Expression expected")

def parse_args():
	if match("("):
		if match(")"):
			return []
		args = [parse_disjunction()]
		while match(","):
			args.append(parse_disjunction())
		if match(")"):
			return args
		else:
			raise SyntaxError("Missing ')'")
	else:
		return []

function_code = {}

def call_fn(name, args):
	if len(args) != len(function_args[name]):
		raise RuntimeError("Bad argument count")
	elif name in function_code:
		return call_user_fn(name, args)
	elif name in functions:
		return functions[name](*args)
	else:
		# Should never happen, but just in case
		raise NameError("Unknown function: " + name)

def parse_def():
	global cursor
	
	if not match_nocase("fn"):
		raise SyntaxError("Missing 'fn'")
	if not match_varname():
		raise SyntaxError("Name expected")

	name = token.lower()

	if name in function_args:
		raise RuntimeError("Duplicate function: " + name)
	if not match("("):
		raise SyntaxError("Missing '('")
	
	if match(")"):
		args = []
	else:
		args = parse_varlist()
		if not match(")"):
			raise SyntaxError("Missing ')'")
	
	if not match("="):
		raise SyntaxError("Missing '='")
	
	function_args[name] = args
	function_code[name] = line[cursor:]
	cursor = len(line)

def call_user_fn(name, args):
	global line, cursor, variables
	
	tmp_line = line
	tmp_cursor = cursor
	tmp_variables = variables
	
	line = function_code[name]
	cursor = 0
	variables = {}
	argnames = function_args[name]
	for i in range(len(argnames)):
		variables[argnames[i]] = args[i]
	
	try:
		result = parse_disjunction()
	finally:
		variables = tmp_variables
		cursor = tmp_cursor
		line = tmp_line
	
	return result

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
	elif match("\\"):
		token = "\\"
		return True
	else:
		return False

def parse_if():
	global cursor
	condition = parse_disjunction()
	if match_nocase("then"):
		if condition != 0:
			skip_whitespace()
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

#def match_relation():
	#global token
	#for op in ["=", "<>", "<=", ">=", "<", ">"]:
		#if match(op):
			#token = op
			#return True
	#return False

def match_relation():
	global token, cursor
	skip_whitespace()
	for op in ["=", "<>", "<=", ">=", "<", ">"]:
		if line.startswith(op, cursor):
			token = op
			cursor += len(op)
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
	skip_whitespace()
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
	varlist = [token.lower()]
	while match(","):
		if not match_varname():
			raise SyntaxError("Var expected")
		varlist.append(token.lower())
	return varlist

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
		parse_statement()

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
	stack.clear()
	for i in function_code.keys():
		del function_code[i]
		del function_args[i]
	continue_program()

def continue_program():
	global crt_line, line, cursor, stop
	stop = False
	try:
		while crt_line < len(addr) and not stop:
			line_num = addr[crt_line]
			line = program[line_num]
			crt_line += 1
			cursor = 0
			parse_statement()
	except Exception as e:
		print(e, "in line", line_num, "column", cursor)

def parse_goto():
	global crt_line
	line_num = int(parse_expression())
	if line_num in addr:
		crt_line = addr.index(line_num)
	else:
		raise ValueError("Line not found: " + line_num)

stack = []

def parse_gosub():
	global crt_line
	line_num = int(parse_expression())
	if line_num in addr:
		stack.append(crt_line)
		crt_line = addr.index(line_num)
	else:
		raise ValueError("Line not found: " + line_num)

def parse_return():
	global crt_line
	if len(stack) > 0:
		crt_line = stack.pop()
	else:
		raise RuntimeError("Stack underflow")

def parse_end():
	global crt_line
	crt_line = len(addr)

def parse_stop():
	global stop
	stop = True

def parse_do():
	stack.append(crt_line)

def parse_loop():
	global crt_line
	if match_nocase("while"):
		if parse_disjunction():
			crt_line = stack[-1]
		else:
			stack.pop()
	elif match_nocase("until"):
		if parse_disjunction():
			stack.pop()
		else:
			crt_line = stack[-1]
	else:
		raise SyntaxError("Condition expected")

def parse_for():
	if not match_varname():
		raise SyntaxError("Variable expected")

	var_name = token.lower()
	
	if not match("="):
		raise SyntaxError("'=' expected")

	variables[var_name] = parse_expression()
	
	if not match_nocase("to"):
		raise SyntaxError("'to' expected")

	limit = parse_expression()
	
	if match_nocase("step"):
		step = parse_expression()
		if step == 0:
			raise ValueError("Infinite loop")
	else:
		step = 1

	stack.append(crt_line)
	stack.append(limit)
	stack.append(step)

def parse_next():
	global crt_line

	if not match_varname():
		raise SyntaxError("Variable expected")

	var_name = token.lower()

	if var_name not in variables:
		raise NameError("Var not found: " + var_name)
	
	variables[var_name] += stack[-1]
	if stack[-1] > 0:
		done = variables[var_name] > stack[-2]
	elif stack[-1] < 0:
		done = variables[var_name] < stack[-2]
	
	if done:
		stack.pop()
		stack.pop()
		stack.pop()
	else:
		crt_line = stack[-3]

def parse_randomize():
	if match_eol():
		random.seed()
	else:
		random.seed(int(parse_expression()))

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
			print(i, program[i], sep="\t", file=f)

def load_program():
	global line, cursor
	if not match_string():
		raise SyntaxError("Filename expected")
	with open(token, "r") as f:
		for i in f:
			line = i.strip()
			cursor = 0
			parse_line()

statements = {
	"let": parse_let,
	"print": parse_print,
	"input": parse_input,
	"if": parse_if,
	"goto": parse_goto,
	"gosub": parse_gosub,
	"return": parse_return,
	"end": parse_end,
	"stop": parse_stop,
	"do": parse_do,
	"loop": parse_loop,
	"for": parse_for,
	"next": parse_next,
	"def": parse_def,
	"rem": parse_rem,
	"randomize": parse_randomize
}

functions = {
	"timer": lambda: time.process_time(),
	"rnd": lambda: random.random(),
	"pi": lambda: math.pi,
	"int": lambda n: math.trunc(n),
	"abs": lambda n: abs(n),
	"sqr": lambda n: math.sqrt(n),
	"sin": lambda n: math.sin(n),
	"cos": lambda n: math.cos(n),
	"rad": lambda n: math.radians(n),
	"deg": lambda n: math.degrees(n),
	"min": lambda a, b: min(a, b),
	"max": lambda a, b: max(a, b),
	"mod": lambda a, b: a % b,
	"hypot2": lambda a, b: math.hypot(a, b),
	"hypot3": lambda a, b, c: math.sqrt(a * a + b * b + c * c),
	"iif": lambda a, b, c: a and b or c
}

def command_loop(banner):
	global line, cursor
	print(banner)
	done = False
	while not done:
		try:
			line = input("> ")
		except SyntaxError as e:
			print(e)
			continue
		except EOFError:
			break
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
				print(e, "in column", cursor)

if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1:
		for i in sys.argv[1:]:
			line = '"' + i + '"'
			cursor = 0
			load_program()
		run_program()
		if stop:
			command_loop("Tinycat BASIC v1.1 READY\n")
	else:
		command_loop("Tinycat BASIC v1.1 READY\n")
