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
- functions, both built-in and user-defined;
- random number generation;
- a modulo function.

Some features would *not* be trivial to add, and therefore outside the scope of this project:

- arrays;
- string variables.

Others can be added easily, but would cause more trouble than it's worth:

- multiple statements per line; they require littering the source code with special cases, and lower performance for little benefit.

Performance
-----------

The reference Python implementation is 225 times slower than the host language, after optimizations. The Java implementation proved harder to benchmark, as a long-running interpreter runs progressively faster. That said, it seems to be roughly 40 times slower than pure Java on a fresh start, and gets to within 40%-60% of a compiled Java program -- almost as if the interpreter wasn't in the way anymore!

Incidentally, Python itself appears to be twice as fast as Java for simple looping and arithmetic. But Java is much better suited for interpreting another language.

I took advantage of the extra performance to make the Java interpreter extensible. That slowed it down again a little, but I think it's worth it.

Expression syntax
-----------------

	disjunction ::= conjunction ("or" conjunction)*
	conjunction ::= negation ("and" negation)*
	negation ::= "not"? comparison
	comparison ::= math_expr (comp_oper math_expr)?
	comp_oper ::= "<" | ">" | "<=" | ">=" | "<>" | "="
	
	math_expr ::= term (("+"|"-") term)*
	term ::= factor (("*" | "/") factor)*
	factor ::= ("+"|"-")? (number | identifier | "(" disjunction ")")
