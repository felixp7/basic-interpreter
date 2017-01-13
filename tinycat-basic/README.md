Tinycat BASIC
=============


Tinycat BASIC is a line-number BASIC dialect that can be implemented in less than a thousand lines of Java or C++ (barring extensions to the core). It achieves that by relying on direct interpretation and having no type system. Its name is meant to honor the classic dialect Tiny BASIC as inspiration and ancestry.

Rationale
---------

While the hardware limitations that made Tiny BASIC desirable are largely a thing of the past, having programming language dialects that can be *trivially* implemented remains a good idea. It reduces software dependencies and black box components.

Features
--------

Tinycat BASIC has a number of useful additions on top of its model:

- floating point numbers;
- arbitrary variable names;
- control structures like DO ... LOOP and FOR ... NEXT;
- the logical operators: AND, OR, NOT;
- power and flooring division operators;
- functions, both built-in and user-defined*;
- random number generation.

*) Note: the new Go implementation lacks DEF FN.

Some features would *not* be trivial to add, and therefore outside the scope of this project:

- arrays;
- string variables.

Others can be added easily, but would cause more trouble than it's worth:

- multiple statements per line; they require littering the source code with special cases, and lower performance for little benefit.

Performance
-----------

The reference Python implementation is 225 times slower than the host language, after optimizations. The Java implementation proved harder to benchmark, as a long-running interpreter runs progressively faster. That said, it seems to be roughly 40 times slower than pure Java on a fresh start, and gets to within 40%-60% of a compiled Java program -- almost as if the interpreter wasn't in the way anymore! Last but not least, the Go implementation is 160 times slower than native code, which makes it 4 times slower than the Java version after JIT optimization.

Incidentally, Python itself appears to be twice as fast as Java for simple looping and arithmetic. But Java is much better suited for interpreting another language. Or at least this interpreter architecture happens to suit Java unusually well.

I took advantage of the extra performance to make the Java interpreter extensible. That slowed it down again a little, but I think it's worth it.

Extending Tinycat BASIC
-----------------------

The Java implementation is fully extensible: by subclassing the interpreter, you can add more statements, built-in functions and even expression kinds.

In the Go implementation, you can only add more built-in functions without changing the source code.

The Python implementation isn't extensible at this time.

Supported statements
--------------------

	LET name "=" expression
	IF expression THEN statement
	GOTO expression
	PRINT (string | expression)? ("," (string | expression))* ";"?
	INPUT (string ",")? name ("," name)?
	FOR name = expression TO expression (STEP expression)?
	NEXT name
	GOSUB expression
	RETURN
	DO
	LOOP (WHILE | UNTIL) expression
	REM text
	DEF FN name "(" (name ("," name)?)? ")" "=" expression**
	RANDOMIZE expression?
	STOP
	END
	
**) Note: absent in the Go edition.

Expression syntax
-----------------

	expression ::= disjunction
	disjunction ::= conjunction ("or" conjunction)*
	conjunction ::= negation ("and" negation)*
	negation ::= "not"? comparison
	comparison ::= math_expr (comp_oper math_expr)?
	comp_oper ::= "<" | ">" | "<=" | ">=" | "<>" | "="
	
	math_expr ::= term (("+"|"-") term)*
	term ::= factor (("*" | "/" | "\") factor)*
	factor ::= ("+"|"-")? (number | name | funcall | "(" expression ")")
	funcall ::= name ("(" expr_list? ")")?
	expr_list ::= expression ("," expression)*

Roadmap
-------

The next version will make all three editions embeddable.
