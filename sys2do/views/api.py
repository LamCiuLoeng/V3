# -*- coding: utf-8 -*-
'''
###########################################
#  Created on 2012-9-5
#  @author: cl.lam
#  Description:
###########################################
'''
from flask.globals import request
from flask.helpers import jsonify
from sys2do.util.common import _g
from sys2do.model import DBSession
from sqlalchemy.sql.expression import and_, desc
from sys2do.model.auth import User
from sys2do.model.logic import DoctorProfile, DoctorComment, Clinic, District

MSG_NO_SUCH_METHOD = "No such api function"
MSG_PARAMS_MISSING = "params missing"
MSG_USER_NOT_EXIST = "The user does not exist!"
MSG_WRONG_PASSWORD = "The password is wrong!"
MSG_VALIDATE_SUCCESS = "login success"
MSG_PARAMS_EMPTY = "The field(s) should not empty!"
MSG_SERVER_ERROR = "There's error occur on the server side!"
MSG_SAVE_SUCCESS = "Save the record successfully!"


def doAction():
    action = _g('action', None)
    if action not in ['login', 'getLocationData', 'getDoctorList', 'getDoctorDetail', 'getComment', 'addComment']:
        return jsonify({'result' : 0 , 'msg' : MSG_NO_SUCH_METHOD})

    return eval("%s()" % action)


#===============================================================================
# check the params
# params ; fields - the fields to be checked
# return : 0 - OK
#          1 - the require fields is missing
#
#===============================================================================
def _check_params(fields):
    for f in fields:
        if f not in request.values : return 1
    return 0

#===============================================================================
# params : userName
#          password
# return : result: 1/0
#          msg: error message
#          userID: userID if login success
#          userName: userName
#
#===============================================================================
def login():

    fields = ['userName', 'password']
    if _check_params(fields) != 0 : return jsonify({'result' : 0 , 'msg' : MSG_PARAMS_MISSING})

    username = _g('userName')
    password = _g('password')
    try:
        user = DBSession.query(User).filter(and_(User.active == 0 , User.email == username)).one()
        if user.password != password:
            return jsonify({'result' : 0 , 'msg' : MSG_WRONG_PASSWORD})
    except:
        return jsonify({'result' : 0 , 'msg' : MSG_USER_NOT_EXIST})

    return jsonify({'result' : 1 , 'msg' : MSG_VALIDATE_SUCCESS,
                    'data' : {
                              "uid": user.id,
                              "name": unicode(user)
                              }
                    })

#===============================================================================
# params : lang : the language code
# return : result: 1/0
#          data : the data of location and doctors
#
#
#===============================================================================
def getLocationData():
    fields = ['lang', ]
    if _check_params(fields) != 0 : return jsonify({'result' : 0 , 'msg' : MSG_PARAMS_MISSING})

    data = []
    for d in DBSession.query(District).filter(and_(District.active == 0)):
        dInfo = {"id" : d.id , "name" : d.name, "children" : []}
        for a in d.area:
            aInfo = {"id" : a.id, "name" : a.name , "children" : []}
            for c in a.clinics:
                for d in c.doctors:
                    aInfo['children'].append({
                                              "doctorID" : d.id,
                                              "name" : d.name,
                                              "location" : c.address,
                                              })
            dInfo["children"].append(aInfo)
        data.append(dInfo)
    return jsonify({'result' : 1 , "data" : data})




#===============================================================================
# params : lang : the language code
#          locationIndex: the location index
#===============================================================================
def getDoctorList():
    fields = ['lang', 'locationIndex']
    if _check_params(fields) != 0 : return jsonify({'result' : 0 , 'msg' : MSG_PARAMS_MISSING})

    ds = []
    locationIndex = _g('locationIndex')
    for c in DBSession.query(Clinic).filter(and_(Clinic.active == 0, Clinic.area_id == locationIndex)):
        for d in c.doctors:
            ds.append({
                       "doctorID" : c.id,
                       "name"     : c.name,
                       "latitude" : None,
                       "longtitude" : None,
                       "address"    : c.address,
                       })

    return jsonify({"result" : 1 , "data" : ds})


#===============================================================================
# params : lang : the language code
#          doctorID
# return : result: 1/0
#          data : the detail of the doctor
#===============================================================================
def getDoctorDetail():
    fields = ['lang', 'doctorID']
    if _check_params(fields) != 0 : return jsonify({'result' : 0 , 'msg' : MSG_PARAMS_MISSING})

    dp = DBSession.query(DoctorProfile).get(_g('doctorID'))
    base_info = dp.getUserProfile()

    return jsonify({
                    "result" : 1,
                    "data"   : {
                                "doctorID"  : dp.id,
                                "name"      : dp.name,
                                "desc"      : dp.desc,
                                "address"   : None,
                                "image"     : base_info['image_url'],
                                "mapLocationX" : None,
                                "mapLocationY" : None,
                                "rating": dp.rating,
                                }
                    })



#===============================================================================
#  params : lang : the language code
#           doctorID
#  retrun : result: 1/0
#           data : the detail of the doctor
#
#===============================================================================
def getComment():
    fields = ['lang', 'doctorID']
    if _check_params(fields) != 0 : return jsonify({'result' : 0 , 'msg' : MSG_PARAMS_MISSING})
    comments = DBSession.query(DoctorComment, User).filter(and_(DoctorComment.active == 0, User.active == 0,
                                                     DoctorComment.create_by_id == User.id,
                                                     DoctorComment.doctor_id == _g('doctorID')
                                              )).order_by(desc(DoctorComment.create_time))
    return jsonify({
                    "result" : 1,
                    "data"   : [{"userID" : comment.create_by_id,
                                 "name"   : unicode(user),
                                 "comment" : comment.content,
                                 } for (comment, user) in comments]
                    })



#===============================================================================
# params ; lang : the language code
#          doctorID
#          userID
#          comment
# return : result: 1/0
#          data : the comment of the doctor
#===============================================================================
def addComment():
    fields = ['lang', 'doctorID', 'userID', 'comment']
    if _check_params(fields) != 0 : return jsonify({'result' : 0 , 'msg' : MSG_PARAMS_MISSING})

    doctorID = _g('doctorID')
    userID = _g('userID')
    comment = _g('comment')

    if not doctorID or not userID or not comment:
        return jsonify({'result' : 0 , 'msg' : MSG_PARAMS_EMPTY})
    try:
        DBSession.add(DoctorComment(
                                    doctor_id = doctorID, content = comment,
                                    create_by_id = doctorID
                                    ))
        DBSession.commit()
        return jsonify({"result" : 1 , "msg" : MSG_SAVE_SUCCESS})
    except:
        DBSession.rollback()
        return jsonify({"result" : 0 , "msg" : MSG_SERVER_ERROR})

