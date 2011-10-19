# -*- coding: utf-8 -*-
import traceback
from sys2do.model import metadata, engine, DBSession, Permission, Group, User, Clinic, DoctorProfile, NurseProfile, Holiday
#import sys2do.model.logic as logic
import sys
reload(sys)
sys.setdefaultencoding('utf8')

def init():
    try:
        metadata.create_all(engine)

        #add the HK holiday 
        for d in ["0101", "0203", "0204", "0205", "0405", "0423", "0425", "0502", "0510",
              "0606", "0701", "0913", "1001", "1005", "1226", "1227"]:
            DBSession.add(Holiday(year = 2011, month = d[:2], day = d[2:], region = 'HK'))

        permissions = ["ORDER_ADD", "ORDER_VIEW", "ORDER_CANCEL", "ORDER_UPDATE", "ORDER_VIEW_ALL",
                   "CLINIC_ADD", "CLINIC_VIEW", "CLINIC_VIEW_ALL", "CLINIC_UPDATE", "CLINIC_DELETE",
                   "DOCTOR_ADD", "DOCTOR_UPDATE", "DOCTOR_DELETE",
                   "NURSE_ADD", "NURSE_UPDATE", "NURSER_DELETE",
                   ]
        permissions_mapping = {}
        for p in permissions:
            obj = Permission(name = p)
            DBSession.add(obj)
            permissions_mapping[p] = obj

        groups = [
                 ("ADMINISTRATOR", "Administrator"), ("CLINIC_MANAGER", "Clinic Manager"),
                 ("DOCTOR", "Doctor"), ("NURSE", "Nurse"),
                 ("NORMALUSER", "Normal User"), ("TEMPUSER", "Temp User")
                 ]
        group_mapping = {}
        for g in groups:
            obj = Group(name = g[0], display_name = g[1])
            DBSession.add(obj)
            group_mapping[g[0]] = obj


        users = [
             ("aa@aa.com", "Admin", "Test"),
             ("c1@aa.com", "Clinic Manager 1", "Test"),
             ("c2@aa.com", "Clinic Manager 2", "Test"),
             ("u1@aa.com", "User 1", "Test"),
             ("u2@aa.com", "User 2", "Test"),
             ]

        users_mapping = {}
        for u in users:
            obj = User(email = u[0], password = 'aa', first_name = u[1], last_name = u[2])
            DBSession.add(obj)
            users_mapping[u[0]] = obj

        group_mapping['ADMINISTRATOR'].permissions = permissions_mapping.values()
        group_mapping['ADMINISTRATOR'].uses = [users_mapping['aa@aa.com'], ]
        group_mapping['CLINIC_MANAGER'].permissions = [
                                                   permissions_mapping["CLINIC_VIEW"],
                                                   permissions_mapping["CLINIC_UPDATE"],
                                                   permissions_mapping["DOCTOR_ADD"],
                                                   permissions_mapping["DOCTOR_UPDATE"],
                                                   permissions_mapping["DOCTOR_DELETE"],
                                                   permissions_mapping["NURSE_ADD"],
                                                   permissions_mapping["NURSE_UPDATE"],
                                                   permissions_mapping["NURSER_DELETE"],
                                                   permissions_mapping["ORDER_VIEW"],
                                                   permissions_mapping["ORDER_CANCEL"],
                                                   permissions_mapping["ORDER_UPDATE"],
                                                   ]
        group_mapping['CLINIC_MANAGER'].uses = [users_mapping['c1@aa.com'], users_mapping['c2@aa.com'], ]
        group_mapping['DOCTOR'].permissions = [
                                               permissions_mapping["ORDER_VIEW"],
                                               permissions_mapping["ORDER_CANCEL"],
                                               permissions_mapping["ORDER_UPDATE"],
                                               ]
        group_mapping['NURSE'].permissions = [
                                               permissions_mapping["ORDER_VIEW"],
                                               permissions_mapping["ORDER_CANCEL"],
                                               permissions_mapping["ORDER_UPDATE"],
                                              ]

        group_mapping['NORMALUSER'].permissions = [
                                               permissions_mapping["ORDER_ADD"],
                                               permissions_mapping["ORDER_VIEW"],
                                               permissions_mapping["ORDER_CANCEL"],
                                               ]
        group_mapping['NORMALUSER'].uses = [users_mapping['u1@aa.com'], users_mapping['u2@aa.com'], ]


        from clinic_list import clinics
        clinics_mapping = {}
        for (code, name, address, tel) in clinics:
            obj = Clinic(code = unicode(code), name = unicode(name), address = unicode(address), tel = unicode(tel))
            DBSession.add(obj)
            clinics_mapping[code] = obj



        default_worktime = {
                          "MONDAY" : [ ],
                          "TUESDAY" : [],
                          "WEDNESDAY" : [],
                          "THURSDAY" : [],
                          "FRIDAY" : [],
                          "SATURDAY" : [],
                          "SUNDAY" : [],
                          "HOLIDAY" : [],
                          "SPECIAL" : [],
                          }
        from doctors_list import doctors
        doctors_count = {}
        for (code, first_name, last_name, worktime) in doctors:

            if code in doctors_count : doctors_count[code] += 1
            else : doctors_count[code] = 1

            obj = User(email = u"%sDOC_%d@aa.com" % (code, doctors_count[code]), password = u'aa', first_name = unicode(first_name), last_name = unicode(last_name))
            obj.groups = [group_mapping['DOCTOR']]
            DBSession.add(obj)
            DBSession.flush()

            tempWorkTime = default_worktime.copy()
            tempWorkTime.update(worktime)
            wt = {}
            for k, v in tempWorkTime.items():
                wt[k] = map(lambda o:{"times" : o, "seats" : 4}, v)

            objprofile = DoctorProfile(user_id = obj.id, worktime_setting = wt)
            objprofile.clinics = [clinics_mapping[code]]
            DBSession.add(objprofile)

        DBSession.commit()
    except:
        traceback.print_exc()
        DBSession.rollback()

if __name__ == '__main__':
    print "start"
    init()
    print "finish"
