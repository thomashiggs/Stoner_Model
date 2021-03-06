#!/usr/bin/env python
"""
This module calculates the spin configuration of a sandwich/multilayers
for applied fields between UPPER and LOWER
"""
import sys
import argparse
import logging
import operator

import math
from math import cos, sin, pi

from scipy.optimize import minimize as minimise

import numpy as np

#import motplotlib.pyplot as plt


# Global definitions
_MU_0 = 1.256637061e-6


class SpinStack(object):
    """
    Model of a spin stack comprising three layers where
    the top and bottom layers are the same material

    We sweep H and determine the minimum

    """

    _J_OUTER = None
    _J_INNER = None

    _K_INNER = None
    _K_OUTER = None

    _M_INNER = None
    _M_OUTER = None

    _THETA_INNER = None
    _THETA_OUTER = None
    
    def __init__(self, n_top, n_middle, n_bottom):

        self.top = [pi] * n_top
        self.middle = [0] * n_middle
        self.bottom = [pi] * n_bottom

    def sweep_h(self, start, end, steps):

        print "Sweeping H from %f to %f with %d steps" % (start, end, steps)

        arrangements = []

        field_range = np.linspace(start, end, steps)
        
        for h in field_range:
            arrangements.append(self.converge_h(h))

        for h in reverse(field_range):
            arrangements.append(self.converge_h(h))

        return arrangements


    def converge_h(self, h, accuracy=10e-3):
        """
        From the current configuration, iteratively calculate
        the new configuration for a given H

        Args:
            h (float)       :   scalar magenetic field

        Kwargs:
            accuracy (float):   When to stop iterating
        """
        def is_inner(i):
            if len(self.top) <= index < len(self.top) + len(self.middle):
                return True
            return False

        def converged(oldstack, newstack):
            print "Accuracy = %f" % (max(map(abs, map(operator.sub, oldstack, newstack))))
            if max(map(abs, map(operator.minus, oldstack, newstack))) < accuracy:
                return True
            return False

        count = 0
        while True:

            combined  = self.top + self.middle + self.bottom
            new_stack = []

            for index, phi in enumerate(combined):
                phi_p = combined[index - 1] if index else phi
                phi_n = combined[index + 1] if index < len(combined) else phi

                if is_inner(index): 
                    msi = self._M_INNER
                    k = self._K_INNER
                    theta = self._THETA_INNER
                    j = self._J_INNER
                else:
                    msi = self._M_OUTER
                    k = self._K_OUTER
                    theta = self._THETA_OUTER
                    j = self._J_OUTER

                msi_p = self._M_INNER if is_inner(index - 1) else self._M_OUTER
                msi_n = self._M_INNER if is_inner(index + 1) else self._M_OUTER

                j_p = self._J_INNER if is_inner(index - 1) else self._J_OUTER
                j_n = self._J_INNER if is_inner(index + 1) else self._J_OUTER

                # Reverse the sign of J on transitions
                if j == j_p and j != j_n:
                    j_n = j_n * -1
                if j == j_n and j != j_p:
                    j_p = j_p * -1

                sign = -1 if h < 0 else 1

                def get_energy(phi_variable):
                    """Function to calculate energy for a given phi"""
                    return (- _MU_0 * msi * h * cos(phi_variable) * sign
                            + k * (sin(phi_variable - theta)**2)
                            - j_n * _MU_0 * msi * msi_n * cos(phi_variable - phi_n)
                            - j_p * _MU_0 * msi * msi_p * cos(phi_variable - phi_p))

                print "About to solve the minimise function..."
                result = minimise(get_energy, [phi], method='TNC', bounds=[(0, 2*pi)])

                if not result.success:
                    print "Minimise function failed!"
                    print result.message

                    ar = []
                    for temp in range(314 * 2):
                        ar.append(get_energy(temp * 0.01))

                    print min(ar)
                    print ar.index(min(ar))
                    sys.exit(1)

                new_phi = result.x[0]

                print "Minimised phi is %f (energy = %f)" % (new_phi, get_energy(new_phi))
                new_stack.append(new_phi)

                self.top = new_stack[0:len(self.top)-1]
                self.middle = new_stack[len(self.top):len(self.top) + len(self.middle) - 1]
                self.bottom = new_stack[len(self.top) + len(self.middle):]

            if count and converged(combined, new_stack): break
            count += 1

        print "Converged to %f in %d iterations" % (accuracy, count)
        return new_stack
                

class NiGdNiStack(SpinStack):

    _J_INNER = 1.82e-21 #Joules
    _J_OUTER = 3.64e-21 #Joules

    _K_INNER = 12960 # Gd, J per m cubed
    _K_OUTER = 109529 #Ni, J per m cubed

    _M_INNER = 7.1 * (9.27400968e-24) * (3e28)  #Gd, A per m
    _M_OUTER = (0.6 * (9.27400968e-24) * (9e28)) #Ni, A per m

    _THETA_INNER = pi/4.0
    _THETA_OUTER = pi/4.0
        


def main():
    # Main calculation
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upper', type=float,
                        help='magnetic field range')
    parser.add_argument('--lower', type=float,
                        help='the lower range')
    parser.add_argument('--steps', type=int,
                        help='the number of steps')

    args = parser.parse_args()

    if args.upper is None or args.lower is None or args.steps is None:
        print "Must provide all arguments"
        parser.print_help()
        sys.exit(1)
        
    print "Started with upper=%f, lower=%f, steps=%d" % (
        args.upper, args.lower, args.steps)

    stack = NiGdNiStack(2, 4, 2)
    result = stack.sweep_h(args.upper, args.lower, args.steps)
    print result

if __name__ == "__main__":
    main()
