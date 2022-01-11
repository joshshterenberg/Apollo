from errors import *
from nodes import *
import constants

### parse results ###

class ParseResult:
	def __init__(self):
		self.error = None
		self.node = None
		self.last_registered_advance_count = 0
		self.advance_count = 0

	def register(self, res):
		self.last_registered_advance_count = res.advance_count
		self.advance_count += res.advance_count
		if res.error: self.error = res.error
		return res.node

	def register_advancement(self):
		self.last_registered_advance_count = 1
		self.advance_count += 1

	def success(self, node):
		self.node = node
		return self

	def failure(self, error):
		if not self.error or self.last_registered_advance_count == 0:
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
				"Expected '+', '-', '*', '/', '^', '==', '!=', '<', '>', <=', '>=', 'AND' or 'OR'"
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
		elif tok.matches(constants.TT_KEYWORD, 'IF'):
			if_expr = res.register(self.if_expr())
			if res.error: return res
			return res.success(if_expr)
		elif tok.matches(constants.TT_KEYWORD, 'FOR'):
			for_expr = res.register(self.for_expr())
			if res.error: return res
			return res.success(for_expr)
		elif tok.matches(constants.TT_KEYWORD, 'WHILE'):
			while_expr = res.register(self.while_expr())
			if res.error: return res
			return res.success(while_expr)
		elif tok.matches(constants.TT_KEYWORD, 'FUN'):
			func_def = res.register(self.func_def())
			if res.error: return res
			return res.success(func_def)
		return res.failure(InvalidSyntaxError(
			tok.pos_start, tok.pos_end,
			"Expected int, float, identifier, '+', '-', '(', 'IF', 'FOR', 'WHILE', 'FUN'"
		))

	def call(self):
		res = ParseResult()
		atom = res.register(self.atom())
		if res.error: return res
		if self.current_tok.type == constants.TT_LPAREN:
			res.register_advancement()
			self.advance()
			arg_nodes = []
			if self.current_tok.type == constants.TT_RPAREN:
				res.register_advancement()
				self.advance()
			else:
				arg_nodes.append(res.register(self.expr()))
				if res.error:
					return res.failure(InvalidSyntaxError(
						self.current_tok.pos_start, self.current_tok.pos_end,
						"Expected ')', 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(' or 'NOT'"
					))
				while self.current_tok.type == constants.TT_COMMA:
					res.register_advancement()
					self.advance()
					arg_nodes.append(res.register(self.expr()))
					if res.error: return res
				if self.current_tok.type != constants.TT_RPAREN:
					return res.failure(InvalidSyntaxError(
						self.current_tok.pos_start, self.current_tok.pos_end,
						f"Expected ',' or ')'"
					))
				res.register_advancement()
				self.advance()
			return res.success(CallNode(atom, arg_nodes))
		return res.success(atom)

	def power(self):
		return self.bin_op(self.call, (constants.TT_POW, ), self.factor)

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

	def arith_expr(self):
		return self.bin_op(self.term, (constants.TT_PLUS, constants.TT_MINUS))

	def comp_expr(self):
		res = ParseResult()
		if self.current_tok.matches(constants.TT_KEYWORD, 'NOT'):
			op_tok = self.current_tok
			res.register_advancement()
			self.advance()
			node = res.register(self.comp_expr())
			if res.error: return res
			return res.success(UnaryOpNode(op_tok, node))
		node = res.register(self.bin_op(self.arith_expr, (constants.TT_EE, constants.TT_NE, constants.TT_LT, constants.TT_GT, constants.TT_LTE, constants.TT_GTE)))
		if res.error:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				"Expected int, float, identifier, '+', '-', '(' or 'NOT'"
			))
		return res.success(node)

	def expr(self):
		res = ParseResult()
		if self.current_tok.matches(constants.TT_KEYWORD, 'VAR'):
			res.register_advancement()
			self.advance()
			if self.current_tok.type != constants.TT_IDENTIFIER:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					"Expected identifier"
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
		node = res.register(self.bin_op(self.comp_expr, ((constants.TT_KEYWORD, 'AND'), (constants.TT_KEYWORD, 'OR'))))
		if res.error:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				"Expected 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(' or 'NOT'"
			))
		return res.success(node)

	def bin_op(self, func_a, ops, func_b=None):
		if func_b == None: func_b = func_a
		res = ParseResult()
		left = res.register(func_a())
		if res.error: return res
		while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
			op_tok = self.current_tok
			res.register_advancement()
			self.advance()
			right = res.register(func_b())
			if res.error: return res
			left = BinOpNode(left, op_tok, right)
		return res.success(left)

	def if_expr(self):
		res = ParseResult()
		cases = []
		else_case = None
		if not self.current_tok.matches(constants.TT_KEYWORD, 'IF'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'IF'"
			))
		while True:
			res.register_advancement()
			self.advance()
			condition = res.register(self.expr())
			if res.error: return res
			if not self.current_tok.matches(constants.TT_KEYWORD, 'THEN'):
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Expected 'THEN'"
				))
			res.register_advancement()
			self.advance()
			expr = res.register(self.expr())
			if res.error: return res
			cases.append((condition, expr))

			if not self.current_tok.matches(constants.TT_KEYWORD, 'ELIF'): break
		if self.current_tok.matches(constants.TT_KEYWORD, 'ELSE'):
			res.register_advancement()
			self.advance()
			else_case = res.register(self.expr())
			if res.error: return res
		return res.success(IfNode(cases, else_case))

	def for_expr(self):
		res = ParseResult()
		if not self.current_tok.matches(constants.TT_KEYWORD, 'FOR'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'FOR'"
			))
		res.register_advancement()
		self.advance()
		if self.current_tok.type != constants.TT_IDENTIFIER:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected Identifier"
			))
		var_name = self.current_tok
		res.register_advancement()
		self.advance()
		if self.current_tok.type != constants.TT_EQ:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected '='"
			))
		res.register_advancement()
		self.advance()
		start_value = res.register(self.expr())
		if res.error: return res
		if not self.current_tok.matches(constants.TT_KEYWORD, 'TO'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'TO'"
			))
		res.register_advancement()
		self.advance()
		end_value = res.register(self.expr())
		if res.error: return res
		if self.current_tok.matches(constants.TT_KEYWORD, 'STEP'):
			res.register_advancement()
			self.advance()
			step_value = res.register(self.expr())
			if res.error: return res
		else: step_value = None
		if not self.current_tok.matches(constants.TT_KEYWORD, 'THEN'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'THEN'"
			))
		res.register_advancement()
		self.advance()
		body = res.register(self.expr())
		if res.error: return res
		return res.success(ForNode(var_name, start_value, end_value, step_value, body))

	def while_expr(self):
		res = ParseResult()
		if not self.current_tok.matches(constants.TT_KEYWORD, 'WHILE'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'WHILE'"
			))
		res.register_advancement()
		self.advance()
		condition = res.register(self.expr())
		if res.error: return res
		if not self.current_tok.matches(constants.TT_KEYWORD, 'THEN'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'THEN'"
			))
		res.register_advancement()
		self.advance()
		body = res.register(self.expr())
		if res.error: return res
		return res.success(WhileNode(condition, body))

	def func_def(self):
		res = ParseResult()
		if not self.current_tok.matches(constants.TT_KEYWORD, 'FUN'):
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected 'FUN'"
			))
		res.register_advancement()
		self.advance()
		if self.current_tok.type == constants.TT_IDENTIFIER:
			var_name_tok = self.current_tok
			res.register_advancement()
			self.advance()
			if self.current_tok.type != constants.TT_LPAREN:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Expected '('"
				))
		else:
			var_name_tok = None
			if self.current_tok.type != constants.TT_LPAREN:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Expected identifier or '('"
				))
		res.register_advancement()
		self.advance()
		arg_name_toks = []
		if self.current_tok.type == constants.TT_IDENTIFIER:
			arg_name_toks.append(self.current_tok)
			res.register_advancement()
			self.advance()
			while self.current_tok.type == constants.TT_COMMA:
				res.register_advancement()
				self.advance()
				if self.current_tok.type != constants.TT_IDENTIFIER:
					return res.failure(InvalidSyntaxError(
						self.current_tok.pos_start, self.current_tok.pos_end,
						f"Expected identifier"
					))
				arg_name_toks.append(self.current_tok)
				res.register_advancement()
				self.advance()
			if self.current_tok.type != constants.TT_RPAREN:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Expected ',' or ')'"
				))
		else:
			if self.current_tok.type != constants.TT_RPAREN:
				return res.failure(InvalidSyntaxError(
					self.current_tok.pos_start, self.current_tok.pos_end,
					f"Expected identifier or ')'"
				))
		res.register_advancement()
		self.advance()
		if self.current_tok.type != constants.TT_ARROW:
			return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				f"Expected '->'"
			))
		res.register_advancement()
		self.advance()
		node_to_return = res.register(self.expr())
		if res.error: return res
		return res.success(FuncDefNode(
			var_name_tok,
			arg_name_toks,
			node_to_return
		))
