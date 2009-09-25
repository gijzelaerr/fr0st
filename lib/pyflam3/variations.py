##############################################################################
#  The Combustion Flame Engine - pyflam3
#  http://combustion.sourceforge.net
#
#  Copyright (C) 2007 by Bobby R. Ward <bobbyrward@gmail.com>
#
#  The Combustion Flame Engine is free software; you can redistribute
#  it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Library General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this library; see the file COPYING.LIB.  If not, write to
#  the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
#  Boston, MA 02111-1307, USA.
##############################################################################

from collections import defaultdict

from constants import flam3_nvariations


VAR_LINEAR = 0
VAR_SINUSOIDAL =   1
VAR_SPHERICAL = 2
VAR_SWIRL =3
VAR_HORSESHOE  =4
VAR_POLAR =5
VAR_HANDKERCHIEF =6
VAR_HEART = 7
VAR_DISC = 8
VAR_SPIRAL = 9
VAR_HYPERBOLIC = 10
VAR_DIAMOND = 11
VAR_EX = 12
VAR_JULIA = 13
VAR_BENT = 14
VAR_WAVES = 15
VAR_FISHEYE = 16
VAR_POPCORN = 17
VAR_EXPONENTIAL = 18
VAR_POWER = 19
VAR_COSINE = 20
VAR_RINGS = 21
VAR_FAN = 22
VAR_BLOB = 23
VAR_PDJ = 24
VAR_FAN2 = 25
VAR_RINGS2 = 26
VAR_EYEFISH = 27
VAR_BUBBLE = 28
VAR_CYLINDER = 29
VAR_PERSPECTIVE = 30
VAR_NOISE = 31
VAR_JULIAN = 32
VAR_JULIASCOPE = 33
VAR_BLUR = 34
VAR_GAUSSIAN_BLUR = 35
VAR_RADIAL_BLUR = 36
VAR_PIE = 37
VAR_NGON = 38
VAR_CURL = 39
VAR_RECTANGLES = 40
VAR_ARCH = 41
VAR_TANGENT = 42
VAR_SQUARE = 43
VAR_RAYS = 44
VAR_BLADE = 45
VAR_SECANT2 = 46
VAR_TWINTRIAN = 47
VAR_CROSS = 48
VAR_DISC2 = 49
VAR_SUPER_SHAPE = 50
VAR_FLOWER = 51
VAR_CONIC = 52
VAR_PARABOLA = 53
VAR_BENT2 = 54
VAR_BIPOLAR = 55
VAR_BOARDERS = 56
VAR_BUTTERFLY = 57
VAR_CELL = 58
VAR_CPOW = 59
VAR_CURVE = 60
VAR_EDISC = 61
VAR_ELLIPTIC = 62
VAR_ESCHER = 63
VAR_FOCI = 64
VAR_LAZYSUSAN = 65
VAR_LOONIE = 66
VAR_PRE_BLUR = 67
VAR_MODULUS = 68
VAR_OSCOPE = 69
VAR_POLAR2 = 70
VAR_POPCORN2 = 71
VAR_SCRY = 72
VAR_SEPARATION = 73
VAR_SPLIT = 74
VAR_SPLITS = 75
VAR_STRIPES = 76
VAR_WEDGE = 77
VAR_WEDGE_JULIA = 78
VAR_WEDGE_SPH = 79
VAR_WHORL = 80
VAR_WAVES2 = 81


variations = {}
variation_list = [None] * 82 #flam3_nvariations
for k,v in locals().items():
    if k.startswith("VAR_"):
        name = k[4:].lower()
        variations[name] = v
        variation_list[v] = name


variable_dict = {'blob_low': 0.2,  
                 'blob_high': 1.0,  
                 'blob_waves': 5.0,  
                 'pdj_a': 0.5,  
                 'pdj_b': 2.0,  
                 'pdj_c': 0.8,  
                 'pdj_d': 1.0,  
                 'fan2_x': 0.4,  
                 'fan2_y': 4.0,  
                 'rings2_val': 0.5,  
                 'perspective_angle': 0.4,  
                 'perspective_dist': 2.0,  
                 'julian_power': 4.0,  
                 'julian_dist': 1.0,  
                 'juliascope_power': 4.0,  
                 'juliascope_dist': 1.0,  
                 'radial_blur_angle': 0.5,  
                 'pie_slices': 5.0,  
                 'pie_rotation': 0.0,  
                 'pie_thickness': 0.4,  
                 'ngon_sides': 5.0,  
                 'ngon_power': 0.6,  
                 'ngon_circle': 0.3,  
                 'ngon_corners': 1.0,  
                 'curl_c1': 0.4,  
                 'curl_c2': 0.5,  
                 'rectangles_x': 0.4,  
                 'rectangles_y': 0.3,  
                 'disc2_rot': 0.5,  
                 'disc2_twist': 0.5,  
                 'super_shape_rnd': 0.4,  
                 'super_shape_m': 5.0,  
                 'super_shape_n1': 0.4,  
                 'super_shape_n2': 0.6,  
                 'super_shape_n3': 0.4,  
                 'super_shape_holes': -0.4,  
                 'flower_petals': 7.0,  
                 'flower_holes': 0.2,  
                 'conic_eccentricity': 0.6,  
                 'conic_holes': 0.5,  
                 'parabola_height': 0.8,  
                 'parabola_width': 0.5,  
                 'bent2_x': 0.3,  
                 'bent2_y': 0.5,  
                 'bipolar_shift': 0.0,  
                 'cell_size': 0.5,  
                 'cpow_r': 0.5,                   
                 'cpow_i': 0.3,  
                 'cpow_power': 2.0,                   
                 'curve_xamp': 0.4,                   
                 'curve_yamp': -0.6,                   
                 'curve_xlength': 2.0,                   
                 'curve_ylength': 1.0,                   
                 'escher_beta': 0.6,                   
                 'lazysusan_spin': 0.5,                   
                 'lazysusan_space': 0.3,                   
                 'lazysusan_twist': 3.0,                   
                 'lazysusan_x': 0.0,  
                 'lazysusan_y': 0.0,                   
                 'modulus_x': 0.4,                   
                 'modulus_y': 1.0,                   
                 'oscilloscope_separation': 0.0,                   
                 'oscilloscope_frequency': 2.0,                   
                 'oscilloscope_amplitude': 1.0,                   
                 'oscilloscope_damping': 0.5,                   
                 'popcorn2_x': 0.2,                   
                 'popcorn2_y': 0.2,                   
                 'popcorn2_c': 4.0,  
                 'separation_x': 0.3,                   
                 'separation_xinside': 0.5,                   
                 'separation_y': 0.2,                   
                 'separation_yinside': 0.4,                   
                 'split_xsize': 2.0,                   
                 'split_ysize': 1.0,                   
                 'splits_x': 0.2,                   
                 'splits_y': 0.1,                   
                 'stripes_space': -0.5,                   
                 'stripes_warp': 2.0,  
                 'wedge_angle': 0.5,                   
                 'wedge_hole': 0.0,                   
                 'wedge_count': 3.0,                   
                 'wedge_swirl': 0.4,                   
                 'wedge_julia_angle': 0.2,                   
                 'wedge_julia_count': 7.0,                   
                 'wedge_julia_power': 3.0,                   
                 'wedge_julia_dist': 4.0,                   
                 'wedge_sph_angle': 0.5,                   
                 'wedge_sph_count': 3.0,  
                 'wedge_sph_hole': 0.0,                   
                 'wedge_sph_swirl': 0.4,                   
                 'whorl_inside': 0.3,                   
                 'whorl_outside': -0.2,                   
                 'waves2_freqx': 0.8,                   
                 'waves2_scalex': 1.0,                   
                 'waves2_freqy': 0.4,                   
                 'waves2_scaley': 2.0}         

variables = defaultdict(list)
for k,v in variable_dict.iteritems():
    tion, ble = k.rsplit("_", 1)
    variables[tion].append((ble, v))

