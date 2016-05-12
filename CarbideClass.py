# -*- coding: utf-8 -*-

'''
CarbideClass - a set of classes for working with CarbideCreate
April 30, 2016
May 7, 2016 - Modified for Beta 286 format
May 10, 2016 - Added ability to convert beta 285 to beta 286
'''

import math
import json
import copy
import uuid

CURR_BETA = '286'
EARLY_BETA = '285'
KNOWN_BETA = ('285', '286')

CC_VALUES    = "DOCUMENT_VALUES"
CC_CIRCLES   = "CIRCLE_OBJECTS"
CC_CURVES    = "CURVE_OBJECTS"
CC_POLYGONS  = "POLYGON_OBJECTS"    # discontinued Beta 286
CC_RECTS     = "RECT_OBJECTS"
CC_REGPOLYS  = "REGULAR_POLYGON_OBJECTS"
CC_TEXTS     = "TEXT_OBJECTS"
CC_TOOLPATHS = "TOOLPATH_OBJECTS"
CC_PATHLINKS = "toolpath_links"     # added Beta 286

PT_POLY = 1
PT_CURVE = 3
PT_CLOSER = 4

OFF_NONE = 0
OFF_INSIDE = -1
OFF_OUTSIDE = 1
OFF_POCKET = 2

def offset_label(val):
    if val == OFF_NONE:
        rslt = 'No Offset'
    elif val == OFF_INSIDE:
        rslt = 'Inside'
    elif val == OFF_OUTSIDE:
        rslt = 'Outside'
    elif val == OFF_POCKET:
        rslt = 'Pocket'
    else:
        rslt = 'Unknown'
    return rslt

def machine_label(lbl):
    test = str(lbl).upper()
    if test == '3':
        rslt = 'Shapeoko 3'
    elif test == 'XL':
        rslt = 'Shapeoko XL'
    elif test == 'XXL':
        rslt = 'Shapeoko XXL'
    elif test == '883':
        rslt = 'Nomad 883'
    else:
        rslt = lbl
    return rslt

def beta_groups(beta=CURR_BETA):
    if beta >= '286':
        allgroups = (CC_VALUES, CC_CIRCLES, CC_CURVES, CC_RECTS, CC_REGPOLYS,
                     CC_TEXTS, CC_TOOLPATHS, CC_PATHLINKS)
        idgroups = (CC_CIRCLES, CC_CURVES, CC_RECTS, CC_REGPOLYS, CC_TEXTS)
        namegroups = (CC_TOOLPATHS, )
        uuidgroups = (CC_PATHLINKS, )
    else:               # such as version 285
        allgroups = (CC_VALUES, CC_CIRCLES, CC_CURVES, CC_POLYGONS, CC_RECTS,
                     CC_REGPOLYS, CC_TEXTS, CC_TOOLPATHS)
        idgroups = (CC_CIRCLES, CC_CURVES, CC_POLYGONS, CC_RECTS, CC_REGPOLYS,
                    CC_TEXTS)
        namegroups = (CC_TOOLPATHS, )
        uuidgroups = ()
    return (allgroups, idgroups, namegroups, uuidgroups)

# --------------------------------------------------------------

def id_is_int(beta=CURR_BETA):
    return beta < '286'

def has_closed_flag(beta=CURR_BETA):
    return beta < '286'

def has_polygons(beta=CURR_BETA):
    return beta < '286'

def has_contour(beta=CURR_BETA):
    return beta < '286'

def has_uuid(beta=CURR_BETA):
    return beta >= '286'

def has_point_type(beta=CURR_BETA):
    return beta >= '286'

# --------------------------------------------------------

def nextlabel(txt):
    rslt = ''
    if len(txt) < 1:
        rslt = 'Auto_001'
    elif txt[-1].isdigit():
        pnt = len(txt) - 1
        while pnt >= 0:
            if not txt[pnt].isdigit():
                rslt = txt[:pnt+1] + '1' + txt[pnt+1:]
                break
            elif txt[pnt] < '9':
                txt = txt[:pnt] + str(int(txt[pnt])+1) + txt[pnt+1:]
                rslt = txt
                break
            else:
                txt = txt[:pnt] + '0' + txt[pnt+1:]
                pnt -= 1
        if pnt < 0:
            rslt = '1' + txt
    elif txt[-1].isalpha():
        rslt = txt + '_001'
    else:
        rslt = txt + '001'
    return rslt

def newuuid():
    return '{%s}' % str(uuid.uuid4())

def uulabel(ref):
    txt = str(ref)
    if len(txt) > 8: txt = txt[:3] + '..' + txt[-3:]
    return txt

#---------------------------------------------------------

def tight(thing):
    rslt = None
    typ = type(thing)
    if typ in (list, tuple):
        rslt = []
        for val in thing:
            rslt.append(tight(val))
    elif typ is float:
        rslt = round(thing, 5)
    elif typ is dict:
        rslt = {}
        for key in thing.keys():
            rslt[key] = tight(thing[key])
    else:
        rslt = thing
    return rslt

_cos_rot = _sin_rot = 0.0

def set_rotation(rot):
    global _cos_rot, _sin_rot
    rot = math.radians(rot)
    _cos_rot = math.cos(rot)
    _sin_rot = math.sin(rot)

def rotate(xx, yy):
    global _cos_rot, _sin_rot
    tx = _cos_rot*xx - _sin_rot*yy
    ty = _sin_rot*xx + _cos_rot*yy
    return tx,ty

# --------------------------------------------------------

class extents:
    def __init__(self, low=-10000, high=10000):
        self.lft = high
        self.top = low
        self.rit = low
        self.btm = high
    
    def test(self, xx, yy):
        if xx < self.lft: self.lft = xx  #
        if xx > self.rit: self.rit = xx  #
        if yy < self.btm: self.btm = yy  #
        if yy > self.top: self.top = yy  #
    
    def extents(self):
        return (self.lft, self.btm, self.rit, self.top)
    
# -----------------------------------------------------------

class CNC:
    def __init__(self, filename=None, use_mm=True, width=340, height=280,
                 thickness=12.7, gridspacing=3, machine='XL',
                 beta=CURR_BETA):
        if filename is not None: filename = str(filename)  #
        if beta == 0: beta = EARLY_BETA  #
        machlbl = machine_label(machine)
        
        self.filename = filename
        self.content = {}
        self.indent = 4
        self.beta = beta

        newfile = True
        if filename is not None:
            newfile = not self.load(filename)
        
        allgr, idgr, namgr, uugr = beta_groups(self.beta)
        self.cc_allgroups = allgr
        self.cc_idgroups = idgr
        self.cc_namegroups = namgr
        self.cc_uuidgroups = uugr
        
        if newfile:
            self.beta = beta
            values = {
                "BACKGROUND_IMAGE": "AAAAAA==",
                "BACKGROUND_OPACITY": 0.5,
                "BACKGROUND_POSITION_X": 0,
                "BACKGROUND_POSITION_Y": 0,
                "BACKGROUND_ROTATION": 0,
                "BACKGROUND_SCALE": 1,
                "BACKGROUND_VISIBLE": False,
                "DISPLAYMM": use_mm,
                "HEIGHT": height,
                "MACHINE": machlbl,
                "MATERIAL": "Soft",
                "RETRACT": 12,
                "THICKNESS": thickness,
                "WIDTH": width,
                "ZERO_X": 0,
                "ZERO_Y": 0,
                "ZERO_Z": 0,
                "grid_enabled": True,
                "grid_spacing": gridspacing,
                "version": 1
            }
            
            self.content = { CC_VALUES: values }
            for group in self.cc_allgroups:
                if group != CC_VALUES:
                    self.content[group] = []
        self.fixbeta()
        
    def __str__(self):
        return ('CarbideCreate save file: %s (beta %s)' %
                (self.filename, self.beta))
    
    def __repr__(self):
        body = json.dumps(self.content, sort_keys=True, indent=self.indent).split('\n')
        for pnt in range(len(body)):
            lin = body[pnt]
            if lin[-3:] == '[],':
                ind = len(lin) - len(lin.lstrip(' '))
                body[pnt] = lin[:-2] + '\n' + (' ' * ind) + '],'
            elif lin[-2:] == '[]':
                ind = len(lin) - len(lin.lstrip(' '))
                body[pnt] = lin[:-1] + '\n' + (' ' * ind) + ']'
        return str.join('\n', body) + '\n'
    
    def tighten(self):
        self.content = tight(self.content)
    
    def getvalue(self, key):
        vals = self.content[CC_VALUES]
        return vals[key] if key in vals else None
    
    def getgroup(self, groupref):
        try:
            return self.content[groupref]
        except:
            return []
    
    def getobject(self, group, ccid):
        rslt = None
        if group in self.content:
            objects = self.content[group]
            for obj in objects:
                if 'id' in obj:
                    objid = obj['id']
                    if objid == ccid:
                        rslt = obj
                        break
                elif 'uuid' in obj:
                    objid = obj['uuid']
                    if objid == ccid:
                        rslt = obj
                        break
        return rslt
    
    def getanyobject(self, ccid):
        rslt = None
        for group in self.cc_idgroups:
            tmp = self.getobject(group, ccid)
            if tmp is not None:
                rslt = [group, tmp]
                break
        if rslt is None:
            for group in self.cc_uuidgroups:
                tmp = self.getobject(group, ccid)
                if tmp is not None:
                    rslt = [group, tmp]
                    break
        return rslt
    
    def gettoolpath(self, name):
        rslt = None
        sname = name.lower()
        if CC_TOOLPATHS in self.content:
            objects = self.content[CC_TOOLPATHS]
            for obj in objects:
                if 'name' in obj:
                    objname = obj['name'].lower()
                    if objname == sname:
                        rslt = obj
                        break
        return rslt
    
    def setvalue(self, valname, val):
        vals = self.content[CC_VALUES]
        vals[valname] = val
    
    def load(self, filename):
        txt = ''
        if '.' not in filename: filename += '.c2d'  #
        try:
            fin = open(filename, 'r')
            txt = fin.read()
            fin.close()
            self.filename = filename
        except:
            print('Unable to load "%s"' % filename)
        
        return (len(txt) > 0) and self.loads(txt)
    
    def loads(self, txt):
        self.content = json.loads(txt)
        
        if id_is_int(self.beta):
            nextid = self.nextid
            for group in self.cc_idgroups:
                objects = self.content[group]
                for obj in objects:
                    if 'id' in obj:
                        tmpid = obj['id']
                        if tmpid >= nextid: nextid = tmpid + 1  #
            self.nextid = nextid
        return True

    def fixbeta(self):
        possible = []
        polytest = CC_POLYGONS in self.content
        crvs = self.getgroup(CC_CURVES)
        crv = None if len(crvs) < 1 else crvs[0]
        contest = False
        concount = 0
        paths = self.getgroup(CC_TOOLPATHS)
        for path in paths:
            if 'contour' in path:
                concount += 1
                if len(path['contour']) > 0:
                    contest = True
                    break

        idset = uuidset = None

        for known in KNOWN_BETA:
            #print('Testing beta %s' % known)
            all_ok = has_polygons(known) == polytest
            #if not all_ok: print('Failed poly test')  #
            if all_ok and concount > 0:
                all_ok = has_contour(known) == contest
                #if not all_ok: print('Failed contour test')  #
            if all_ok and crv is not None:
                all_ok = ('closed' in crv) == has_closed_flag(known)
                #if not all_ok: print('Failed closed curve test')  #
                if all_ok:
                    all_ok = ('point_type' in crv) == has_point_type(known)
                    #if not all_ok: print('Failed point_type test')  #
            if all_ok:
                q,idset,qq,uuidset = beta_groups(known)
                if has_uuid(known):
                    all_ok = False
                    for item in uuidset:
                        if item in self.content:
                            all_ok = True
                            break
                    #if not all_ok: print('Failed uuid test')  #
            if all_ok:
                idcount = 0
                idtest = False
                for group in idset:
                    if group in self.content:
                        objects = self.getgroup(group)
                        for obj in objects:
                            if 'id' in obj:
                                idcount += 1
                                idtest = (type(obj['id']) is int)
                                break
                        if idcount > 0: break
                all_ok = (idcount < 1) or (id_is_int(known) == idtest)
                #if not all_ok: print('Failed id_is_int test')  #
            if all_ok: possible.append(known)  #
        
        self.beta = possible[-1] if len(possible) > 0 else 'BAD'
    
    def save(self, filename=None):
        if filename is None: filename = self.filename  #
        if '.' not in filename: filename += '.c2d'  #

        try:
            fout = open(filename, 'w')
            fout.write(self.__repr__())
            fout.close()
            if self.filename is None: self.filename = filename  #
        except:
            pass
    
    def content_summary(self):
        filename = self.filename
        beta = self.beta
        id_int = id_is_int(self.beta)
        width = round(self.getvalue('WIDTH'))
        height = round(self.getvalue('HEIGHT'))
        
        rslt = ('CNC File: "%s" (beta %s) %5dw x %dh' % 
                (filename, beta, width, height))
        if id_int: rslt += ', Next ID: %d' % self.nextid  #

        groups = list(self.content.keys())
        groups.sort()
        for group in groups:
            hasid = group in self.cc_idgroups
            hasname = group in self.cc_namegroups
            if group != CC_VALUES:
                objects = self.content[group]
                cnt = len(objects)
                rslt += '\n    %s (%d)' % (group, cnt)
                
                if cnt >= 0 and (hasid or hasname):
                    lin = '\n    '
                    for obj in objects:
                        if hasid:
                            txt = uulabel(obj['id'])
                        elif hasname:
                            txt = '%s, ' % obj['name']
                        if len(lin) + len(txt) > 70:
                            rslt += lin
                            lin = '\n    ' + txt
                    rslt += lin[:-2]
        return rslt
    
    def unique_name(self, group, test='Unique 001'):
        objects = self.content[group]
        pathnames = []
        for path in objects:
            if 'name' in path: pathnames.append(path['name'].lower())  #
        while test.lower() in pathnames:
            test = nextlabel(test)
        return test
    
    def update_object(self, obj):
        group = obj.group
        isdone = False
        
        if group in self.cc_namegroups:
            sname = obj.name.lower()
            paths = self.content[group]
            for pnt in range(len(paths)):
                if paths[pnt]['name'].lower() == sname:
                    paths[pnt] = obj.obj_dict()
                    isdone = True
                    break
            
        elif group in self.cc_idgroups:
            ccid = obj.ccid
            objects = self.content[group]
            for pnt in range(len(objects)):
                if objects[pnt]['id'] == ccid:
                    objects[pnt] = obj.obj_dict()
                    isdone = True
                    break
                
        elif group in self.cc_uuidgroups:
            tuuid = obj.uuid
            objects = self.content[group]
            for pnt in range(len(objects)):
                if objects[pnt]['uuid'] == tuuid:
                    objects[pnt] = obj.obj_dict()
                    isdone = True
                    break
        
        if not isdone:
            self.add_object(obj)
    
    def add_object(self, obj):
        group = obj.group
        
        if group == CC_VALUES:
            self.content[CC_VALUES][obj.name] = obj.value
        elif group in self.cc_idgroups:
            if id_is_int(self.beta):
                obj.ccid = self.nextid
                self.nextid += 1
            else:
                obj.ccid = newuuid()
        elif group in self.cc_namegroups:
            obj.name = self.unique_name(group, obj.name)
        elif group in self.cc_uuidgroups:
            obj.uuid = newuuid()

        if group not in self.content: self.content[group] = []  #
        self.content[group].append(obj.obj_dict())
    
    def add_pathlink(self, pathlink):
        tuuid = pathlink['uuid']
        links = pathlink['links']
        uuset = self.getgroup(CC_PATHLINKS)
        uuseek = True
        for pnt in len(uuset):
            if uuset[pnt]['uuid'] == tuuid:
                linkset = uuset[pnt]['links']
                for link in links:
                    linkseek = True
                    for ll in linkset:
                        if link == ll:
                            linkseek = False
                            break
                    if linkseek: linkset.append(link)  #
                uuseek = False
                break
        if uuseek: uuset.append(pathlink)  #
        return
    
    def extents(self):
        ext = extents()
        
        for group in self.cc_idgroups:
            objects = self.getgroup(group)
            for obj in objects:
                if 'position' in obj:
                    ox,oy = obj['position']
                else:
                    ox = oy = 0.0
                
                if group == CC_CURVES:
                    points = obj['points']
                    for pnt in points:
                        ext.test(ox + pnt[0], oy + pnt[1])
                
                elif group == CC_POLYGONS:
                    rot = obj['rotation']
                    dorot = rot != 0.0
                    if dorot: set_rotation(rot)  #
                    
                    points = obj['points']
                    for pnt in points:
                        xx, yy = pnt
                        if dorot: xx,yy = rotate(xx, yy)  #
                        ext.test(ox + xx, oy + yy)
                
                elif group == CC_RECTS:
                    wd2 = obj['width'] / 2
                    hd2 = obj['height'] / 2
                    rot = obj['rotation']
                    dorot = rot != 0.0
                    if dorot: set_rotation(rot)  #
                    xx,yy = rotate(ox-wd2, oy-hd2)
                    ext.test(xx, yy)
                    xx,yy = rotate(ox+wd2, oy-hd2)
                    ext.test(xx, yy)
                    xx,yy = rotate(ox-wd2, oy+hd2)
                    ext.test(xx, yy)
                    xx,yy = rotate(ox-wd2, oy+hd2)
                    ext.test(xx, yy)
                
                elif group == CC_TEXTS:
                    width = obj['width']
                    height = obj['height']
                    if width < 0.0: 
                        text = obj['text']
                        width = len(text) * height * .7
                    
                    rot = obj['rotation']
                    dorot = rot != 0.0
                    if dorot: set_rotation(rot)  #
                    
                    ext.test(ox,oy)
                    xx,yy = 0, height
                    if dorot: xx,yy = rotate(xx,yy)  #
                    ext.test(ox+xx, oy+yy)
                    xx,yy = width, 0
                    if dorot: xx,yy = rotate(xx,yy)  #
                    ext.test(ox+xx, oy+yy)
                    xx,yy = width, height
                    if dorot: xx,yy = rotate(xx,yy)  #
                    ext.test(ox+xx, oy+yy)
                    
                if group == CC_CIRCLES or group == CC_REGPOLYS:
                    rad = obj['radius']
                    ext.test(ox-rad, oy-rad)
                    ext.test(ox+rad, oy+rad)
                
        return ext.extents()
    
    def mirror(self):
        rslt = CNC(beta=self.beta)
        rslt.content = copy.deepcopy(self.content)
        
        width = rslt.getvalue('WIDTH')
        
        for group in rslt.cc_idgroups:
            objects = rslt.getgroup(group)
            for obj in objects:
                obj['position'][0] = width - obj['position'][0]
                
                if group == CC_CIRCLES:
                    pass    # no other changes needed
                
                elif group == CC_CURVES:
                    points = obj['points']
                    for pnt in points:
                        pnt[0] = -pnt[0]
                    cp1s = obj['control_point_1'] 
                    for cp1 in cp1s:
                        cp1[0] = -cp1[0]
                    cp2s = obj['control_point_2'] 
                    for cp2 in cp2s:
                        cp2[0] = -cp2[0]
                
                elif group == CC_POLYGONS:
                    obj['rotations'] = 180.0 - obj['rotatation']
                    points = obj['points']
                    for pnt in points:
                        pnt[0] = -pnt[0]
                
                elif group in (CC_RECTS, CC_REGPOLYS, CC_TEXTS):
                    obj['rotations'] = 180.0 - obj['rotatation']
        return rslt
    
# ----------------------------------------------------------------------

class CC_Object:
    def __init__(self, group, position=None, beta=CURR_BETA):
        if position is not None:
            try:
                xx = position[0]
                yy = position[1]
            except:
                xx = yy = 0.0
            position = [xx,yy]
        
        self.beta = beta
        self.group = group
        self.position = position
        self.ccid = 0 if id_is_int(beta) else '?'
        self.name = ''
        self.uuid = ''
        self.value = 0
    
    def __str__(self):
        group = self.group
        allgrp, idgrp, namegrp, uuidgrp = beta_groups(self.beta)
        
        if group in idgrp:
            rslt = self.ccid
        elif group == CC_VALUES:
            rslt = '%s = %s' % (self.name, self.value)
        elif self.group in namegrp:
            rslt = self.name
        elif group in uuidgrp:
            rslt = str(self.uuid)
        else:
            rslt = '(Unknown)'
        return '%s: %s' % (group, rslt)
    
    def obj_dict(self):
        return {}
    
class Circle(CC_Object):
    def __init__(self, position=None, radius=None, source=None,
                 beta=CURR_BETA):
        group = CC_CIRCLES
        
        if source is None:
            if position is None: position = [0.0,0.0]  #
            if radius is None: radius = 3.0  #
        
        else:
            if position is None: position = source['position']  #
            if radius is None: radius = source['radius']  #
        
        super().__init__(group, position, beta)
        self.radius = radius
    
    def __str__(self):
        return ('Circle, At %s, Radius %5.3f, ID: %s' % 
                (self.position, self.radius, self.ccid))
    
    def obj_dict(self):
        return {
            "id": self.ccid,
            "position": self.position,
            "radius": self.radius
        }

class Curve(CC_Object):
    def __init__(self, position=None, ispoly=False, source=None,
                 beta=CURR_BETA):
        group = CC_CURVES
        
        super().__init__(group, position, beta)
        if has_point_type(beta):
            curve_286(self, ispoly, source)
        else:
            curve_285(self, source)
    
    def __str__(self):
        wants_closed = has_closed_flag(self.beta)
        lbl = ' ('
        if wants_closed: lbl = 'Closed' if self.closed else 'Open'  #
        lbl += (' Polygon)' if self.ispoly else 'Curve)')

        cnt = len(self.points)
        return ('Curve, at %s,%s with %d points ID: %s' %
                (self.position, lbl, cnt, self.ccid))
    
    def addpoint(self, atx, aty=None, cp1x=None, cp1y=None,
                 cp2x=None, cp2y=None):
        if aty is None:
            atx, aty = atx
            cp1x = cp2x = atx
            cp1y = cp2y = aty
        elif cp1x is None:
            cp1x = cp2x = atx
            cp1y = cp2y = aty
        elif cp1y is None:
            cp2x, cp2y = cp1x
            cp1x, cp1y = aty
            atx, aty = atx

        self.points.append([atx,aty])
        self.cp1.append([cp1x,cp1y])
        self.cp2.append([cp2x,cp2y])
        
        if has_point_type(self.beta):
            if (len(self.points) > 0 and atx == self.points[0][0] and
                aty == self.points[0][1]):
                ptype = PT_CLOSER
            elif self.ispoly:
                ptype = PT_POLY
            else:
                ptype = PT_CURVE
            self.pt.append(ptype)
    
    def fix_point_type(self, ispoly=None):
        hasptype = has_point_type(self.beta)
        if ispoly is None: ispoly = self.ispoly if hasptype else False
        ptype = PT_POLY if hasptype and ispoly else PT_CURVE
        
        self.ispoly = ispoly
        
        cnt = len(self.points)
        if cnt < 1:
            self.cp1 = []
            self.cp2 = []
            if hasptype: self.pt = []  #
        
        else:
            if len(self.cp1) > cnt:
                self.cp1 = self.cp1[:cnt]
            elif len(self.cp1) < cnt:
                for pnt in range(len(self.cp1), cnt):
                    self.cp1.append([self.points[pnt][0],self.points[pnt][1]])
            if len(self.cp2) > cnt:
                self.cp2 = self.cp2[:cnt]
            elif len(self.cp2) < cnt:
                for pnt in range(len(self.cp2), cnt):
                    self.cp1.append([self.points[pnt][0],self.points[pnt][1]])
            if hasptype:
                if len(self.pt) > cnt:
                    self.pt = self.pt[:cnt]
                elif len(self.pt) < cnt:
                    for pnt in range(len(self.pt), cnt):
                        self.pt.append(ptype)
            
            for pnt in range(cnt):
                xx = self.points[pnt][0]
                yy = self.points[pnt][1]
                self.points[pnt][0] = xx
                self.points[pnt][1] = yy
                if ispoly:
                    self.cp1[pnt][0] = xx
                    self.cp1[pnt][1] = yy
                    self.cp2[pnt][0] = xx
                    self.cp2[pnt][1] = yy
                else:
                    self.cp1[pnt][0] = self.cp1[pnt][0]
                    self.cp1[pnt][1] = self.cp1[pnt][1]
                    self.cp2[pnt][0] = self.cp2[pnt][0]
                    self.cp2[pnt][1] = self.cp2[pnt][0]
                if hasptype:
                    self.pt[pnt] = ptype
            if hasptype and self.points[0] == self.points[-1]:
                self.pt[-1] = PT_CLOSER
        
    def obj_dict(self):
        rslt = {
            "id": self.ccid,
            "position": self.position,
            "points": copy.deepcopy(self.points),
            "control_point_1": copy.deepcopy(self.cp1),
            "control_point_2": copy.deepcopy(self.cp2)
        }
        
        if has_closed_flag(self.beta): rslt["closed"] = self.closed  #
        if has_point_type(self.beta): rslt["point_type"] = self.pt  #

def curve_286(crv286, ispoly, src286=None):
    if crv286.beta != '286':
        raise ValueError('Bad object, not beta 286.')
    if src286 is None:
        crv286.ispoly = ispoly
        if crv286.position is None: crv286.position = [0.0,0.0]  #
        crv286.points = []
        crv286.cp1 = []
        crv286.cp2 = []
        crv286.pt = []
    elif src286.beta != '286':
        raise ValueError('Bad source, not beta 286.')
    else:
        crv286.ispoly = src286.ispoly
        if crv286.position is None:
            crv286.position = [src286.position[0], src286.position[1]]
        crv286.points = copy.deepcopy(src286.points)
        crv286.cp1 = copy.deepcopy(src286.cp1)
        crv286.cp2 = copy.deepcopy(src286.cp2)
        crv286.pt = copy.deepcopy(src286.pt)

def curve_285(crv285, src285):
    if crv285.beta != '285':
        raise ValueError('Bad object, not beta 285.')
    if src285 is None:
        crv285.closed = True
        crv285.ispoly = False
        if crv285.position is None: crv285.position = [0.0,0.0]  #
        crv285.points = []
        crv285.cp1 = []
        crv285.cp2 = []
    elif src285.beta != '285':
        raise ValueError('Bad source, not beta 285.')
    else:
        crv285.closed = src285.closed
        crv285.ispoly = src285.ispoly
        if crv285.position is None:
            crv285.position = [src285.position[0], src285.position[1]]
        crv285.points = copy.deepcopy(src285.points)
        crv285.cp1 = copy.deepcopy(src285.cp1)
        crv285.cp2 = copy.deepcopy(src285.cp2)

class Polygon(CC_Object):       # only use prior to beta 286
    def __init__(self, position=None, rotation=None, source=None,
                 beta=CURR_BETA):
        group = CC_POLYGONS
        
        super().__init__(group, position, beta)

        if source is None:
            if position is None: position = [0.0,0.0]  #
            points = []
        else:
            if position is None: position = source['position']  #
            if rotation is None: rotation = source['rotation']  #
            points = source['points']
            
        self.position = position
        self.rotation = rotation
        self.points = points
    
    def __str__(self):
        cnt = len(self.points)
        return ('ID:%4d Polygon, at %s, with %d points' %
                (self.ccid, self.position, cnt))
    
    def addpoint(self, atx, aty=None):
        if aty is None:
            atx, aty = atx
        self.points.append([atx,aty])
        
    def obj_dict(self):
        return {
            "id": self.ccid,
            "position": self.position,
            "points": copy.deepcopy(self.points),
            "rotation": self.rotation
        }
    
class Rect(CC_Object):
    def __init__(self, position=None, width=None, height=None, rotation=None,
                 source=None, beta=CURR_BETA):
        group = CC_RECTS
        
        if source is None:
            if position is None: position = [0.0,0.0]  #
            if width is None: width = 10.0  #
            if height is None: height = 5.0  #
            if rotation is None: rotation = 0.0  #
        else:
            if position is None: position = source['position']  #
            if width is None: width = source['width']  #
            if height is None: height = source['height']  #
            if rotation is None: rotation = source['rotation']  #
        
        super().__init__(group, position, beta)
        self.width = width
        self.height = height
        self.rotation = rotation

    def __str__(self):
        return ('Rectangle, At %s, %5.3fw x %5.3fh, Rotation %5.3f, ID: %s' %
                (self.position, self.width, self.height,
                 self.rotation, self.ccid))
    
    def obj_dict(self):
        return {
            "id": self.ccid,
            "position": self.position,
            "width": self.width,
            "height": self.height,
            "rotation": self.rotation
        }

class RegPoly(CC_Object):
    def __init__(self, position=None, num_sides=None, radius=None,
                 rotation=None, source=None, beta=CURR_BETA):
        group = CC_REGPOLYS
        
        if source is None:
            if position is None: position = [0.0,0.0]  #
            if num_sides is None: num_sides = 6  #
            if radius is None: radius = 5.0  #
            if rotation is None: rotation = 0.0  #
        else:
            if position is None: position = source['position']  #
            if num_sides is None: num_sides = source['num_sides']  #
            if radius is None: radius = source['radius']  #
            if rotation is None: rotation = source['rotation']  #
        
        super().__init__(group, position, beta)
        self.numsides = num_sides
        self.radius = radius
        self.rotation = rotation
    
    def __str__(self):
        return ('Regular Polygon, At %s, %d Sides, Radius %5.3f,' +
                ' Rotation %5.3f, ID: %s' %
                (self.position, self.num_sides, self.radius, self.rotation,
                 self.ccid))
    
    def obj_dict(self):
        return {
            "id": self.ccid,
            "position": self.position,
            "num_sides": self.num_sides,
            "radius": self.radius,
            "rotation": self.rotation
        }

class Text(CC_Object):
    def __init__(self, position=None, font=None, height=None, text=None,
                 rotation=None, width=None, source=None, beta=CURR_BETA):
        group = CC_TEXTS
        
        if source is None:
            if position is None: position = [0.0,0.0]  #
            if font is None: font = 'Arial'  #
            if height is None: height = 20  #
            if width is None: width = -1  #
            if text is None: text ='empty text'  #
            if rotation is None: rotation = 0.0  #
        else:
            if position is None: position = source['position']  #
            if font is None: font = source['font']  #
            if height is None: height = source['height']  #
            if width is None: width = source['width']  #
            if text is None: text = source['text']  #
            if rotation is None: rotation = source['rotation']  #
        
        super().__init__(group, position, beta)
        self.font = font
        self.width = width
        self.height = height
        self.text = text
        self.rotation = rotation
    
    def __str__(self):
        txt = self.text
        if len(txt) > 20: txt = txt[:9] + '..' + txt[-9:]  #
        return ('Text "%s", At %s, Font "%s", Height %5.3f,' +
                ' Rotation %5.3f, ID: %s' %
                (txt, self.position, self.font, self.height,
                 self.rotation, self.ccid))
    
    def obj_dict(self):
        return {
            "id": self.ccid,
            "position": self.position,
            "font": self.font,
            "width": self.width,
            "height": self.height,
            "text": self.text,
            "rotation": self.rotation
        }

class Toolpath(CC_Object):
    def __init__(self, contour_id=None, name=None, end_depth=None,
                 stepdown=None, auto=None, source=None, beta=CURR_BETA):
        group = CC_TOOLPATHS
        
        if source is None:
            if auto is None: auto = False  #
            if has_contour(beta):
                if contour_id is None: contour_id = 1  #
                contour_list = [ contour_id ]
            else:
                contour_list = []
            if name is None: name = 'Toolpath 001'  #
            if end_depth is None: end_depth = 3.0  #
            if stepdown is None: stepdown = 1.5  #
            details = {
                "automatic_parameters": auto,
                "contours": contour_list,
                "enabled": True,
                "end_depth": end_depth,
                "name": name,
                "ofset_dir": 2,
                "speeds": {
                    "feedrate": 587,
                    "plungerate": 293,
                    "rpm": 9375
                },
                "start_depth": 0,
                "stepdown": stepdown,
                "stepover": 1.42875,
                "tolerance": 0.01,
                "tool": {
                    "angle": 0,
                    "corner_radius": 1.5875,
                    "diameter": 3.175,
                    "display_mm": False,
                    "flutes": 2,
                    "length": 19.05,
                    "name": "",
                    "number": 102,
                    "overall_length": 30.48,
                    "uuid": "{00000000-0000-0000-0000-000000000102}"
                },
                "vcarve": False
            }
        else:
            details = copy.deepcopy(source)
            if auto is not None: details['automatic_parameters'] = auto  #
            if contour_id is not None:
                if has_contour(beta):
                    contour_list = [ contour_id ]
                else:
                    contour_list = []
                details['contour'] = contour_list
            if name is not None: details['name'] = name  #
            if end_depth is not None: details['end_depth'] = end_depth  #
            if stepdown is not None: details['stepdown'] = stepdown  #
            
        super().__init__(group, None, beta)
        self.details = details
    
    def __str__(self):
        offset = offset_label(self.details['ofset_dir'])
        depth = -self.details['end_depth']
        return ('ToolPath: %s (%s Down:%5.3f)' % (self.name, offset, depth))
    
    def obj_dict(self):
        return copy.deepcopy(self.details)

class PathLink(CC_Object):
    def __init__(self, shape=None, toolpath=None, source=None, beta=CURR_BETA):
        group = CC_PATHLINKS
        
        if source is None:
            uushape = '?' if shape is None else shape['id']
            uupaths = [ ('?' if toolpath is None else toolpath['uuid']) ]
        else:
            uushape = source['uuid']
            uupaths = copy.deepcopy(source['links'])
        
        super().__init__(group, None, beta)
        self.uuid = uushape
        self.links = uupaths
    
    def __str__(self):
        shapetxt = uulabel(self.uuid)
        pathtxt = ''
        for link in self.links:
            pathtxt += ', %s' % uulabel(link)
        if len(pathtxt) > 0: pathtxt = pathtxt[2:]  #
        
        return ('ToolLink: Shape %s Using %s' % (shapetxt, pathtxt))
    
    def obj_dict(self):
        return {
            'uuid': self.uuid,
            'links': copy.deepcopy(self.links)
        }
        
# --------------------------------------------------

def convert_285to286(src285):
    rslt = CNC(beta='286')
    con286 = rslt.content
    val286 = con286[CC_VALUES]
    
    val285 = src285.getgroup(CC_VALUES)
    for key in val285:
        val286[key] = val285[key]
    
    allgr, idgr, namegr, uugr = beta_groups('285')
    xid = {}
    
    newobjects = []
    objects = src285.getgroup(CC_CURVES)
    for obj in objects:
        newobj = curve_285to286(obj)
        ccid = newobj['id']
        tuuid = newuuid()
        xid[ccid] = tuuid
        newobj['id'] = tuuid
        newobjects.append(newobj)
    
    objects = src285.getgroup(CC_POLYGONS)
    for obj in objects:
        newobj = polygon_285to286(obj)
        ccid = newobj['id']
        tuuid = newuuid()
        xid[ccid] = tuuid
        newobj['id'] = tuuid
        newobjects.append(newobj)
    rslt.content[CC_CURVES] = newobjects
    
    for group in idgr:
        if group not in (CC_CURVES, CC_POLYGONS):
            objects = src285.getgroup(group)
            newobjects = []
            for obj in objects:
                newobj = copy.deepcopy(obj)
                ccid = newobj['id']
                tuuid = newuuid()
                xid[ccid] = tuuid
                newobj['id'] = tuuid
                newobjects.append(newobj)
            rslt.content[group] = newobjects
    
    for group in namegr:
        if group != CC_TOOLPATHS:
            objects = src285.getgroup(group)
            newobjects = []
            for obj in objects:
                newobjects.append(copy.deepcopy(obj))
            rslt.content[group] = newobjects
    
    objects = src285.getgroup(CC_TOOLPATHS)
    newobjects = []
    shapetopath = []
    for obj in objects:
        newobj = copy.deepcopy(obj)        
        contours = newobj['contours']
        newobj['contours'] = []
        addobj = False
        if len(contours) > 0:
            tuuid = newuuid()
            newobj['uuid'] = tuuid
            for ccid in contours:
                if ccid in xid:
                    shapetopath.append((xid[ccid], tuuid))
                    addobj = True
        if addobj: newobjects.append(newobj)  #
    rslt.content[group] = newobjects
    
    if len(shapetopath) > 0:
        newobjects = []
        shapetopath.sort()
        olduu = '?'
        oldlinks = []
        for pair in shapetopath:
            newuu, newlink = pair
            if newuu == olduu:
                oldlinks.append(newlink)
            else:
                if len(oldlinks) > 0:
                    newobjects.append({'uuid':olduu, 'links':oldlinks})
                olduu = newuu
                oldlinks = [newlink]
        if len(oldlinks) > 0:
            newobjects.append({'uuid':olduu, 'links':oldlinks})
        rslt.content[CC_PATHLINKS] = newobjects
    
    return rslt

def curve_285to286(crv285):
    # translates beta 285 CURVES to beta 286
    ccid = crv285['id']
    xx,yy = crv285['position']
    position = [round(xx,5), round(yy,5)]
    
    points = crv285['points']
    size = len(points)
    cp1 = crv285['control_point_1']
    if len(cp1) < size:
        for idx in range(len(cp1), size):
            cp1.append([points[idx][0],points[idx][1]])
    cp2 = crv285['control_point_2']
    if len(cp2) < size:
        for idx in range(len(cp2), size):
            cp2.append([points[idx][0],points[idx][1]])
    
    newpoints = [None] * size
    newcp1 = [None] * size
    newcp2 = [None] * size
    newpt = [PT_CURVE] * size
    for idx in range(size):
        newpoints[idx] = [round(points[idx][0],5), round(points[idx][1],5)]
        newcp1[idx] = [round(cp1[idx][0],5), round(cp1[idx][1],5)]
        newcp2[idx] = [round(cp2[idx][0],5), round(cp2[idx][1],5)]
    
    if newpoints[0] != newpoints[-1]:
        xx,yy = newpoints[0]
        newpoints.append([xx,yy])
        newcp1.append([xx,yy])
        newcp2.append([xx,yy])
        newpt.append(PT_CURVE)
        
    newpt[-1] = PT_CLOSER
    
    rslt = {
        "id": ccid,
        "position": position,
        "points": copy.deepcopy(newpoints),
        "control_point_1": copy.deepcopy(newcp1),
        "control_point_2": copy.deepcopy(newcp2),
        "point_type": copy.deepcopy(newpt)
    }
    return rslt

def polygon_285to286(poly285):
    # translates beta 285 POLYGONS to beta 286
    ccid = poly285['id']
    xx,yy = poly285['position']
    position = [round(xx,5), round(yy,5)]
    
    rot = poly285['rotation']
    dorot = rot != 0.0
    if dorot: set_rotation(rot)  #
    
    points = poly285['points']
    size = len(points)
    
    newpoints = [None] * size
    newpt = [PT_POLY] * size
    for idx in range(size):
        tx = points[idx][0]
        ty = points[idx][1]
        if dorot: tx,ty = rotate(tx,ty)  #
        newpoints[idx] = [round(tx,5), round(ty,5)]
    
    if newpoints[0] != newpoints[-1]:
        newpoints.append([newpoints[0][0], newpoints[0][1]])
        newpt.append(PT_POLY)
    
    newpt[-1] = PT_CLOSER
    
    rslt = {
        "id": ccid,
        "position": position,
        "points": copy.deepcopy(newpoints),
        "control_point_1": copy.deepcopy(newpoints),
        "control_point_2": copy.deepcopy(newpoints),
        "point_type": copy.deepcopy(newpt)
    }
    return rslt

# ----------------------------------------------------------------------

'''
dodemo = False
if dodemo:
    cnc = CNC('Dummy.c2d')
    c2 = convert_285to286(cnc)
    c2.save('Dummy286.c2d')
'''