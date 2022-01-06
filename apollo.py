from errors import *
from position import *
from token import *
from lexing import *
from parsing import *
from interpretation import *

DIGITS = '0123456789'
TT_INT = 'INT'
TT_FLOAT = 'FLOAT'
TT_PLUS = 'PLUS'
TT_MINUS = 'MINUS'
TT_MUL = 'MUL'
TT_DIV = 'DIV'
TT_LPAREN = 'LPAREN'
TT_RPAREN = 'RPAREN'
TT_EOF = 'EOF'

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
	interpreter.visit(ast.node)

	return result, None
