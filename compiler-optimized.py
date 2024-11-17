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
        self.error = False

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
                                self.tokens.append((token_type, token_value))
                            linebuf = linebuf[match.end():] # Remove tudo antes do fim do match do buffer
                            break
                    if not match:
                        errmsg = f'Token inválido: \'{linebuf[0]}\', linha {line_nr}'
                        raise SyntaxError(errmsg)
                    tk_pos += 1
                except SyntaxError as synerr:
                    print(f"\n***Erro***: Lexer: {synerr}\n")
                    self.error = True
                    linebuf = linebuf[1:] # Remove o caracter atual do buffer
        return self.tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token = None
        self.next_token()
        self.current_line = 1
        self.error = False

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
                self.error = True
                self.next_token()
        try:
            if self.current_token[0] == 'EOF': 
                raise SyntaxError(f"\"end\" esperado após linha: {self.current_line}")
        except SyntaxError as synerr:
            print(f"\n***Erro***: Parser: {synerr}\n")
            self.error = True


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
        self.error = False

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
                        self.error = True
                    try:
                        if self.current_line in self.read_lines:
                            raise RuntimeError(f"Linha Duplicada: {self.current_line}")
                    except RuntimeError as semerr:
                        print(f"\n***Erro***: SemanticAnalyzer: {semerr}\n")
                        self.error = True
                    self.read_lines.append(self.current_line)
                    self.next_token()
                    self.analyze_keyword()
                    self.last_line = self.current_line
                    
                else:
                    self.next_token()
            except RuntimeError as semerr:
                print(f"\n***Erro***: SemanticAnalyzer: {semerr}\n")
                self.error = True

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
        # self.current_line = 0 # Linha atual do código SIMPLE
        self.code = []
        self.vars = {} # Dict de variáveis
        self.consts = []
        self.equiv_lines = {}
        self.var_in_accum = None

    def next_token(self):
        if len(self.tokens) > 0:
            self.current_token = self.tokens.pop(0)
        else:
            self.current_token = ('EOF', 'EOF')

    def add_var_to_list(self):
        if self.current_token[0] == 'IDENTIFIER':
            # if self.current_token[1] not in self.vars:
            self.vars[self.current_token[1]] = None

    def read_program(self):
        self.next_token()
        while self.current_token[0] != 'EOF' and self.current_token[0] != 'KW_END':
            if self.current_token[0] == 'LINE_NR':
                # self.current_line = int(self.current_token[1])
                self.equiv_lines[self.current_token[1]] = len(self.code)
                self.next_token()
                self.read_keyword()
            else:
                self.next_token()

    def read_keyword(self):
        if self.current_token[0] == 'KW_INPUT':
            self.read_input()
        elif self.current_token[0] == 'KW_LET':
            self.read_let()
        elif self.current_token[0] == 'KW_PRINT':
            self.read_print()
        # elif self.current_token[0] == 'KW_IF':
        #     self.analyze_if()
        # elif self.current_token[0] == 'KW_GOTO':
        #     self.read_goto()
        elif self.current_token[0] == 'COMMENT':
            self.next_token()
        elif self.current_token[0] == 'LINE_NR':
            return
        elif self.current_token[0] == 'KW_END':
            self.proc_end()

    def read_input(self):
        self.next_token()
        self.add_var_to_list()
        self.code.append(f'+10{self.current_token[1]}')

    def read_let(self):
        self.next_token() # var
        self.add_var_to_list()
        var = self.current_token[1]
        self.next_token() # '='
        self.next_token() # arg1
        if self.current_token[0] == 'NUMBER':
            num1 = int(self.current_token[1])
        else: # se arg1 for variável:
            arg1 = self.current_token[1]
        self.next_token() # op
        
        if self.current_token[0] != 'OPERATOR': # Se tivermos o formato 'let var = arg1':
            if 'num1' in locals(): # Se arg1 é número:
                self.vars[var] = num1
            elif 'arg1' in locals(): # Se arg1 é var:
                if self.vars[arg1] != None: # Se arg1 tem valor definido:
                    self.vars[var] = self.vars[arg1]
                else:
                    if self.var_in_accum != arg1:
                        self.code.append(f'+20{arg1}')
                        self.var_in_accum = arg1
                    self.code.append(f'+21{var}')

        else: # Se tivermos o formato 'let var = arg1 op arg2':
            op = self.current_token[1]
            self.next_token() # arg2
            if 'num1' in locals(): # Se arg1 é número:
                if self.current_token[0] == 'NUMBER': # Se arg2 é número:
                    self.vars[var] = self.calculate(num1, op, int(self.current_token[1]))
                else: # Se arg2 é var:
                    if self.vars[self.current_token[1]] != None: # Se arg2 tem valor definido:
                        self.vars[var] = self.calculate(num1, op, self.vars[self.current_token[1]])
                    else:
                        self.consts.append(int(num1))
                        self.code.append(f'+20C{len(self.consts)-1}')
                        match op:
                            case '+':
                                self.code.append(f'+30{self.current_token[1]}')
                            case '-':
                                self.code.append(f'+31{self.current_token[1]}')
                            case '*':
                                self.code.append(f'+33{self.current_token[1]}')
                            case '/':
                                self.code.append(f'+32{self.current_token[1]}')
                            case '%':
                                self.code.append(f'+34{self.current_token[1]}')
                        self.var_in_accum = None
                        self.code.append(f'+21{var}')
            elif 'arg1' in locals(): # Se arg1 é var:
                if self.vars[arg1] != None: # Se arg1 tem valor definido:
                    if self.current_token[0] == 'NUMBER': # Se arg2 é número:
                        self.vars[var] = self.calculate(self.vars[arg1], op, int(self.current_token[1]))
                    else: # Se arg2 é var:
                        if self.vars[self.current_token[1]] != None: # Se arg2 tem valor definido:
                            self.vars[var] = self.calculate(self.vars[arg1], op, self.vars[self.current_token[1]])
                        else:
                            if self.var_in_accum != arg1:
                                self.code.append(f'+20{arg1}')
                            match op:
                                case '+':
                                    self.code.append(f'+30{self.current_token[1]}')
                                case '-':
                                    self.code.append(f'+31{self.current_token[1]}')
                                case '*':
                                    self.code.append(f'+33{self.current_token[1]}')
                                case '/':
                                    self.code.append(f'+32{self.current_token[1]}')
                                case '%':
                                    self.code.append(f'+34{self.current_token[1]}')
                            self.var_in_accum = None
                            self.code.append(f'+21{var}')
                else: # se arg1 não tem valor definido:
                    if self.current_token[0] == 'NUMBER': # Se arg2 é número:
                        self.consts.append(int(self.current_token[1]))
                        if self.var_in_accum != arg1:
                            self.code.append(f'+20{arg1}')
                        match op:
                            case '+':
                                self.code.append(f'+30C{len(self.consts)-1}')
                            case '-':
                                self.code.append(f'+31C{len(self.consts)-1}')
                            case '*':
                                self.code.append(f'+33C{len(self.consts)-1}')
                            case '/':
                                self.code.append(f'+32C{len(self.consts)-1}')
                            case '%':
                                self.code.append(f'+34C{len(self.consts)-1}')
                    else:
                        if self.var_in_accum != arg1:
                            self.code.append(f'+20{arg1}')
                        match op:
                            case '+':
                                self.code.append(f'+30{self.current_token[1]}')
                            case '-':
                                self.code.append(f'+31{self.current_token[1]}')
                            case '*':
                                self.code.append(f'+33{self.current_token[1]}')
                            case '/':
                                self.code.append(f'+32{self.current_token[1]}')
                            case '%':
                                self.code.append(f'+34{self.current_token[1]}')
                    self.var_in_accum = None
                    self.code.append(f'+21{var}')


    def calculate(self, x, op, y):
        match op:
            case '+':
                return x + y
            case '-':
                return x - y
            case '*':
                return x * y
            case '/':
                return x / y
            case '%':
                return x % y


    def read_print(self):
        self.next_token()
        self.code.append(f'+11{self.current_token[1]}')

    def read_goto(self):
        self.next_token() # target line
        self.code.append(f'+40B{self.current_token[1]}')


    def proc_end(self):
        self.code.append('+4300')
        self.proc_consts()
        self.proc_vars()
    
    def proc_consts(self):
        for c_id, const in enumerate(self.consts):
            # Adicionar const após end:
            if const < 0:
                sign = '-'
            else:
                sign = '+'
            self.code.append(f'{sign}{"%0004d" % abs(const)}') # Formatar const no padrão da SML
            # Substituir menções de const pelo endereço de const:
            for l_id, line in enumerate(self.code):
                if f'C{c_id}' in line:
                    self.code[l_id] = f'{line[:3]}{"%02d" % (len(self.code) - 1)}' # Manter 3 primeiros caracteres, substituir 2 últimos por len(self.code) - 1

    def proc_vars(self):
        for var in self.vars:
            # Adicionar var após end:
            if self.vars[var] != None: # Se a var tiver um valor
                if self.vars[var] < 0:
                    sign = '-'
                else:
                    sign = '+'
                self.code.append(f'{sign}{"%0004d" % abs(self.vars[var])}')
            else:
                # self.code.append(f'+00{"%02d" % len(self.code)}')
                self.code.append('-7777')
            # Substituir menções de var pelo endereço de var:
            for l_id, line in enumerate(self.code):
                if var in line:
                    self.code[l_id] = f'{line[:3]}{"%02d" % (len(self.code) - 1)}' # Manter 3 primeiros caracteres, substituir 2 últimos por len(self.code) - 1


# ========== Código SIMPLE a ser compilado ==========:
code = """
01 let x = 70
05 let y = x
10 let z = x + y
20 let w = x + 2
25 let v = 2 - y
26 let u = 100 / 3
30 input a
35 let b = a
40 let c = 80 * a
45 let d = x % a
50 let e = a - 1
55 let f = a + y
60 let g = a * b
99 end
"""

lexer = Lexer(code)
tokens = lexer.tokenize()

parser = Parser(tokens[:])
parser.parse_program()

semantic_analyzer = SemanticAnalyzer(tokens[:])
semantic_analyzer.analyze_program()

print("\nAnálise concluída!\n")

code_gen = CodeGen(tokens[:])
code_gen.read_program()

debug = True # Flag p/ imprimir tudo de debug

if debug:
    # Debug: Listar todos os tokens
    print('***Debug***: Tokens:')
    for token in tokens:
        if token[0] == 'LINE_NR' and token != tokens[0]:
            print()
        print(token)

    # Debug: Listar consts e vars
    print('\n***Debug***: Consts:')
    for const in code_gen.consts:
        print(const)
    print('\n***Debug***: Vars:')
    print(code_gen.vars)
    print('\n***Debug***: SIMPLE Line | SML Line:')
    print(code_gen.equiv_lines)

# Conferir erros e avisar:
if (lexer.error or parser.error or semantic_analyzer.error):
    print('\n***Info***: Erros encontrados na análise!\n')
    if input('***Importante***: Tentar compilar mesmo assim? [S/n]: ') not in ['n', 'N']:
        print('Código inoperante (compilado com erros):')
        for instr in code_gen.code:
            print(instr)
    else:
        print('Abortando!')
else:
    print('\nCompilado com sucesso!\n\nCódigo:')
    for instr in code_gen.code:
        print(instr)


# print(f"test: {self.current_token}")