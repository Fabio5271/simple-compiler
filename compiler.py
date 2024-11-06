import re
from sys import exit

class Lexer:
    def __init__(self, code):
        self.code = code
        self.tokens = []
        self.token_specification = [
            ('LINE_NR', r'\d+'),
            ('KW_INPUT', r'input'),
            ('KW_LET', r'let'),
            ('KW_PRINT', r'print'),
            ('KW_GOTO', r'goto'),
            ('KW_IF', r'if'),
            ('KW_END', r'end'),
            ('COMMENT', r'rem.*'),
            ('WTSPACE', r'\s+'),  # Pular whitespace e comentários, tem que estar antes de identifier
            ('IDENTIFIER', r'[a-z]'), # Tem que estar depois de tokens multi caractere
            ('NUMBER', r'-?\d+'),
            ('OPERATOR', r'[+\-*/%]'),
            ('COMPARISON', r'>=|>|<=|<|==|!='), # Tem que estar antes de assign p/ ser avaliado corretamente
            ('ASSIGN', r'='), # Tem que estar depois de comparison p/ não interferir em sua avaliação
        ]

    def tokenize(self):
        line_nr = 1
        for linebuf in self.code.splitlines():
            tk_pos = 0
            while linebuf:
                try:
                    match = None
                    for token_type, pattern in self.token_specification:
                        regex = re.compile(pattern)
                        match = regex.match(linebuf)
                        if match:
                            if token_type:
                                if token_type == 'COMMENT': # Remover linhas de comentário
                                    self.tokens.append((token_type, 'COMMENT'))
                                    linebuf = linebuf[match.end():]
                                    break
                                if token_type == 'WTSPACE': # Pular tokens SKIP
                                    linebuf = linebuf[match.end():]
                                    break
                                if tk_pos != 0 and token_type == 'LINE_NR': # Token só será LINE_NR se estiver no começo da linha
                                    continue
                                token_value = match.group(0)
                                if token_type == 'LINE_NR': # Atualizar line_nr para as mensagens de erro
                                    line_nr = token_value
                                    # print() # Debug
                                self.tokens.append((token_type, token_value))
                                # print(f"({token_type}, {token_value})") # Debug
                            linebuf = linebuf[match.end():] # Remove tudo antes do fim do match do buffer
                            break
                    if not match:
                        errmsg = f'Token inválido: \'{linebuf[0]}\', linha {line_nr}'
                        raise SyntaxError(errmsg)
                    tk_pos += 1
                except SyntaxError as synerr:
                    print(f"\n***Erro***: Lexer: {synerr}\n")
                    linebuf = linebuf[1:] # Remove o caracter atual do buffer
        return self.tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token = None
        self.next_token()
        self.current_line = 1

    def next_token(self):
        if len(self.tokens) > 0:
            self.current_token = self.tokens.pop(0)
        else:
            self.current_token = ('EOF', 'EOF')

    def parse_program(self):
        while self.current_token[0] != 'EOF' and self.current_token[0] != 'KW_END':
            try:
                self.parse_keyword()
            except SyntaxError as synerr:
                print(f"\n***Erro***: Parser: {synerr}\n")
                self.next_token()
        try:
            if self.current_token[0] == 'EOF': 
                raise SyntaxError(f"\"end\" esperado após linha: {self.current_line}")
        except SyntaxError as synerr:
            print(f"\n***Erro***: Parser: {synerr}\n")


    def parse_keyword(self):
        if self.current_token[0] == 'LINE_NR':
            self.current_line = int(self.current_token[1])
            self.next_token()
            if self.current_token[0] == 'KW_INPUT':
                self.parse_input()
            elif self.current_token[0] == 'KW_LET':
                self.parse_assign()
            elif self.current_token[0] == 'KW_PRINT':
                self.parse_print()
            elif self.current_token[0] == 'KW_IF':
                self.parse_cond()
            elif self.current_token[0] == 'KW_GOTO':
                self.parse_goto()
            elif self.current_token[0] == 'COMMENT':
                self.next_token()
                return
            elif self.current_token[0] == 'LINE_NR':
                return
            elif self.current_token[0] == 'KW_END':
                return
            elif self.current_token[0] == 'EOF':
                raise SyntaxError(f"\"end\" esperado após linha: {self.current_line}")
            else:
                raise SyntaxError(f"Token inesperado: '{self.current_token}', linha: {self.current_line}")
        else:
            raise SyntaxError(f"Token inesperado: '{self.current_token}', linha: {self.current_line}")

    def parse_input(self):
        self.next_token()
        if self.current_token[0] == 'IDENTIFIER':
            self.next_token()
        else:
            raise SyntaxError(f"Identificador esperado após input ou let, linha: {self.current_line}")

    def parse_assign(self):
        self.parse_input()
        if self.current_token[0] == 'ASSIGN':
            self.next_token()
            self.parse_expr()

    def parse_print(self):
        self.next_token()
        if self.current_token[0] == 'IDENTIFIER':
            self.next_token()
        else:
            raise SyntaxError(f"Identificador esperado após 'print', linha: {self.current_line}")

    def parse_cond(self):
        self.next_token()
        self.parse_expr()
        if self.current_token[0] == 'COMPARISON':
            self.next_token()
            self.parse_expr()
            if self.current_token[0] == 'KW_GOTO':
                self.parse_goto()
            else:
                raise SyntaxError(f"'goto' esperado após condicional, linha: {self.current_line}, token: {self.current_token}")
        else:
            raise SyntaxError(f"Operador de comparação esperado (>, >=, <, <=, ==, !=), linha: {self.current_line}, token: {self.current_token}")

    def parse_goto(self):
        self.next_token()
        if self.current_token[0] == 'NUMBER':
            self.next_token()
        else:
            raise SyntaxError(f"Número da linha esperado após 'goto', linha: {self.current_line}")

    def parse_expr(self):
        self.parse_factor()
        if self.current_token[0] == 'OPERATOR':
            self.next_token()
            self.parse_factor()

    def parse_factor(self):
        if self.current_token[0] in ['IDENTIFIER', 'NUMBER']:
            self.next_token()
        else:
            raise SyntaxError(f"Identificador ou número esperado, linha: {self.current_line}, token: {self.current_token}")


class SemanticAnalyzer:
    def __init__(self, tokens):
        self.current_line = None
        self.last_line = 1 # Última linha analisada
        self.valid_lines = [] # Armazena todas as linhas válidas
        self.read_lines = [] # Armazena todas as linhas já lidas
        self.tokens = tokens
        self.current_token = None
        self.symbol_table = []

    def collect_valid_lines(self):
        # Recolhe todas as linhas válidas
        for token in self.tokens:
            if token[0] == 'LINE_NR':
                self.valid_lines.append(int(token[1]))

    def next_token(self):
        if len(self.tokens) > 0:
            self.current_token = self.tokens.pop(0)
        else:
            self.current_token = ('EOF', 'EOF')

    def analyze_program(self):
        self.collect_valid_lines() # Coletar todas as linhas válidas antes da análise
        self.next_token()
        while self.current_token[0] != 'EOF' and self.current_token[0] != 'KW_END':
            try:
                if self.current_token[0] == 'LINE_NR':
                    self.current_line = int(self.current_token[1])
                    if self.current_line < self.last_line: 
                        print(f"\n***Erro***: SemanticAnalyzer: Número de linha fora de ordem: {self.current_line}")
                    try:
                        if self.current_line in self.read_lines:
                            raise RuntimeError(f"Linha Duplicada: {self.current_line}")
                    except RuntimeError as semerr:
                        print(f"\n***Erro***: SemanticAnalyzer: {semerr}\n")
                    self.read_lines.append(self.current_line)
                    self.next_token()
                    self.analyze_keyword()
                    self.last_line = self.current_line
                    
                else:
                    self.next_token()
            except RuntimeError as semerr:
                print(f"\n***Erro***: SemanticAnalyzer: {semerr}\n")

    def analyze_keyword(self):
        if self.current_token[0] == 'KW_INPUT':
            self.analyze_input()
        elif self.current_token[0] == 'KW_LET':
            self.analyze_let()
        elif self.current_token[0] == 'KW_PRINT':
            self.analyze_print()
        elif self.current_token[0] == 'KW_IF':
            self.analyze_if()
        elif self.current_token[0] == 'KW_GOTO':
            self.analyze_goto()
        elif self.current_token[0] == 'COMMENT':
            self.next_token()
            return
        elif self.current_token[0] == 'LINE_NR':
            return
        elif self.current_token[0] == 'KW_END':
            return
        else:
            raise RuntimeError(f"Token inesperado '{self.current_token}', linha {self.current_line}")

    def analyze_input(self):
        self.next_token()
        if self.current_token[0] == 'IDENTIFIER':
            var_name = self.current_token[1]
            if var_name not in self.symbol_table:
                self.symbol_table.append(var_name)
            self.next_token()
        else:
            raise RuntimeError(f"Identificador esperado após 'input', linha {self.current_line}")

    def analyze_let(self):
        self.next_token()
        if self.current_token[0] == 'IDENTIFIER':
            var_name = self.current_token[1]
            if var_name not in self.symbol_table:
                self.symbol_table.append(var_name)
            self.next_token()
            if self.current_token[0] == 'ASSIGN':
                self.next_token()
                self.analyze_expr()
            else:
                raise RuntimeError(f"'=' esperado após identificador, linha {self.current_line}")
        else:
            raise RuntimeError(f"Identificador esperado após 'let', linha {self.current_line}")

    def analyze_print(self):
        self.next_token()
        if self.current_token[0] == 'IDENTIFIER':
            var_name = self.current_token[1]
            if var_name not in self.symbol_table:
                raise RuntimeError(f"Variável '{var_name}' não inicializada, linha {self.current_line}")
            self.next_token()
        else:
            raise RuntimeError(f"Identificador esperado após 'print', linha {self.current_line}")

    def analyze_if(self):
        self.next_token()
        self.analyze_expr()
        if self.current_token[0] == 'COMPARISON':
            self.next_token()
            self.analyze_expr()
            if self.current_token[0] == 'KW_GOTO':
                self.analyze_goto()
            else:
                raise RuntimeError(f"'Goto' esperado após expressão condicional, linha {self.current_line}")
        else:
            raise RuntimeError(f"Operador de comparação esperado após expressão, linha {self.current_line}")

    def analyze_goto(self):
        self.next_token()
        if self.current_token[0] != 'NUMBER':
            raise RuntimeError(f"Número esperado após 'goto', linha {self.current_line}")
        line_number = int(self.current_token[1])
        if line_number <= 0:
            raise RuntimeError(f"Número da linha inválido após 'goto', linha {self.current_line}")
        if line_number not in self.valid_lines: # Verifica se o número da linha existe
            print(self.valid_lines)
            raise RuntimeError(f"Linha {line_number} não existe, linha {self.current_line}")
        self.next_token()

    def analyze_expr(self):
        if self.current_token[0] == 'IDENTIFIER':
            self.check_initialized(self.current_token[1])
            self.next_token()
            self.analyze_op()
        elif self.current_token[0] == 'NUMBER':
            self.next_token()
            self.analyze_op()
        else:
            raise RuntimeError(f"Identificador ou número esperado, linha {self.current_line}")

    def check_initialized(self, var_name): # Deve ser usada só com variáveis ('IDENTIFIER's), passando o nome (self.current_token[1])
        if var_name not in self.symbol_table:
            raise RuntimeError(f"Variável '{var_name}' não inicializada, linha {self.current_line}")

    def analyze_op(self):
        if self.current_token[0] == 'OPERATOR':
            if self.current_token[1] == '/':
                self.next_token()
                if self.current_token[0] == 'IDENTIFIER':
                    self.check_initialized(self.current_token[1])
                    self.next_token()
                elif self.current_token[0] == 'NUMBER':
                    if self.current_token[1] == '0':
                        raise RuntimeError(f"Divisão por zero, linha {self.current_line}")
                    self.next_token()
                else:
                    raise RuntimeError(f"Identificador ou número esperado, linha {self.current_line}")
            else:
                self.next_token()
                if self.current_token[0] == 'IDENTIFIER':
                    self.check_initialized(self.current_token[1])
                    self.next_token()
                elif self.current_token[0] == 'NUMBER':
                    self.next_token()
                else:
                    raise RuntimeError(f"Identificador ou número esperado, linha {self.current_line}")


class CodeGen:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token = None
        self.code = []
        self.var_lines = {} # Dict de linhas das variáveis



# Exemplo de uso
code = """
05 rem erro sintatico na linha 75
10 input n
15 if n > 0 goto 30
20 let m = -1
25 goto 70
30 let s = 0
35 let i = 1
40 if i > n goto 65
45 let a = 2 * i
50 let s = s + a
55 let i = i + 1
60 goto 40
65 let m = s / n
70 print m
75 end
"""

lexer = Lexer(code)
tokens = lexer.tokenize()
# print('\nTokens gerados!\n')

parser = Parser(tokens[:])
parser.parse_program()
# print("\nAnálise sintática concluída!\n")

semantic_analyzer = SemanticAnalyzer(tokens[:])
semantic_analyzer.analyze_program()
# print("\nAnálise semântica concluída!\n")

print(tokens)

# code_gen = CodeGen(tokens)


print("\nAnálise concluída!\n")
