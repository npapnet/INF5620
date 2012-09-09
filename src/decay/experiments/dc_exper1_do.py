#!/usr/bin/env python
import os, sys, glob

# The command line must contain dt values
if len(sys.argv) > 1:
    dt_values = [float(arg) for arg in sys.argv[1:]]
else:
    print 'Usage: %s dt1 dt2 dt3 ...';  sys.exit(1)  # abort

# Fixed physical parameters
I = 1
a = 2
T = 5

# Run module file and grab output
cmd = 'python dc_mod.py --I %g --a %g --makeplot --T %g' % \
      (I, a, T)
dt_values_str = ' '.join([str(v) for v in dt_values])
cmd += ' --dt %s' % dt_values_str
print cmd
from subprocess import Popen, PIPE, STDOUT
p = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
output, dummy = p.communicate()
failure = p.returncode
if failure:
    print 'Command failed:', cmd; sys.exit(1)

errors = {'dt': dt_values, 1: [], 0: [], 0.5: []}
min_E = 1E+20; max_E = -min_E  # keep track of min/max E for axis
for line in output.splitlines():
    words = line.split()
    if words[0] in ('0.0', '0.5', '1.0'):  # line with E?
        # typical line: 0.0   1.25:    7.463E+00
        theta = float(words[0])
        E = float(words[2])
        errors[theta].append(E)
        min_E = min(min_E, E);  max_E = max(max_E, E)

import matplotlib.pyplot as plt
plt.loglog(errors['dt'], errors[0], 'ro-')
#plt.hold('on')  # Matlab style...
plt.loglog(errors['dt'], errors[0.5], 'b+-')
plt.loglog(errors['dt'], errors[1], 'gx-')
plt.legend(['FE', 'CN', 'BE'], loc='upper left')
plt.xlabel('log(time step)')
plt.ylabel('log(error)')
plt.axis([min(dt_values), max(dt_values), min_E, max_E])
plt.title('Error vs time step')
plt.savefig('error.png')

# Combine images into rows with 2 plots in each row
# imagefiles['FE'] holds a list of files for the FE method
montage_commands = []
for method in 'BE', 'CN', 'FE':
    imagefiles = ['%s_%s.png' % (method, dt) for dt in dt_values]
    montage_commands.append(
        'montage -background white -geometry 100%' + \
        ' -tile 2x %s %s.png' % (' '.join(imagefiles), method))

for cmd in montage_commands:
    print cmd
    failure = os.system(cmd)
    if failure:
        print 'Command failed:', cmd; sys.exit(1)

# Remove the files generated by dc_mod.py and all the
# temporary files tmp*.png generated above
filenames = glob.glob('*_*.png') + glob.glob('tmp*.png')
for filename in filenames:
    os.remove(filename)

#plt.show()  # at the end of the program

# Write Doconce report
do = open('tmp_report.do.txt', 'w')
title = 'Experiments with Schemes for Exponential Decay'
author1 = 'Hans Petter Langtangen Email:hpl@simula.no at '\
          'Center for Biomedical Computing, '\
          'Simula Research Laboratory and '\
          'Department of Informatics, University of Oslo.'
date = 'August 20, 2012'

dt_values_str = ', '.join([str(v) for v in dt_values])

# Remember to use raw string because of latex commands for math
do.write(r"""
TITLE: %(title)s
AUTHOR: %(author1)s
DATE: %(date)s

__Summary.__
This report investigates the accuracy of three finite difference
schemes for the ordinary differential equation $u'=-au$ with the
aid of numerical experiments. Numerical artifacts are in particular
demonstrated.

# Include table of contents (latex and html; sphinx always has a toc)

TOC: on

# Purpose: section with multi-line equation.

======= Mathematical problem =======
label{math:problem}

idx{model problem} idx{exponential decay}

We address the initial-value problem

!bt
\begin{align}
u'(t) &= -au(t), \quad t \in (0,T], label{ode}\\
u(0)  &= I,                         label{initial:value}
\end{align}
!et
where $a$, $I$, and $T$ are prescribed parameters, and $u(t)$ is
the unknown function to be estimated. This mathematical model
is relevant for physical phenomena featuring exponential decay
in time.

# Purpose: section with single-line equation and a bullet list.

======= Numerical solution method =======
label{numerical:problem}

idx{mesh in time} idx{$\theta$-rule} idx{numerical scheme}
idx{finite difference scheme}

We introduce a mesh in time with points $0= t_0< t_1 \cdots < t_N=T$.
For simplicity, we assume constant spacing $\Delta t$ between the
mesh points: $\Delta t = t_{n}-t_{n-1}$, $n=1,\ldots,N$. Let
$u^n$ be the numerical approximation to the exact solution at $t_n$.

The $\theta$-rule is used to solve (ref{ode}) numerically:

!bt
\[
u^{n+1} = \frac{1 - (1-\theta) a\Delta t}{1 + \theta a\Delta t}u^n,
\]
!et
for $n=0,1,\ldots,N-1$. This scheme corresponds to

  * The Forward Euler scheme when $\theta=0$
  * The Backward Euler scheme when $\theta=1$
  * The Crank-Nicolson scheme when $\theta=1/2$

# Purpose: section with computer code taken from a part of
# a file. The fromto: f@t syntax copies from the regular
# expression f up to the line, but not including, the regular
# expression t.

======= Implementation =======

The numerical method is implemented in a Python function:

@@@CODE ../dc_mod.py  fromto: def solver@def verify_three

# Purpose: section with figures.

======= Numerical experiments =======

idx{numerical experiments}

We define a set of numerical experiments where $I$, $a$, and $T$ are
fixed, while $\Delta t$ and $\theta$ are varied.
In particular, $I=%(I)g$, $a=%(a)g$, $\Delta t = %(dt_values_str)s$.

""" % vars())

short2long = dict(FE='The Forward Euler method',
                  BE='The Backward Euler method',
                  CN='The Crank-Nicolson method')
methods = 'BE', 'CN', 'FE'
inline_figures = True  # True: subsections with inline graphics
                       # False: no subsecs, figures with captions
if inline_figures:
    for method in methods:
        do.write("""

# Purpose: subsection with inline figure (figure without caption).

===== %s =====

idx{%s}

FIGURE: [%s.png, width=800]

""" % (short2long[method], method, method))
else:
    do.write("""

===== Time series =====

Figures ref{fig:BE}-ref{fig:FE} display the results.

""")
    # Full figures with captions
    for method in methods:
        fig = 'FIGURE: [%s.png, width=800] %s. '\
              'label{fig:%s}\n\n' % \
              (method, short2long[method], method)
        do.write(fig)

# Remember raw string for latex math with backslashes
do.write(r"""

# Purpose: exemplify referring to a figure with label and caption.

===== Error vs $\Delta t$ =====

idx{error vs time step}

How $E$ varies with $\Delta t$ for $\theta=0,0.5,1$
is shown in Figure ref{fig:E}.

FIGURE: [error.png, width=400] Error versus time step. label{fig:E}
""")

# Good habits when writing for latex, sphinx and mathjax-html
# at once:
#
# Minimize math in captions as the caption becomes the figure
# name in sphinx, when referring to figures, and any math
# is deleted in the name.
#
# Use \[, equation or align enviroments in latex math.
# Sphinx cannot handle labels in align environments.
#
# Figures float around in latex, but are placed at where
# they are defined in sphinx and html. Figures without captions
# are placed inline in latex and may be convenient.
#
# Remember raw strings for any text with latex math with
# backslashes.
