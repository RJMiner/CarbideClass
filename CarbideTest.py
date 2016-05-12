# -*- coding: utf-8 -*-
"""
Created on Tue May 10 15:20:43 2016

@author: Miner
"""

# datapath = 'C:\\Users\\Richard\\Documents\\CNC\\'
datapath = 'C:\\Users\\Richard\\CarbideDrawings\\'

import CarbideClass as CC

CONVERT_FILE = 1
MIRROR_DRAWING = 2

opt = 99

if opt == CONVERT_FILE:
    cnc = CC.CNC(datapath + 'TRB_01old')
    c2 = CC.convert_285to286(cnc)
    c2.save(datapath + 'TRB_01')

elif opt == MIRROR_DRAWING:
    cnc = CC.CNC(datapath + 'DinoHead3')
    lft,btm,rit,top = cnc.extents()
    cnc.setvalue('WIDTH', round(rit + 6.9999))
    c2 = cnc.mirror()
    c2.save(datapath + 'DinoHead7')