"""
tingu is an interpreter that understands an small subset of LISP, based on
Michael Nielsen's interpretation of Peter Norvig's beautiful LISP interpreter
"""
import pdb
import traceback
import sys
import numpy as np

isa = isinstance
Symbol = str

#============================================================================================ 
# Redefining some operators

def addn(*inputs):
    "Addition operator for n inputs"
    return sum(inputs)

def muln(*inputs):
    "Multiplication operator for n inputs"
    product = 1.0
    for i in inputs:
        product *= i
    return product

def minus(*inputs):
    if len(inputs) == 1:
        return -1.0*inputs[0]
    elif len(inputs) == 2:
        return (inputs[0] - inputs[1])
    else:
        return None    #TODO This is wrong. Must throw error here.
#============================================================================================ 
# Extending the environment with some built in functions

def length(x):
    "Return length of list"
    return len(x)

def mysqrt(x):
    "Returns the square root of the number, -1 if it is negative"
    if x < 0.0:
        return -1.0
    else:
        return np.sqrt(x)

#============================================================================================ 
# Environment - a sub-class of dict

class Env(dict):
    """This keeps track of outer environment, and if the variable is not found in
    itself, it checks in it's parent, recursively. Thus returning innermost env
    where the variable is defined. This implements the scope rule of lisp."""

    def __init__(self, params=(), args=(), outer=None): # for top level env, outer is null
        self.update(zip(params, args))
        self.outer = outer

    def find(self, var):
        """Find the innermost env where a variable is defined."""
        if var in self:
            return self
        else:
            return self.outer.find(var)

def add_globals(env):
    """Here we add the builtin procedures and variables to the given environment"""
    import operator
    env.update(
            {
                '+' : addn, #operator.add,
                '-' : minus, #operator.sub,
                '*' : muln, #operator.mul,
                '/' : operator.div,
                '>' : operator.gt,
                '<' : operator.lt,
                '>=' : operator.ge,
                '<=' : operator.le,
                '=' : operator.eq,
                'sqrt' : mysqrt,
                'length': length,
            }
    )
    env.update({ 'True': True, 'False': False})
    """NOTE: From Nielsen- 
    One notable feature of the global environment is the variables named True
    and False, which evaluate to Python's Boolean True and False, respectively.
    This isn't standard in Scheme (or most other Lisps), but I've done it
    because it ensures that we can use the strings True and False, and get the
    appropriate internal representation."""
    return env

global_env = add_globals(Env())     # Initialise global environment

#============================================================================================ 
# The Read from REPL


def parse(s):
    """string to lisp expression internal representation. TODO: This wont work
    if we treat strings as first class objects in tingu. """
    return read_from(tokenise(s))

def tokenise(s):
    """convert string to list of tokens"""
    return s.replace('(',' ( ').replace(')',' ) ').split()

def read_from(tokens):
    """Read an expression from a sequence of tokens"""
    if len(tokens) == 0:
        raise SyntaxError('Unexpected EOF while reading')
    token = tokens.pop(0)
    if '(' == token:    # if the token denotes the start of a sub-expression -->
        L = []
        while tokens[0] != ')':
            L.append(read_from(tokens))     # --> recursively read from sub-expressions
        tokens.pop(0)   # pop off the ending paranthesis
        return L
    elif ')' == token:
        raise SyntaxError('Unexpected )')
    else:
        return atom(token)  # in case it is a simple atomic expression, return its value

def atom(token):
    """Numbers become numbers, everything else is a symbol"""
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token)

#============================================================================================
# The print part of REPL

def to_string(exp):
    """Convert expression back into a lisp string"""
    if not isa(exp, list):
        return str(exp)
    else:
        return '(' + ' '.join(map(to_string, exp))  + ')'   #recursively process sublists


#============================================================================================ 
# The EVAL from REPL
def eval(x, env=global_env):
    "Evaluate an expression in an environment"
    if isa(x, Symbol):      # variable reference - return the val/exp denoted by the var
        return env.find(x)[x]   # Note the use of find

    elif not isa(x, list):      # not a variable and not a list, meaning it's a literal constant
        return x

    elif x[0] == 'quote' or x[0] == 'q':        # (quote exp) or (q exp)
        (_, exp) = x    # NOTE: Since the form of the expression is known at
                        # this point, we don't care about the keyword,  
                        # and we can directly convert python list into tuple here
        return exp

    elif x[0] == 'atom?':
        (_, exp) = x
        return not isa(eval(exp, env), list)    # if it's not an atom, treat it
                                                # as expression and evaluate
                                                # recursively returning the value

    elif x[0] == 'eq?':     # eq? evals to true if values are 
                            # same and the exps are not lists
        (_, exp1, exp2) = x
        v1, v2 = eval(exp1, env), eval(exp2, env)
        return (not isa(v1, list) and (v1 == v2))

    elif x[0] == 'car':     # return the val of first element of the list
        (_, exp) =  x
        return eval(exp, env)[0]

    elif x[0] == 'cdr':     # return the val of remainder of the list
        (_, exp) = x
        return eval(exp, env)[1:]

    elif x[0] == 'cons':    # if the second expression is a list,
                            # add val of first exp as an element  
                            # to it at the start
        (_, exp1, exp2) = x
        return [eval(exp1, env)] + eval(exp2, env)

    elif x[0] == 'cond':    # evaluate each expression in the list, if its condition is true - multi-way conditional
        for (p, e) in x[1:]:
            if eval(p, env):
                return eval(e, env)

    elif x[0] == 'null?':       # if the expression is null, return true
        (_, exp) = x
        return eval(exp, env) == [] 

    elif x[0] == 'if':          # (if test consq alt)
        (_, test, conseq, alt) = x
        return eval((conseq if eval(test, env) else alt),env)

    elif x[0] == 'set!':          # set value of defined variable
        (_, var, exp) = x
        env.find(var)[var] = eval(exp, env)
    
    elif x[0] == 'define':          # define variable
        (_, var, exp) = x
        env[var] = eval(exp, env)

    elif x[0] == 'lambda':          # define a lambda expression, ie create a
                                    # nested environment
        (_, vars, exp) = x
        return lambda *args: eval(exp, Env(params=vars, args=args, outer=env))

    elif x[0] == 'begin':           # begin new list of expressions to eval one
                                    # by one and return the final value
        for exp in x[1:]:
            val = eval(exp, env)
        return val
    else:                           # (proc exp*) x is a list of expressions,
                                    # eval them all
        exps = [eval(exp, env) for exp in x]
        proc = exps.pop(0)
        return proc(*exps)
#============================================================================================ 
# The REPL 
def repl(prompt='tingu> '):
    """A prompt read-eval-print loop"""
    while True:
        try:
            val = eval(parse(raw_input(prompt)))
            if val is not None: 
                 print to_string(val)
        except KeyboardInterrupt:
            print '\nBye!\n'
            sys.exit()
        except:
            handle_error()

#============================================================================================ 
# Load from a file and run

def running_paren_sums(program):
    """
    Map the lines in the list program to a list whose entries contain
    a running sum of the per-line difference between the number of '('
    parentheses and the number of ')' parentheses.
    """
    count_open_parens = lambda line: line.count("(")-line.count(")")
    paren_counts = map(count_open_parens, program)
    rps = []
    total = 0
    for paren_count in paren_counts:
        total += paren_count
        rps.append(total)
    return rps

def load(filename):
    """
    Load the tiddlylisp program in filename, execute it, and start the
    repl.  If an error occurs, execution stops, and we are left in the
    repl.  Note that load copes with multi-line tiddlylisp code by
    merging lines until the number of opening and closing parentheses
    match.
    """
    print "Loading and executing %s" % filename
    f = open(filename, "r")
    program = f.readlines()
    f.close()
    rps = running_paren_sums(program)
    full_line = ""
    for (paren_sum, program_line) in zip(rps, program):
        program_line = program_line.strip()
        full_line += program_line+" "
        if paren_sum == 0 and full_line.strip() != "":
            try:
                val = eval(parse(full_line))
                if val is not None: print to_string(val)
            except:
                handle_error()
                print "\nThe line in which the error occurred:\n%s" % full_line
                break
            full_line = ""
    repl()


def handle_error():
    """Bare bones error handling"""
    print 'Error. Py stack-trace:\n'
    traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) > 1: 
        load(sys.argv[1])
    else: 
        repl()
