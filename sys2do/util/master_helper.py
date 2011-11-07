# -*- coding: utf-8 -*-
'''
###########################################
#  Created on 2011-11-7
#  @author: cl.lam
#  Description:
###########################################
'''

from sys2do.model import Area, District, DBSession

__all__ = ['getDistrictInfo']


def getDistrictInfo():
    result = getattr(getDistrictInfo, 'result', None)
    if not result:
        result = {}
        for d in DBSession.query(District).filter(District.active == 0):
            result[d.name] = [(a.id, a.name) for a in d.area]
        setattr(getDistrictInfo, 'result', result)

    return result
