// Extensible line-number Basic interpreter in under 1000 lines of Go.
package main

import (
	"fmt"
	"errors"
	"unicode"
	"strings"
	"strconv"
	"math"
	"math/rand"
	"container/list"
	"sort"
	"time"
	"bufio"
	"os"
)

var Ins = os.Stdin
var Outs = os.Stdout
var Errs = os.Stderr

type Variables map[string]float64
type Program map[int]string

func (prg Program) LineNumbers() []int {
	addr := make([]int, 0, len(prg))
	for ln, _ := range prg {
		addr = append(addr, ln)
	}
	sort.Ints(addr)
	return addr
}

// Encapsulates all the state needed to interpret a Basic program.
type Context struct {
	Line string
	Cursor int
	Token string
	
	Variables
	Program
	
	line_num int
	crt_line int
	stop bool
	addr []int
	stack list.List
}

type Builtin struct {
	Arity int
	Call func (args ...float64) float64
}

var Functions = map[string]Builtin {
	"timer": {0, func (args ...float64) float64 {
		return float64(time.Now().UnixNano()) / (1000 * 1000 * 1000)
	}},
	"rnd": {0, func (args ...float64) float64 {
		return rand.Float64()
	}},
	"pi": {0, func (args ...float64) float64 {
		return math.Pi
	}},
	"int": {1, func (args ...float64) float64 {
		return math.Trunc(args[0])
	}},
	"abs": {1, func (args ...float64) float64 {
		return math.Abs(args[0])
	}},
	"sqr": {1, func (args ...float64) float64 {
		return math.Sqrt(args[0])
	}},
	"sin": {1, func (args ...float64) float64 {
		return math.Sin(args[0])
	}},
	"cos": {1, func (args ...float64) float64 {
		return math.Cos(args[0])
	}},
	"rad": {1, func (args ...float64) float64 {
		return args[0] * (math.Pi / 180)
	}},
	"deg": {1, func (args ...float64) float64 {
		return args[0] * (180 / math.Pi)
	}},
	"min": {2, func (args ...float64) float64 {
		return math.Min(args[0], args[1])
	}},
	"max": {2, func (args ...float64) float64 {
		return math.Max(args[0], args[1])
	}},
	"mod": {2, func (args ...float64) float64 {
		return float64(int64(args[0]) % int64(args[1]))
	}},
	"hypot2": {2, func (args ...float64) float64 {
		return math.Sqrt(args[0] * args[0] + args[1] * args[1])
	}},
	"hypot3": {3, func (args ...float64) float64 {
		return math.Sqrt(
			args[0] * args[0] +
			args[1] * args[1] +
			args[2] * args[2])
	}},
	"iif": {3, func (args ...float64) float64 {
		if args[0] != 0 {
			return args[1]
		} else {
			return args[2]
		}
	}},
}

func CallBuiltin(name string, args []float64) (float64, error) {
	builtin, ok := Functions[name]
	if !ok {
		return 0, errors.New("No such function: " + name)
	} else if len(args) != builtin.Arity {
		return 0, errors.New("Bad argument count in call to " + name)
	} else {
		return builtin.Call(args...), nil
	}
}

// Parse (and run) the content of Context.Line, starting from Context.Cursor.
func (ctx *Context) ParseLine() error {
	if (ctx.MatchNumber()) {
		value, err := strconv.Atoi(ctx.Token)
		if err != nil { return err }
		ctx.Program[value] = strings.TrimSpace(ctx.Line[ctx.Cursor:])
		return nil
	} else {
		return ctx.ParseStatement()
	}
}

// Parse/run the next statement from Context.Line, starting at Context.Cursor.
func (ctx *Context) ParseStatement() error {
	//ctx.SkipWhitespace()
	if ctx.MatchKeyword() {
		return ctx.DispatchStatement()
	} else {
		return errors.New(
			"Statement expected, found: " + ctx.Line[ctx.Cursor:])
	}
}

// Parse syntax for statement named in Context.Token, if known, or error out.
func (ctx *Context) DispatchStatement() error {
	switch ctx.Token {
		case "let": return ctx.ParseLet()
		case "if": return ctx.ParseIf()
		case "goto": return ctx.ParseGoto()
		case "print": return ctx.ParsePrint()
		case "input": return ctx.ParseInput()
		case "for": return ctx.ParseFor()
		case "next": return ctx.ParseNext()
		case "gosub": return ctx.ParseGosub()
		case "return": return ctx.ParseReturn()
		case "do": ctx.stack.PushFront(ctx.crt_line); return nil
		case "loop": ctx.ParseLoop(); return nil
		case "rem": ctx.Cursor = len(ctx.Line); return nil
		case "randomize": return ctx.ParseRandomize();
		case "stop": ctx.stop = true; return nil
		case "end": ctx.crt_line = len(ctx.addr); return nil
		default: return errors.New("Unknown statement: " + ctx.Token)
	}
}

func (ctx *Context) ParseLet() error {
	if !ctx.MatchVarname() {
		return errors.New(
			"Variable expected, found: " + ctx.Line[ctx.Cursor:])
	}
	var_name := ctx.Token
	if !ctx.Match("=") {
		return errors.New(
			"'=' expected, found: " + ctx.Line[ctx.Cursor:])
	}
	value, err := ctx.ParseExpression()
	if err != nil { return err }
	ctx.Variables[var_name] = value
	return nil
}

func (ctx *Context) ParseIf() error {
	condition, err := ctx.ParseExpression()
	if err != nil {
		return err
	} else if ctx.MatchNocase("then") {
		if condition != 0 {
			ctx.SkipWhitespace()
			return ctx.ParseStatement()
		} else {
			ctx.Cursor = len(ctx.Line)
			return nil
		}
	} else {
		return errors.New("IF without THEN.");
	}
}

func (ctx *Context) ParseGoto() error {
	if ctx.addr == nil { return errors.New("Program not running.") }
	ln, err := ctx.ParseArithmetic()
	if err != nil {
		return err
	} else if idx := IndexOf(int(ln), ctx.addr); idx > -1 {
		ctx.crt_line = idx
		return nil
	} else {
		return errors.New("Line not found: " + fmt.Sprintf("%d", ln))
	}
}

func (ctx *Context) ParsePrint() error {
	if ctx.MatchEol() {
		fmt.Fprintln(Outs)
		return nil
	}
	value, err := ctx.ParsePrintable()
	if err != nil { return err }
	for ctx.Match(",") {
		val, err := ctx.ParsePrintable()
		if err != nil { return err }
		value += val
	}
	if ctx.Match(";") {
		fmt.Fprint(Outs, value)
	} else {
		fmt.Fprintln(Outs, value)
	}
	return nil
}

func (ctx *Context) ParsePrintable() (string, error) {
	value, err := ctx.MatchedString()
	if err != nil {
		return "", err
	} else if value {
		return ctx.Token, nil
	} else {
		value2, err := ctx.ParseExpression()
		return fmt.Sprintf("%g", value2), err
	}
}

func (ctx *Context) MatchedString() (bool, error) {
	ctx.SkipWhitespace()

	if ctx.Cursor >= len(ctx.Line) || ctx.Line[ctx.Cursor] != '"' {
		return false, nil
	}
		
	mark := ctx.Cursor
	ctx.Cursor++ // Skip the opening double quote.
	if ctx.Cursor >= len(ctx.Line) {
		return false, errors.New("Unclosed string")
	}
	for ctx.Line[ctx.Cursor] != '"' {
		ctx.Cursor++
		if ctx.Cursor >= len(ctx.Line) {
			return false, errors.New("Unclosed string")
		}
	}
	ctx.Cursor++ // Skip the closing double quote.
	
	// Save string value without the double quotes.
	ctx.Token = ctx.Line[mark + 1:ctx.Cursor - 1]
	return true, nil
}

func (ctx *Context) ParseInput() error {
	var prompt string
	ok, err := ctx.MatchedString()
	if err != nil {
		return err
	} else if ok {
		prompt = ctx.Token
		if !ctx.Match(",") {
			return errors.New(
				"Comma expected near " + ctx.Line[ctx.Cursor:])
		}
	}
	
	input_vars, err := ctx.ParseVarlist()
	if err != nil { return err }
	fmt.Fprint(Outs, prompt)
	var data []string
	scanner := bufio.NewScanner(os.Stdin)
	if scanner.Scan() {
		data = strings.Split(scanner.Text(), ",")
	} else if err := scanner.Err(); err != nil {
		return err
	} else {
		data = make([]string, 0)
	}

	for i, varname := range input_vars {
		if i < len(data) {
			data[i] = strings.TrimSpace(data[i])
			value, err := strconv.ParseFloat(data[i], 64)
			if err != nil { return err }
			ctx.Variables[varname] = value
		} else {
			ctx.Variables[varname] = 0
		}
	}
	return nil
}

func (ctx *Context) ParseVarlist() ([]string, error) {
	if !ctx.MatchVarname() {
		return make([]string, 0), errors.New(
			"Variable expected near " + ctx.Line[ctx.Cursor:])
	}
	varlist := make([]string, 0)
	varlist = append(varlist, ctx.Token)
	for ctx.Match(",") {
		if !ctx.MatchVarname() {
			return varlist, errors.New(
				"Variable expected near " +
					ctx.Line[ctx.Cursor:])
		}
		varlist = append(varlist, ctx.Token)
	}
	return varlist, nil
}

func (ctx *Context) ParseFor() error {
	if !ctx.MatchVarname() {
		return errors.New(
			"Variable expected near " + ctx.Line[ctx.Cursor:])
	}
	var_name := ctx.Token
	if !ctx.Match("=") {
		return errors.New(
			"'=' expected, found " + ctx.Line[ctx.Cursor:])
	}
	
	init, err := ctx.ParseArithmetic()
	if err != nil { return err }
	ctx.Variables[var_name] = init
	
	if !ctx.MatchNocase("to") {
		return errors.New(
			"'to' expected, found " + ctx.Line[ctx.Cursor:])
	}

	limit, err := ctx.ParseArithmetic()
	if err != nil { return err }
	
	var step float64
	if ctx.MatchNocase("step") {
		step, err = ctx.ParseArithmetic()
		if err != nil { return err }
		if step == 0 { return errors.New("Infinite loop") }
	} else {
		step = 1
	}

	ctx.stack.PushFront(ctx.crt_line)
	ctx.stack.PushFront(limit);
	ctx.stack.PushFront(step);
	
	return nil
}

func (ctx *Context) ParseNext() error {
	if !ctx.MatchVarname() {
		return errors.New(
			"Variable expected near " + ctx.Line[ctx.Cursor:])
	}
	var_name := ctx.Token
	_, ok := ctx.Variables[var_name]
	if !ok { return errors.New("Variable not found: " + var_name) }
	
	step := ctx.stack.Front().Value.(float64)
	limit := ctx.stack.Front().Next().Value.(float64)
	ctx.Variables[var_name] += step
	
	var done bool
	if step > 0 {
		done = ctx.Variables[var_name] > limit
	} else if step < 0 {
		done = ctx.Variables[var_name] < limit
	} else {
		return errors.New("Infinite loop")
	}
	if done {
		ctx.stack.Remove(ctx.stack.Front())
		ctx.stack.Remove(ctx.stack.Front())
		ctx.stack.Remove(ctx.stack.Front())
	} else {
		ctx.crt_line = ctx.stack.Front().Next().Next().Value.(int)
	}
	return nil
}

func (ctx *Context) ParseGosub() error {
	ln, err := ctx.ParseArithmetic()
	if err != nil {
		return err
	} else if idx := IndexOf(int(ln), ctx.addr); idx > -1 {
		ctx.stack.PushFront(ctx.crt_line)
		ctx.crt_line = idx
		return nil
	} else {
		return errors.New("Line not found: " + fmt.Sprintf("%d", ln))
	}
}

func (ctx *Context) ParseReturn() error {
	if ctx.stack.Len() > 0 {
		ctx.crt_line = ctx.stack.Remove(ctx.stack.Front()).(int)
		return nil
	} else {
		return errors.New("RETURN without GOSUB.")
	}
}

func (ctx *Context) ParseLoop() error {
	if ctx.MatchNocase("while") {
		value, err := ctx.ParseExpression()
		if err != nil {
			return err
		} else if value != 0 {
			ctx.crt_line = ctx.stack.Front().Value.(int)
		} else {
			ctx.stack.Remove(ctx.stack.Front())
		}
	} else if ctx.MatchNocase("until") {
		value, err := ctx.ParseExpression()
		if err != nil {
			return err
		} else if value == 0 {
			ctx.crt_line = ctx.stack.Front().Value.(int)
		} else {
			ctx.stack.Remove(ctx.stack.Front())
		}
	} else {
		return errors.New("Condition expected near " +
			ctx.Line[ctx.Cursor:])
	}
	return nil
}

func (ctx *Context) ParseRandomize() error {
	if ctx.MatchEol() {
		rand.Seed(time.Now().UnixNano())
	} else {
		seed, err := ctx.ParseArithmetic()
		if err != nil { return err }
		rand.Seed(int64(seed))
	}
	return nil
}

func (ctx *Context) ParseExpression() (float64, error) {
	return ctx.ParseDisjunction()
}

func (ctx *Context) ParseDisjunction() (float64, error) {
	lside, err := ctx.ParseConjunction()
	if err != nil { return 0, err }
	for ctx.MatchNocase("or") {
		rside, err := ctx.ParseConjunction()
		if err != nil { return 0, err }
		lside = Bool2float(lside != 0 || rside != 0)
	}
	return lside, nil
}

func (ctx *Context) ParseConjunction() (float64, error) {
	lside, err := ctx.ParseNegation()
	if err != nil { return 0, err }
	for ctx.MatchNocase("and") {
		rside, err := ctx.ParseNegation()
		if err != nil { return 0, err }
		lside = Bool2float(lside != 0 && rside != 0)
	}
	return lside, nil
}

func (ctx *Context) ParseNegation() (float64, error) {
	if ctx.MatchNocase("not") {
		value, err := ctx.ParseComparison()
		return Bool2float(value == 0), err
	} else {
		// Leave purely arithmetic results intact
		return ctx.ParseComparison()
	}
}

func (ctx *Context) ParseComparison() (float64, error) {
	lside, err := ctx.ParseArithmetic()
	if err != nil {
		return 0, err
	} else if !ctx.MatchRelation() {
		return lside, nil
	} else {
		op := ctx.Token
		rside, err := ctx.ParseArithmetic()
		if err != nil { return 0, nil }
		switch op {
			case "<=": return Bool2float(lside <= rside), nil
			case "<": return Bool2float(lside < rside), nil
			case "=": return Bool2float(lside == rside), nil
			case "<>": return Bool2float(lside != rside), nil
			case ">": return Bool2float(lside > rside), nil
			case ">=": return Bool2float(lside >= rside), nil
			default: return 0, errors.New(
				"Unknown operator: " + op)
		}
	}
}

func Bool2float(value bool) float64 {
	if value { return -1 } else { return 0 }
}

func (ctx *Context) ParseArithmetic() (float64, error) {
	t1, err := ctx.ParseTerm()
	if err != nil { return 0, err }
	for ctx.MatchAddSub() {
		op := ctx.Token
		t2, err2 := ctx.ParseTerm()
		if err2 != nil {
			return 0, err2
		} else if (op == "+") {
			t1 += t2
		} else if (op == "-") {
			t1 -= t2
		} else {
			return 0, errors.New("Unknown operator: " + op);
		}
	}
	return t1, nil
}

func (ctx *Context) ParseTerm() (float64, error) {
	t1, err := ctx.ParsePower()
	if err != nil { return 0, err }
	for ctx.MatchMulDiv() {
		op := ctx.Token
		t2, err2 := ctx.ParsePower()
		if err2 != nil {
			return 0, err2
		} else if op == "*" {
			t1 *= t2
		} else if op == "/" {
			t1 /= t2
		} else if op == "\\" {
			t1 = math.Floor(t1 / t2)
		} else {
			return 0, errors.New("Unknown operator: " + op);
		}
	}
	return t1, nil
}

func (ctx *Context) ParsePower() (float64, error) {
	t1, err := ctx.ParseFactor()
	if err != nil {
		return 0, err
	} else if ctx.Match("^") {
		t2, err := ctx.ParsePower()
		if err != nil {
			return 0, err
		} else {
			return math.Pow(t1, t2), nil
		}
	} else {
		return t1, nil
	}
}

func (ctx *Context) ParseFactor() (float64, error) {
	var signum float64
	if ctx.Match("-") {
		signum = -1
	} else if ctx.Match("+") {
		signum = 1
	} else {
		signum = 1
	}
	
	if ctx.MatchNumber() {
		value, err := strconv.ParseFloat(ctx.Token, 64)
		return value * signum, err
	} else if ctx.MatchVarname() {
		name := ctx.Token
		if _, ok := Functions[name]; ok {
			args, err := ctx.ParseArgs()
			if err != nil { return 0, err }
			return CallBuiltin(name, args)
		} else if value, ok := ctx.Variables[name]; ok {
			return value * signum, nil
		} else {
			return 0, errors.New("Variable not found: " + name)
		}
	} else if ctx.Match("(") {
		value, err := ctx.ParseExpression()
		if err != nil {
			return 0, err
		} else if ctx.Match(")") {
			return value * signum, nil
		} else {
			return 0, errors.New(
				"Missing ')' near " + ctx.Line[ctx.Cursor:])
		}
	} else {
		return 0, errors.New(
			"Expression expected near " + ctx.Line[ctx.Cursor:])
	}
}

func (ctx *Context) ParseArgs() ([]float64, error) {
	args := make([]float64, 0, 3) // The most arguments a built-in takes.
	if (ctx.Match("(")) {
		if (ctx.Match(")")) {
			return args, nil
		}
		value, err := ctx.ParseExpression()
		if err != nil { return args, err }
		args = append(args, value)
		for ctx.Match(",") {
			value, err := ctx.ParseExpression()
			if err != nil { return args, err }
			args = append(args, value)
		}
		if ctx.Match(")") {
			return args, nil
		} else {
			return args, errors.New(
				"Missing ')' near" + ctx.Line[ctx.Cursor:])
		}
	} else {
		return args, nil
	}
}

func (ctx *Context) MatchKeyword() bool {
	if ctx.Cursor >= len(ctx.Line) || !hasLetterAt(ctx.Line, ctx.Cursor) {
		return false
	}
	mark := ctx.Cursor
	for ctx.Cursor < len(ctx.Line) && hasLetterAt(ctx.Line, ctx.Cursor) {
		ctx.Cursor++
	}
	ctx.Token = strings.ToLower(ctx.Line[mark:ctx.Cursor])
	return true
}

func (ctx *Context) MatchVarname() bool {
	ctx.SkipWhitespace()
	if ctx.Cursor >= len(ctx.Line) || !hasLetterAt(ctx.Line, ctx.Cursor) {
		return false
	}
	mark := ctx.Cursor
	for ctx.Cursor < len(ctx.Line) && hasAlnumAt(ctx.Line, ctx.Cursor) {
		ctx.Cursor++
	}
	ctx.Token = strings.ToLower(ctx.Line[mark:ctx.Cursor])
	return true
}

func (ctx *Context) MatchNumber() bool {
	ctx.SkipWhitespace()
	mark := ctx.Cursor
	ctx.SkipDigits()
	if (mark == ctx.Cursor) {
		return false
	} else if (ctx.Cursor < len(ctx.Line) && ctx.Line[ctx.Cursor] == '.') {
		ctx.Cursor++
		ctx.SkipDigits()
	}
	ctx.Token = ctx.Line[mark:ctx.Cursor]
	return true
}

func (ctx *Context) MatchEol() bool {
	ctx.SkipWhitespace()
	return ctx.Cursor >= len(ctx.Line)
}

var RelOp = [6]string{"<=", "<>", ">=", "<", "=", ">"}

func (ctx *Context) MatchRelation() bool {
	ctx.SkipWhitespace()
	for _, i := range RelOp {
		if strings.HasPrefix(ctx.Line[ctx.Cursor:], i) {
			ctx.Token = i;
			ctx.Cursor += len(i)
			return true
		}
	}
	return false
}

func (ctx *Context) MatchAddSub() bool {
	if ctx.Match("+") {
		ctx.Token = "+"
		return true
	} else if ctx.Match("-") {
		ctx.Token = "-"
		return true
	} else {
		return false
	}
}

func (ctx *Context) MatchMulDiv() bool {
	if ctx.Match("*") {
		ctx.Token = "*"
		return true
	} else if ctx.Match("/") {
		ctx.Token = "/"
		return true
	} else if ctx.Match("\\") {
		ctx.Token = "\\"
		return true
	} else {
		return false
	}
}

func (ctx *Context) Match(text string) bool {
	ctx.SkipWhitespace()
	if strings.HasPrefix(ctx.Line[ctx.Cursor:], text) {
		ctx.Cursor += len(text)
		return true
	} else {
		return false
	}
}

func (ctx *Context) MatchNocase(kw string) bool {
	mark := ctx.Cursor
	ctx.SkipWhitespace()
	if !ctx.MatchKeyword() {
		ctx.Cursor = mark
		return false
	} else if strings.ToLower(ctx.Token) != strings.ToLower(kw) {
		ctx.Cursor = mark
		return false
	} else {
		return true
	}
}

func (ctx *Context) SkipWhitespace() {
	for ctx.Cursor < len(ctx.Line) && hasSpaceAt(ctx.Line, ctx.Cursor) {
		ctx.Cursor++
	}
}

func (ctx *Context) SkipDigits() {
	for ctx.Cursor < len(ctx.Line) && hasDigitAt(ctx.Line, ctx.Cursor) {
		ctx.Cursor++
	}
}

func hasLetterAt(text string, index int) bool {
	return unicode.IsLetter(rune(text[index]))
}

func hasAlnumAt(text string, index int) bool {
	return unicode.IsLetter(rune(text[index])) ||
		unicode.IsDigit(rune(text[index]))
}

func hasDigitAt(text string, index int) bool {
	return unicode.IsDigit(rune(text[index]))
}

func hasSpaceAt(text string, index int) bool {
	return unicode.IsSpace(rune(text[index]))
}

func IndexOf(needle int, haystack []int) int {
	for i, num := range haystack {
		if num == needle { return i }
	}
	return -1
}

func (ctx *Context) RunProgram() error {
	ctx.stack.Init()
	ctx.addr = ctx.Program.LineNumbers()
	ctx.crt_line = 0
	return ctx.ContinueProgram()
}

func (ctx *Context) ContinueProgram() error {
	var err error
	ctx.stop = false
	for ctx.crt_line < len(ctx.addr) && !ctx.stop {
		ctx.line_num = ctx.addr[ctx.crt_line]
		ctx.Line = ctx.Program[ctx.line_num]
		ctx.crt_line++
		ctx.Cursor = 0
		err = ctx.ParseStatement()
		if err != nil {
			fmt.Fprint(Errs, err);
			fmt.Fprint(Errs, " in line ", ctx.line_num);
			fmt.Fprintln(Errs, ", column ", ctx.Cursor);
			break
		}
	}
	return err
}

func (ctx *Context) Stopped() bool { return ctx.stop }

func (ctx *Context) LoadFile(fn string) error {
	file, err := os.Open(fn)
	if err != nil { return err }
	defer file.Close()
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		ctx.Line = scanner.Text()
		ctx.Cursor = 0
		err = ctx.ParseLine()
		if err != nil { return err }
	}
	return scanner.Err()
}

func (ctx *Context) SaveFile(fn string) error {
	file, err := os.Create(fn)
	if err != nil { return err }
	defer file.Close()
	fmt.Fprintln(Errs, "Opening file: " + fn)
	for _, i := range ctx.Program.LineNumbers() {
		_, err = fmt.Fprintf(file, "%d\t%s\n", i, ctx.Program[i])
		if (err != nil) { return err }
	}
	return nil
}

func (ctx *Context) CommandLoop(banner string) {
	fmt.Fprintln(Outs, banner);
	fmt.Fprint(Outs, "> ")
	scanner := bufio.NewScanner(Ins)
	for scanner.Scan() {
		ctx.Line = scanner.Text()
		if len(ctx.Line) == 0 { fmt.Fprint(Outs, "> "); continue }
		ctx.Cursor = 0
		var err error
		
		if hasDigitAt(ctx.Line, 0) {
			err = ctx.ParseLine()
		} else if !ctx.MatchKeyword() {
			err = errors.New("Command expected")
		} else if ctx.Token == "bye" {
			break
		} else if ctx.Token == "list" {
			for _, i := range ctx.Program.LineNumbers() {
				fmt.Fprintf(Outs, "%d\t%s\n", i, ctx.Program[i])
			}
		} else if ctx.Token == "run" {
			ctx.RunProgram()
		} else if ctx.Token == "continue" {
			ctx.ContinueProgram()
		} else if ctx.Token == "clear" {
			ctx.Variables = make(Variables)
		} else if ctx.Token == "new" {
			ctx.Program = make(Program)
		} else if ctx.Token == "delete" {
			if ctx.MatchNumber() {
				ln, _ := strconv.Atoi(ctx.Token)
				delete(ctx.Program, ln)
			} else {
				err = errors.New("Line # expected")
			}
		} else if ctx.Token == "load" {
			if ok, err := ctx.MatchedString(); ok {
				err = ctx.LoadFile(ctx.Token)
				if err == nil {
					fmt.Fprintln(Outs, "File loaded.")
				} else {
					fmt.Fprintln(Errs, err)
				}
			} else if err == nil {
				fmt.Fprintln(Errs, "String expected.")
			} else {
				fmt.Fprintln(Errs, err)
			}
		} else if ctx.Token == "save" {
			if ok, err := ctx.MatchedString(); ok {
				err = ctx.SaveFile(ctx.Token)
				if err == nil {
					fmt.Fprintln(Outs, "File saved.")
				} else {
					fmt.Fprintln(Errs, err)
				}
			} else if err == nil {
				fmt.Fprintln(Errs, "String expected.")
			} else {
				fmt.Fprintln(Errs, err)
			}
		} else {
			err = ctx.DispatchStatement()
		}
		if err != nil { fmt.Fprintln(Errs, err) }
		fmt.Fprint(Outs, "> ")
	}
	if err := scanner.Err(); err != nil {
		fmt.Fprintln(Errs, "Error on input: ", err)
	}
}

func main() {
	basic := Context{Variables: make(Variables), Program: make(Program)}
	
	if len(os.Args) > 1 {
		for _, i := range os.Args[1:] {
			err := basic.LoadFile(i)
			if err != nil { fmt.Fprintln(Errs, err); return }
		}
		basic.RunProgram()
		if !basic.stop { return }
	}

	basic.CommandLoop("Tinycat BASIC v1.0 READY\nType BYE to quit.")
}
