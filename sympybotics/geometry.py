# -*- coding: utf-8 -*-

###############################################################################
#  SymPyBotics: Symbolic Robotics Toolbox using Python and SymPy
#
#      Copyright (C) 2012, 2013 Cristóvão Sousa <crisjss@gmail.com>
#
#  Distributed under the terms of the GNU General Public License (GPL),
#  version 2 or any later version.  The full text of the GPL is available at:
#                  http://www.gnu.org/licenses/
###############################################################################


import sympy

from .robot import _joint_i_symb

_id = lambda x: x

class Geometry(object):
  """Robot symbolic geometric transformations."""
  
  def __init__( self, robot , ifunc=None):
    
    if not ifunc: ifunc = _id

    def inverse_T(T):
      return T[0:3,0:3].transpose().row_join( - T[0:3,0:3].transpose() * T[0:3,3] ).col_join( sympy.zeros((1,3)).row_join(sympy.eye(1)) )

    (alpha , a , d , theta) = sympy.symbols('alpha,a,d,theta',real=True)

    self.Tdh = list(range(robot.dof))
    self.Tdh_inv = list(range(robot.dof))
    self.Rdh = list(range(robot.dof))
    self.pdh = list(range(robot.dof))

    dh_transfmat_inv = inverse_T(robot.dh_transfmat)

    q_subs = dict([(_joint_i_symb(i+1),robot.q[i]) for i in range(robot.dof)])

    for l in range(robot.dof):

      subs_dict = dict( zip( robot.dh_symbols, robot.dh_parms[l] ) )

      self.Tdh[l] = robot.dh_transfmat.subs(subs_dict).subs(q_subs)
      self.Tdh_inv[l] = dh_transfmat_inv.subs(subs_dict).subs(q_subs)
      self.Rdh[l] = self.Tdh[l][0 :3 ,0 :3 ]
      self.pdh[l] = self.Tdh[l][0 :3 ,3 ]


    self.T = list(range(robot.dof))
    
    self.T[-1] = sympy.eye(4) # set T[-1] so that T[l-1] for l=0 is correctly assigned, T[-1] is override after
    for l in range(robot.dof):
      self.T[l] = ifunc( self.T[l-1] *  self.Tdh[l] )

    self.R = list(range(robot.dof))
    self.p = list(range(robot.dof))
    self.z = list(range(robot.dof))

    for l in range(robot.dof):
      self.R[l] = self.T[l][0 :3 ,0 :3 ]
      self.p[l] = self.T[l][0 :3 ,3 ]
      self.z[l] = self.R[l][0 :3 ,2 ]

    #######################
    # for screw theory:

    cos = sympy.cos
    sin = sympy.sin
    exp = sympy.exp

    Mr = sympy.Matrix([[  1,           0,            0,  a  ],
                [  0,  cos(alpha),  -sin(alpha),  0  ],
                [  0,  sin(alpha),   cos(alpha),  d  ],
                [  0,           0,            0,  1  ]])
    Pr = sympy.Matrix([[  0, -1,  0,  0  ],
                [  1,  0,  0,  0  ],
                [  0,  0,  0,  0  ],
                [  0,  0,  0,  0  ]])
    ### from Frank Park paper:
    #Mp = sympy.Matrix([[  cos(theta),  -sin(theta)*cos(alpha),            0,  a*cos(theta)  ],
                #[  sin(theta),   cos(theta)*cos(alpha),  -sin(alpha),  a*sin(theta)  ],
                #[           0,              sin(alpha),   cos(alpha),             0  ],
                #[           0,                       0,            0,             1  ]])
    ### my own:
    Mp = sympy.Matrix([[  cos(theta),  -sin(theta)*cos(alpha),   sin(theta)*sin(alpha),  a*cos(theta)  ],
                [  sin(theta),   cos(theta)*cos(alpha),  -cos(theta)*sin(alpha),  a*sin(theta)  ],
                [           0,              sin(alpha),              cos(alpha),             0  ],
                [           0,                       0,                       0,             1  ]])
    Pp = sympy.Matrix([[  0,  0,  0,  0  ],
                [  0,  0,  0,  0  ],
                [  0,  0,  0,  1  ],
                [  0,  0,  0,  0  ]])

    #if 0:
        #D_exp2trig = { exp(SR.wild(0)) : exp(SR.wild(0).real_part()) * ( cos(SR.wild(0).imag_part()) + sympy.I*sin(SR.wild(0).imag_part()) ) }
        #ePtM_r = exp( Pr*theta ) * Mr
        #ePtM_r = ePtM_r.expand().subs(D_exp2trig).simplify_rational()
        #ePtM_p = exp( Pp*d ) * Mp
        #ePtM_p = ePtM_p.expand().subs(D_exp2trig).simplify_rational()
        #if bool( ePtM_r != robot.dh_transfmat or ePtM_p != robot.dh_transfmat ):
            #raise Exception('Geom: interlink transformation does not follows implemented DH formulation')

    Sr = ( inverse_T(Mr) * Pr * Mr ).applyfunc(lambda x: sympy.trigsimp(x))
    Sp = ( inverse_T(Mp) * Pp * Mp ).applyfunc(lambda x: sympy.trigsimp(x))



    def sym_se3_unskew(g):
      w = sympy.Matrix( [ g[2,1], g[0,2], g[1,0] ] )
      v = g[0:3,3]
      return w.col_join(v)

    self.S = list(range(robot.dof))
    for l in range(robot.dof):
        if robot.links_sigma[l]: S = Sp
        else: S = Sr
        self.S[l] = ifunc( sym_se3_unskew( S.subs( dict( zip(robot.dh_symbols, robot.dh_parms[l]) ) ) ) )
