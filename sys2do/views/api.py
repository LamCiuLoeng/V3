# -*- coding: utf-8 -*-
'''
###########################################
#  Created on 2012-9-5
#  @author: cl.lam
#  Description:
###########################################
'''
import traceback
from flask.globals import request
from flask.helpers import jsonify
from sys2do.util.common import _g
from sys2do.model import DBSession
from sqlalchemy.sql.expression import and_, desc, func
from sys2do.model.auth import User
from sys2do.model.logic import DoctorProfile, DoctorComment, Clinic, District, \
    Area
from sys2do import app
from sys2do.model.logic import clinic_doctor_table

MSG_NO_SUCH_METHOD = "No such api function"
MSG_PARAMS_MISSING = "params missing"
MSG_USER_NOT_EXIST = "The user does not exist!"
MSG_WRONG_PASSWORD = "The password is wrong!"
MSG_VALIDATE_SUCCESS = "login success"
MSG_PARAMS_EMPTY = "The field(s) should not empty!"
MSG_SERVER_ERROR = "There's error occur on the server side!"
MSG_SAVE_SUCCESS = "Save the record successfully!"
MSG_EMAIL_BLANK_ERROR = "The email could not be blank!"
MSG_PASSWORD_BLANK_ERROR = "The password could not be blank!"
MSG_PASSWORD_NOT_MATCH = "The password and repassword are not the same!"
MSG_EMAIL_EXIST = "The email is already exist!"



def doAction():
    action = _g('action', None)
    if action not in ['login', 'register', 'getLocationData', 'getDoctorList', 'getDoctorDetail', 'getComment', 'addComment']:
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

    if not username : return jsonify({'result' : 0 , 'msg' : MSG_EMAIL_BLANK_ERROR})
    if not password : return jsonify({'result' : 0 , 'msg' : MSG_PASSWORD_BLANK_ERROR})

    try:
        user = DBSession.query(User).filter(and_(User.active == 0 , func.upper(User.email) == username.upper())).one()
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



def register():
    fields = ['email', 'password', 'repassword']
    if _check_params(fields) != 0 : return jsonify({'result' : 0 , 'msg' : MSG_PARAMS_MISSING})

    email = _g('email')
    password = _g('password')
    repassword = _g('repassword')

    if not email : return jsonify({'result' : 0 , 'msg' : MSG_EMAIL_BLANK_ERROR})
    if not password : return jsonify({'result' : 0 , 'msg' : MSG_PASSWORD_BLANK_ERROR})
    if password != repassword : return jsonify({'result' : 0 , 'msg' : MSG_PASSWORD_NOT_MATCH})

    try:
        DBSession.query(User).filter(and_(User.active == 0, func.upper(User.email) == email.upper())).one()
        return jsonify({'result' : 0 , 'msg' : MSG_EMAIL_EXIST})
    except:
        traceback.print_exc()
        pass
    display_name = _g('display_name') or email
    try:
        u = User(email = email, password = password, display_name = display_name)
        DBSession.add(u)
        DBSession.commit()
        return jsonify({'result' : 1 , 'msg' : MSG_SAVE_SUCCESS, 'id' : u.id , 'point' : u.point})
    except:
        traceback.print_exc()
        return jsonify({'result' : 0 , 'msg' : MSG_SERVER_ERROR})


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
    lang = _g('lang')
    for (u, d, c, a, dd) in DBSession.query(User, DoctorProfile, Clinic, Area, District).filter(and_(
                                                                         User.id == DoctorProfile.user_id,
                                                                         Clinic.id == clinic_doctor_table.c.clinic_id,
                                                                         DoctorProfile.id == clinic_doctor_table.c.doctor_id,
                                                                         Clinic.area_id == Area.id,
                                                                         Area.district_id == District.id,
                                                                         )):
        for dtmp in data:
            if dtmp['id'] == dd.id:
                dInfo = dtmp
                break
        else:
            dInfo = {"id" : dd.id ,
                     "name" : dd.name_tc if lang == 'zh_HK' else dd.name,
                     "children" : []}
            data.append(dInfo)

        for atmp in dInfo['children']:
            if atmp['id'] == a.id:
                aInfo = atmp
                break
        else:
            aInfo = {"id" : a.id,
                     "name" : a.name_tc if lang == 'zh_HK' else a.name,
                     "children" : []}
            dInfo['children'].append(aInfo)


        aInfo['children'].append({
                      "doctorID" : d.id,
                      "name" : u.display_name_tc if lang == 'zh_HK' else u.display_name,
                      "location" : c.address_tc if lang == 'zh_HK' else c.address,
                      })

    return jsonify({'result' : 1 , "data" : data})



#===============================================================================
# params : lang : the language code
#          locationIndex: the location index
#===============================================================================
def getDoctorList():
    fields = ['lang', 'locationIndex']
    if _check_params(fields) != 0 : return jsonify({'result' : 0 , 'msg' : MSG_PARAMS_MISSING})

    ds = []
    lang = _g('lang')
    locationIndex = _g('locationIndex')
    for c in DBSession.query(Clinic).filter(and_(Clinic.active == 0, Clinic.area_id == locationIndex)):
        latitude = longtitude = None
        if c.coordinate:
            latitude, longtitude = c.coordinate.split(",")
        for d in c.doctors:
            ds.append({
                       "doctorID" : d.id,
                       "clinicID" : c.id,
                       "name"     : c.name_tc if lang == 'zh_HK' else c.name,
                       "latitude" : latitude,
                       "longtitude" : longtitude,
                       "address"    : c.address_tc if lang == 'zh_HK' else c.address,
                       })

    return jsonify({"result" : 1 , "data" : ds})


#===============================================================================
# params : lang : the language code
#          doctorID
# return : result: 1/0
#          data : the detail of the doctor
#===============================================================================
def getDoctorDetail():
    fields = ['lang', 'doctorID', 'clinicID']
    if _check_params(fields) != 0 : return jsonify({'result' : 0 , 'msg' : MSG_PARAMS_MISSING})

    lang = _g('lang')
    dp = DBSession.query(DoctorProfile).get(_g('doctorID'))
    base_info = dp.getUserProfile()

    c = DBSession.query(Clinic).get(_g('clinicID'))
    latitude = longtitude = None
    if c.coordinate:
        latitude, longtitude = c.coordinate.split(",")
    return jsonify({
                    "result" : 1,
                    "data"   : {
                                "doctorID"  : dp.id,
                                "name"      : base_info['display_name_tc'] if lang == 'zh_HK' else base_info['display_name'],
                                "desc"      : dp.desc,
                                "address"   : c.address_tc if lang == 'zh_HK' else c.address,
                                "image"     : base_info['image_url'],
                                "mapLocationX" : longtitude,
                                "mapLocationY" : latitude,
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

