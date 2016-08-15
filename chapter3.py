#!/usr/bin/python3

from __future__ import division

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
	if not match_keyword():
		raise SyntaxError("Statement expected")
	
	stmt = token.lower()
		
	if stmt == "let":
		parse_let()
	elif stmt == "print":
		parse_print()
	else:
		raise SyntaxError("Unknown statement")

variables = {}

def parse_let():
	if not match_varname():
		raise SyntaxError("Variable expected")
		
	var_name = token.lower()
	
	if not match("="):
		raise SyntaxError("'=' expected")

	variables[var_name] = parse_expression()
	
	if not match_eol():
		raise SyntaxError("End of line expected")

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
	if not match_eol():
		raise SyntaxError("End of line expected")

def parse_value():
	global token
	if match_string():
		return token
	else:
		return parse_expression()

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

#line = "let c = 37"
#cursor = 0
#parse_statement()
#line = 'print "f = ", 32 + c * (9 / 5)'
#cursor = 0
#parse_statement()

print("Basic v0.2 READY\n")
done = False
while not done:
	line = input("> ")
	if line.lower() == "bye":
		done = True
	else:
		cursor = 0
		try:
			parse_statement()
		except Exception as e:
			print(str(e) +
				" in column " +
				str(cursor))
