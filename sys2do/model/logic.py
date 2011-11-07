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
from sqlalchemy.types import Unicode, Integer, DateTime
from sqlalchemy.orm import relation, backref
from sqlalchemy.sql.expression import and_

from sys2do.model import DeclarativeBase, metadata, DBSession
from auth import SysMixin, User
from sys2do.util.sa_helper import JSONColumn

__all__ = ['Clinic', 'DoctorProfile', 'NurseProfile', 'Events', 'Message', 'Holiday', 'UploadFile', 'District', 'Area']


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
    code = Column(Unicode(100))
    name = Column(Unicode(100))
    address = Column(Unicode(1000))
    desc = Column(Unicode(1000))
    tel = Column(Unicode(50))
    website = Column(Unicode(100))
    district = Column(Unicode(500))
    street = Column(Unicode(500))
    location = Column(Unicode(20))
    doctors = relation('DoctorProfile', secondary = clinic_doctor_table, backref = 'clinics')
    nurses = relation('NurseProfile', secondary = clinic_nurse_table, backref = 'clinics')


    def __str__(self): return self.name
    def __repr__(self): return self.name


class DoctorProfile(DeclarativeBase, SysMixin):
    __tablename__ = 'doctor_profile'

    id = Column(Integer, autoincrement = True, primary_key = True)
    user_id = Column(Integer)
    desc = Column(Unicode(1000))
    worktime_setting = Column(JSONColumn(5000))

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



class NurseProfile(DeclarativeBase, SysMixin):
    __tablename__ = 'nurse_profile'

    id = Column(Integer, autoincrement = True, primary_key = True)
    user_id = Column(Integer)
    desc = Column(Unicode(1000))




class Events(DeclarativeBase, SysMixin):
    __tablename__ = 'events'

    id = Column(Integer, autoincrement = True, primary_key = True)
    user_id = Column(Integer)
    doctor_id = Column(Integer)
    date = Column(Unicode(10))
    time = Column(Unicode(10))
    status = Column(Integer, default = 0)
    remark = Column(Unicode(1000))

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
    subject = Column(Unicode(200))
    content = Column(Unicode(1000))
    type = Column(Unicode(20))
    status = Column(Integer, default = 0)





class Holiday(DeclarativeBase, SysMixin):
    __tablename__ = 'system_holiday'
    id = Column(Integer, autoincrement = True, primary_key = True)
    year = Column(Integer)
    month = Column(Integer)
    day = Column(Integer)
    region = Column(Unicode(10))

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
    name = Column(Unicode(100))
    path = Column(Unicode(1000))
    url = Column(Unicode(1000))
    remark = Column(Unicode(5000))



class District(DeclarativeBase, SysMixin):
    __tablename__ = 'district'

    id = Column(Integer, autoincrement = True, primary_key = True)
    name = Column(Unicode(100))


class Area(DeclarativeBase, SysMixin):
    __tablename__ = 'area'

    id = Column(Integer, autoincrement = True, primary_key = True)
    name = Column(Unicode(100))
    district_id = Column(Integer, ForeignKey('district.id'))
    district = relation(District, backref = backref("area", order_by = id), primaryjoin = "and_(District.id == Area.district_id, Area.active == 0)")
