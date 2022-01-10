from errors import *
from position import *
from lexing import *
from parsing import *
from interpretation import *

global_symbol_table = SymbolTable()
global_symbol_table.set("null", Number(0))

def run(fn, text): # go go go
	# lex
	lexer = Lexer(fn, text)
	tokens, error = lexer.make_tokens()
	if error: return None, error

	# parse
	parser = Parser(tokens)
	ast = parser.parse()
	if ast.error: return None, ast.error

	# interpret
	interpreter = Interpreter()
	context = Context('<program>')
	context.symbol_table = global_symbol_table
	result = interpreter.visit(ast.node, context)

	return result.value, result.error
