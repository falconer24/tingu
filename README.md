# tingu

Tingu is a toy Lisp interpreter, written in Python based on tiddlylisp, 
which was intended to accompany Michael Nielsen's essay
[Lisp as the Maxwell's equations of software](http://michaelnielsen.org/ddi/lisp-as-the-maxwells-equations-of-software/).

The repository contains the following files:

`tingu.py`: A simple interpreter for a subset of Lisp.
Tingu is adapted from and closely based on Peter Norvig's
[lispy interpreter](http://norvig.com/lispy.html).

Initially I merely replicated Nielsen's interpreter. I am now making
updates to it as I work through the exercise problems. The end product
of this effort should be a somewhat more polished and usable LISP
subset interpreter. This will serve as a base for future interpreter
projects, slowly phasing out the dependence on python runtime, with a 
my implementation of the runtime backend.
