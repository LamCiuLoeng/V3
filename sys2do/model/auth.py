# -*- coding: utf-8 -*-
from datetime import datetime as dt
import sys
try:
    from hashlib import sha1
except ImportError:
    sys.exit('ImportError: No module named hashlib\n'
             'If you are on python2.4 this library is not part of python. '
             'Please install it. Example: easy_install hashlib')

from sqlalchemy import Table, ForeignKey, Column
from sqlalchemy.types import Unicode, Integer, DateTime, Date, Text
from sqlalchemy.orm import relation

from sys2do.model import DeclarativeBase, metadata, DBSession

__all__ = ['User', 'Group', 'Permission', 'SysMixin']

def getUserID():
#    return request.identity["user"].user_id
    return None

class SysMixin(object):
    create_time = Column(DateTime, default = dt.now)
    create_by_id = Column(Integer, default = getUserID)
    update_time = Column(DateTime, default = dt.now, onupdate = dt.now)
    update_by_id = Column(Integer, default = getUserID, onupdate = getUserID)
    active = Column(Integer, default = 0)  # 0 is active ,1 is inactive

    @property
    def create_by(self):
        return DBSession.query(User).get(self.create_by_id)

    @property
    def update_by(self):
        return DBSession.query(User).get(self.update_by_id)


# { Association tables


# This is the association table for the many-to-many relationship between
# groups and permissions. This is required by repoze.what.
group_permission_table = Table('system_group_permission', metadata,
    Column('group_id', Integer, ForeignKey('system_group.id',
        onupdate = "CASCADE", ondelete = "CASCADE"), primary_key = True),
    Column('permission_id', Integer, ForeignKey('system_permission.id',
        onupdate = "CASCADE", ondelete = "CASCADE"), primary_key = True)
)

# This is the association table for the many-to-many relationship between
# groups and members - this is, the memberships. It's required by repoze.what.
user_group_table = Table('system_user_group', metadata,
    Column('user_id', Integer, ForeignKey('system_user.id',
        onupdate = "CASCADE", ondelete = "CASCADE"), primary_key = True),
    Column('group_id', Integer, ForeignKey('system_group.id',
        onupdate = "CASCADE", ondelete = "CASCADE"), primary_key = True)
)




class Group(DeclarativeBase, SysMixin):
    __tablename__ = 'system_group'

    id = Column(Integer, autoincrement = True, primary_key = True)
    name = Column(Text, unique = True, nullable = False)
    display_name = Column(Text)

    desc = Column(Text)
    users = relation('User', secondary = user_group_table, backref = 'groups')

    def __repr__(self): return self.display_name or self.name

    def __unicode__(self): return self.display_name or self.name



class User(DeclarativeBase, SysMixin):
    __tablename__ = 'system_user'

    id = Column(Integer, autoincrement = True, primary_key = True)
    email = Column(Text, unique = True, nullable = False)
    password = Column(Text)
    display_name = Column(Text)
    display_name_tc = Column(Text)
#    first_name = Column(Text)
#    last_name = Column(Text)
    phone = Column(Text)
    birthday = Column(Date, default = None)
    image_url = Column(Text)
    point = Column(Integer, default = 0)

    def __str__(self): return self.display_name

    def __repr__(self): return self.display_name

    def __unicode__(self): return self.display_name

    @property
    def permissions(self):
        """Return a set of strings for the permissions granted."""
        perms = set()
        for g in self.groups:
            perms = perms | set(g.permissions)
        return perms


    def populate(self):
        return {
                'id' : self.id,
                'email' : self.email,
                'display_name' : self.display_name,
                'display_name_tc' : self.display_name_tc,
                'image_url' : self.image_url,
                'phone' : self.phone,
                'name' : unicode(self)
                }


class Permission(DeclarativeBase, SysMixin):
    __tablename__ = 'system_permission'

    id = Column(Integer, autoincrement = True, primary_key = True)
    name = Column(Text, unique = True, nullable = False)
    desc = Column(Text)
    groups = relation(Group, secondary = group_permission_table, backref = 'permissions')

    def __repr__(self): return self.name

    def __unicode__(self): return self.name
