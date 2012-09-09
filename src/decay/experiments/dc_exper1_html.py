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

# Write HTML report
html = open('tmp_report.html', 'w')
html.write('''
<html>
<head></head>
<body bgcolor="white">

<title>Numerical investigations</title>

<center><h1>Experiments with Schemes for Exponential Decay</h1></center>

<center><b>Hans Petter Langtangen</b></center>
<center><b>Simula Research Laboratory</b></center>
<center><b>University of Oslo</b></center>
<center><h4>August 20, 2012</h4></center>

<b>Summary.</b> This report investigates the accuracy of three
finite difference schemes for the ordinary differential equation
u'=-au with the aid of numerical experiments.  Numerical
artifacts are in particular demonstrated.

<h2>Mathematical problem</h2>

We address the initial-value problem u'(t)=-au(t),
for t in (0,T], and with initial condition u(0)=I.
Here, I, a, and T are prescribed parameters,
and u(t) is the unknown function to be estimated.
This mathematical model is relevant for physical
phenomena featuring exponential decay in time.

<h2>Numerical solution method</h2>

We use a mesh in time with equally spaced points.
The theta-rule is used to discretize the differential
equation. This scheme corresponds to

<ul>
  <li> The Forward Euler scheme when theta=0
  <li> The Backward Euler scheme when theta=1
  <li> The Crank-Nicolson scheme when theta=1/2
</ul>

<h2>Implementation</h2>

The numerical method is implemented in a Python function:
<pre>
def solver(I, a, T, dt, theta):
    """Solve u'=-a*u, u(0)=I, for t in (0,T] with steps of dt."""
    N = int(round(T/float(dt)))  # no of intervals
    u = zeros(N+1)
    t = linspace(0, T, N+1)

    u[0] = I
    for n in range(0, N):
        u[n+1] = (1 - (1-theta)*a*dt)/(1 + theta*dt*a)*u[n]
    return u, t
</pre>

<h2>Numerical experiments</h2>

We define a set of numerical experiments where I, a, and
T are fixed, while the time step and theta are varied.
In particular, I=%g, a=%g, dt=%s.

''' % (I, a, ', '.join([str(v) for v in dt_values])))

short2long = dict(FE='The Forward Euler method',
                  BE='The Backward Euler method',
                  CN='The Crank-Nicolson method')
for method in 'BE', 'CN', 'FE':
    html.write('\n<h3>%s</h3>\n' % short2long[method])
    html.write('<img src="%s.png" width="800">\n\n' % method)
html.write("""

<h3>Error versus time discretization</h3>

How E varies with the time step, for the three discretization
methods, is shown below.
<p>
<img="error.png", width="400">

</body>
</html>
""")


