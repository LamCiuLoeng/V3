# -*- coding: utf-8 -*-
'''
###########################################
#  Created on 2011-10-19
#  @author: CL.Lam
#  Description:
###########################################
'''

from sqlalchemy import Table, ForeignKey, Column, Date, Time
from sqlalchemy.types import Unicode, Integer, DateTime
from sqlalchemy.orm import relation, backref

from sys2do.model import DeclarativeBase, metadata, DBSession
from auth import SysMixin, User
from sys2do.util.sa_helper import JSONColumn

__all__ = ['Clinic', 'DoctorProfile', 'NurseProfile', 'Events', 'Message', 'Holiday']


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


class DoctorProfile(DeclarativeBase, SysMixin):
    __tablename__ = 'doctor_profile'

    id = Column(Integer, autoincrement = True, primary_key = True)
#    clinic_id = Column(Integer, ForeignKey('clinic.id'))
#    clinic = relation(Clinic, backref = backref("doctors", order_by = id), primaryjoin = "and_(Clinic.id == Doctor.clinic_id, Doctor.active == 0)")
    user_id = Column(Integer)
    desc = Column(Unicode(1000))
    worktime_setting = Column(JSONColumn(5000))




class NurseProfile(DeclarativeBase, SysMixin):
    __tablename__ = 'nurse_profile'

    id = Column(Integer, autoincrement = True, primary_key = True)
#    clinic_id = Column(Integer, ForeignKey('clinic.id'))
#    clinic = relation(Clinic, backref = backref("nurses", order_by = id), primaryjoin = "and_(Clinic.id == Nurse.clinic_id, Nurse.active == 0)")
    user_id = Column(Integer)
    desc = Column(Unicode(1000))




class Events(DeclarativeBase, SysMixin):
    __tablename__ = 'events'

    id = Column(Integer, autoincrement = True, primary_key = True)
    user_id = Column(Integer)
    doctor_id = Column(Integer)
    date = Column(Date)
    time = Column(Time)
    status = Column(Integer)
    remark = Column(Unicode(1000))





class Message(DeclarativeBase, SysMixin):
    __tablename__ = 'message'

    id = Column(Integer, autoincrement = True, primary_key = True)
    user_id = Column(Integer, ForeignKey('system_user.id'))
    user = relation(User, backref = backref("messages", order_by = id), primaryjoin = "and_(User.id == Message.user_id, Message.active == 0)")
    subject = Column(Unicode(200))
    content = Column(Unicode(1000))
    type = Column(Unicode(20))
    status = Column(Integer)





class Holiday(DeclarativeBase, SysMixin):
    __tablename__ = 'system_holiday'
    id = Column(Integer, autoincrement = True, primary_key = True)
    year = Column(Integer)
    month = Column(Integer)
    day = Column(Integer)
    region = Column(Unicode(10))
