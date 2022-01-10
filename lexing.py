from position import *
from errors import *
import constants

class Token:
	def __init__(self,type_,value=None, pos_start=None, pos_end=None):
		self.type = type_
		self.value = value
		if pos_start:
			self.pos_start = pos_start.copy()
			self.pos_end = pos_start.copy()
			self.pos_end.advance()
		if pos_end:
			self.pos_end = pos_end
	def matches(self, type_, value):
		return self.type == type_ and self.value == value
	def __repr__(self): # for nice printing
		if self.value: return f'{self.type}:{self.value}'
		return f'{self.type}'

### lexer ###

class Lexer:
	def __init__(self, fn, text):
		self.fn = fn
		self.text = text
		self.pos = Position(-1,0,-1, fn, text) # beginning
		self.current_char = None
		self.advance()

	def advance(self): # move if ! end
		self.pos.advance(self.current_char)
		self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

	def make_tokens(self): # make list, ignore spaces
		tokens = []
		while self.current_char != None:
			if self.current_char in ' \t':
				self.advance()
			elif self.current_char in constants.DIGITS:
				tokens.append(self.make_number())
			elif self.current_char in constants.LETTERS:
				tokens.append(self.make_identifier())
			elif self.current_char == "+":
				tokens.append(Token(constants.TT_PLUS, pos_start = self.pos))
				self.advance()
			elif self.current_char == "-":
				tokens.append(Token(constants.TT_MINUS, pos_start = self.pos))
				self.advance()
			elif self.current_char == "*":
				tokens.append(Token(constants.TT_MUL, pos_start = self.pos))
				self.advance()
			elif self.current_char == "/":
				tokens.append(Token(constants.TT_DIV, pos_start = self.pos))
				self.advance()
			elif self.current_char == "^":
				tokens.append(Token(constants.TT_POW, pos_start = self.pos))
				self.advance()
			elif self.current_char == "=":
				tokens.append(Token(constants.TT_EQ, pos_start = self.pos))
				self.advance()
			elif self.current_char == "(":
				tokens.append(Token(constants.TT_LPAREN, pos_start = self.pos))
				self.advance()
			elif self.current_char == ")":
				tokens.append(Token(constants.TT_RPAREN, pos_start = self.pos))
				self.advance()
			else: # bad character
				pos_start = self.pos.copy()
				char = self.current_char
				self.advance()
				return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")
		tokens.append(Token(constants.TT_EOF, pos_start = self.pos))
		return tokens, None

	def make_number(self): # more than one digit / float
		num_str = ''
		dot_count = 0
		pos_start = self.pos.copy()
		while self.current_char != None and self.current_char in constants.DIGITS + '.':
			if self.current_char == '.':
				if dot_count == 1: break
				dot_count += 1
				num_str += '.'
			else:
				num_str += self.current_char
			self.advance()
		if dot_count == 0:
			return Token(constants.TT_INT, int(num_str), pos_start, self.pos)
		else:
			return Token(constants.TT_FLOAT, float(num_str), pos_start, self.pos)

	def make_identifier(self):
		id_str = ''
		pos_start = self.pos.copy()
		while self.current_char != None and self.current_char in constants.LETTERS_DIGITS + '_':
			id_str += self.current_char
			self.advance()
		tok_type = constants.TT_KEYWORD if id_str in constants.KEYWORDS else constants.TT_IDENTIFIER
		return Token(tok_type, id_str, pos_start, self.pos)
