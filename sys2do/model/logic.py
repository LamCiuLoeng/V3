# -*- coding: utf-8 -*-
'''
###########################################
#  Created on 2011-10-19
#  @author: CL.Lam
#  Description:
###########################################
'''

import datetime
from sqlalchemy import Table, ForeignKey, Column, Date, Time
from sqlalchemy.types import Unicode, Integer, DateTime, Text
from sqlalchemy.orm import relation, backref, relationship
from sqlalchemy.sql.expression import and_

from sys2do.model import DeclarativeBase, metadata, DBSession
from auth import SysMixin, User
from sys2do.util.sa_helper import JSONColumn

__all__ = ['Clinic', 'DoctorProfile', 'NurseProfile', 'Events', 'Message', 'Holiday',
           'UploadFile', 'District', 'Area', 'clinic_doctor_table', 'clinic_nurse_table']


class District(DeclarativeBase, SysMixin):
    __tablename__ = 'district'

    id = Column(Integer, autoincrement = True, primary_key = True)
    name = Column(Text)
    name_tc = Column(Text)


class Area(DeclarativeBase, SysMixin):
    __tablename__ = 'area'

    id = Column(Integer, autoincrement = True, primary_key = True)
    name = Column(Text)
    name_tc = Column(Text)
    district_id = Column(Integer, ForeignKey('district.id'))
    district = relation(District, backref = backref("area", order_by = id), primaryjoin = "and_(District.id == Area.district_id, Area.active == 0)")



clinic_doctor_table = Table('clinic_doctor', metadata,
    Column('clinic_id', Integer, ForeignKey('clinic.id',
        onupdate = "CASCADE", ondelete = "CASCADE"), primary_key = True),
    Column('doctor_id', Integer, ForeignKey('doctor_profile.id',
        onupdate = "CASCADE", ondelete = "CASCADE"), primary_key = True)
)


clinic_nurse_table = Table('clinic_nurse', metadata,
    Column('clinic_id', Integer, ForeignKey('clinic.id',
        onupdate = "CASCADE", ondelete = "CASCADE"), primary_key = True),
    Column('nurse_id', Integer, ForeignKey('nurse_profile.id',
        onupdate = "CASCADE", ondelete = "CASCADE"), primary_key = True)
)



class Clinic(DeclarativeBase, SysMixin):
    __tablename__ = 'clinic'

    id = Column(Integer, autoincrement = True, primary_key = True)
    code = Column(Text)
    name = Column(Text)
    name_tc = Column(Text)
    address = Column(Text)
    address_tc = Column(Text)
    desc = Column(Text)
    tel = Column(Text)
    website = Column(Text)
    district = Column(Text)
    street = Column(Text)
    location = Column(Text)
    doctors = relation('DoctorProfile', secondary = clinic_doctor_table, backref = 'clinics')
    nurses = relation('NurseProfile', secondary = clinic_nurse_table, backref = 'clinics')
    area_id = Column(Integer, ForeignKey('area.id'))
    area = relation(Area, backref = backref("clinics", order_by = id), primaryjoin = "and_(Area.id == Clinic.area_id, Clinic.active == 0)")
    coordinate = Column(Text)

    def __str__(self): return self.name
    def __repr__(self): return self.name



class DoctorProfile(DeclarativeBase, SysMixin):
    __tablename__ = 'doctor_profile'

    id = Column(Integer, autoincrement = True, primary_key = True)
    user_id = Column(Integer)
    desc = Column(Unicode(1000))
    worktime_setting = Column(JSONColumn(5000))
    rating_score = Column(Integer, default = 0)
    rating_count = Column(Integer, default = 0)

    def getUserProfile(self):
        user = DBSession.query(User).get(self.user_id)
        info = user.populate()
        info['profile_id'] = self.id
        info['desc'] = self.desc
        info['worktime_setting'] = self.worktime_setting
        return info

    @property
    def name(self):
        return unicode(DBSession.query(User).get(self.user_id))

    @property
    def rating(self):
        if self.rating_count == 0 : return 0
        return self.rating_score / self.rating_count



class DoctorComment(DeclarativeBase, SysMixin):
    __tablename__ = 'doctor_comment'

    id = Column(Integer, autoincrement = True, primary_key = True)
    doctor_id = Column(Integer, ForeignKey('doctor_profile.id'))
    doctor = relation(DoctorProfile, backref = backref("comments", order_by = id), primaryjoin = "and_(DoctorProfile.id == DoctorComment.doctor_id, DoctorComment.active == 0)")
    content = Column(Text)



class NurseProfile(DeclarativeBase, SysMixin):
    __tablename__ = 'nurse_profile'

    id = Column(Integer, autoincrement = True, primary_key = True)
    user_id = Column(Integer)
    desc = Column(Text)




class Events(DeclarativeBase, SysMixin):
    __tablename__ = 'events'

    id = Column(Integer, autoincrement = True, primary_key = True)
    user_id = Column(Integer)
    doctor_id = Column(Integer)
    date = Column(Text)
    time = Column(Text)
    status = Column(Integer, default = 0)
    remark = Column(Text)

    def showStatus(self):
        return {
                0 : "NEW",
                1 : "CONFIRMED",
                2 : "CANCEL"
                }[self.status]


    @property
    def user(self):
        return DBSession.query(User).get(self.user_id)

    @property
    def doctor_info(self):
        return DBSession.query(DoctorProfile).get(self.doctor_id)


class Message(DeclarativeBase, SysMixin):
    __tablename__ = 'message'

    id = Column(Integer, autoincrement = True, primary_key = True)
    user_id = Column(Integer, ForeignKey('system_user.id'))
    user = relation(User, backref = backref("messages", order_by = id), primaryjoin = "and_(User.id == Message.user_id, Message.active == 0)")
    subject = Column(Text)
    content = Column(Text)
    type = Column(Text)
    status = Column(Integer, default = 0)





class Holiday(DeclarativeBase, SysMixin):
    __tablename__ = 'system_holiday'
    id = Column(Integer, autoincrement = True, primary_key = True)
    year = Column(Integer)
    month = Column(Integer)
    day = Column(Integer)
    region = Column(Text)

    @classmethod
    def isHoliday(clz, d):
        if isinstance(d, (str, unicode)):
            try:
                year, month, day = d[:10].split('-')
                DBSession.query(clz).filter(and_(clz.year == year, clz.month == month, clz.day == day)).one()
                return True
            except:
                pass
        elif isinstance(d, (datetime.datetime, datetime.date)):
            try:
                DBSession.query(clz).filter(and_(clz.year == d.year, clz.month == d.month, clz.day == d.day)).one()
                return True
            except:
                pass
        return False




class UploadFile(DeclarativeBase, SysMixin):
    __tablename__ = 'system_upload_file'

    id = Column(Integer, autoincrement = True, primary_key = True)
    name = Column(Text)
    path = Column(Text)
    url = Column(Text)
    remark = Column(Text)

