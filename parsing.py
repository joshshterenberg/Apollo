from errors import *
import string
import constants

### nodes ###
# all for the hierarchical tree to exec commands
class NumberNode:
	def __init__(self, tok):
		self.tok = tok
		self.pos_start = self.tok.pos_start
		self.pos_end = self.tok.pos_end
	def __repr__(self):
		return f'{self.tok}'

class VarAccessNode:
	def __init__(self, var_name_tok):
		self.var_name_tok = var_name_tok
		self.pos_start = self.var_name_tok.pos_start
		self.pos_end = self.var_name_tok.pos_end

class VarAssignNode:
	def __init__(self, var_name_tok, value_node):
		self.var_name_tok = var_name_tok
		self.value_node = value_node
		self.pos_start = self.var_name_tok.pos_start
		self.pos_end = self.value_node.pos_end

class BinOpNode: # for 2 operands: +, -, etc. 2 leaf tree
	def __init__(self, left_node, op_tok, right_node):
		self.left_node = left_node
		self.op_tok = op_tok
		self.right_node = right_node
		self.pos_start = self.left_node.pos_start
		self.pos_end = self.right_node.pos_end

	def __repr__(self):
		return f'({self.left_node}, {self.op_tok}, {self.right_node})'

class UnaryOpNode: # for 1 operand, !, %, etc. 1 leaf tree
	def __init__(self, op_tok, node):
		self.op_tok = op_tok
		self.node = node
		self.pos_start = self.op_tok.pos_start
		self.pos_end = node.pos_end

	def __repr__(self):
		return f'({self.op_tok}, {self.node})'

### parse results ###

class ParseResult: # class to help with node errors and like
	def __init__(self):
		self.error = None
		self.node = None
		self.advance_count = 0

	def register(self, res):
		self.advance_count += res.advance_count
		if res.error: self.error = res.error
		return res.node

	def register_advancement(self):
		self.advance_count += 1

	def success(self, node):
		self.node = node
		return self

	def failure(self, error):
		if not self.error or self.advance_count == 0:
			self.error = error
		return self

### parser ###

class Parser:
	def __init__(self, tokens):
		self.tokens = tokens
		self.tok_idx = -1
		self.advance()

	def advance(self):
		self.tok_idx += 1
		if self.tok_idx < len(self.tokens):
			self.current_tok = self.tokens[self.tok_idx]
		return self.current_tok # return value if exists

	def parse(self):
		res = self.expr() # get expression as a function of terms as a function of factors
		if not res.error and self.current_tok.type != constants.TT_EOF:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				"Expected '+', '-', '*', or '/'"
			))
		return res

	def atom(self):
		res = ParseResult()
		tok = self.current_tok
		if tok.type in (constants.TT_INT, constants.TT_FLOAT):
			res.register_advancement()
			self.advance()
			return res.success(NumberNode(tok))
		elif tok.type == constants.TT_IDENTIFIER:
			res.register_advancement()
			self.advance()
			return res.success(VarAccessNode(tok))
		elif tok.type == constants.TT_LPAREN:
			res.register_advancement()
			self.advance()
			expr = res.register(self.expr())
			if res.error: return res
			if self.current_tok.type == constants.TT_RPAREN:
				res.register_advancement()
				self.advance()
				return res.success(expr)
			else:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected ')'"
				))
		return res.failure(InvalidSyntaxError(
			tok.pos_start, tok.pos_end,
			"Expected int, float, identifier, '+', '-' or '('"
		))

	def power(self):
		return self.bin_op(self.atom, (constants.TT_POW, ), self.factor)

	def factor(self):
		res = ParseResult()
		tok = self.current_tok
		if tok.type in (constants.TT_PLUS, constants.TT_MINUS):
			res.register_advancement()
			self.advance()
			factor = res.register(self.factor())
			if res.error: return res
			return res.success(UnaryOpNode(tok, factor))
		return self.power()

	def term(self):
		return self.bin_op(self.factor, (constants.TT_MUL, constants.TT_DIV))

	def expr(self):
		res = ParseResult()
		if self.current_tok.matches(constants.TT_KEYWORD, 'VAR'):
			res.register_advancement()
			self.advance()
			if self.current_tok.type != constants.TT_IDENTIFIER:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected Identifier"
				))
			var_name = self.current_tok
			res.register_advancement()
			self.advance()
			if self.current_tok.type != constants.TT_EQ:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected '='"
				))
			res.register_advancement()
			self.advance()
			expr = res.register(self.expr())
			if res.error: return res
			return res.success(VarAssignNode(var_name, expr))
		node = res.register(self.bin_op(self.term, (constants.TT_PLUS, constants.TT_MINUS)))
		if res.error: return res.failure(InvalidSyntaxError(
			self.current_tok.pos_start, self.current_tok.pos_end,
			"Expected 'VAR', int, float, identifier, '+', '-', or '('"
		))
		return res.success(node)

	def bin_op(self, func_a, ops, func_b=None):
		if func_b == None: func_b = func_a
		res = ParseResult()
		left = res.register(func_a())
		if res.error: return res
		while self.current_tok.type in ops:
			op_tok = self.current_tok
			res.register_advancement()
			self.advance()
			right = res.register(func_b())
			if res.error: return res
			left = BinOpNode(left, op_tok, right)
		return res.success(left)
