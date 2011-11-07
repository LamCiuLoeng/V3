# -*- coding: utf-8 -*-
import traceback
from sys2do.model import metadata, engine, DBSession, Permission, Group, User, Clinic, DoctorProfile, NurseProfile, Holiday, District, Area
#import sys2do.model.logic as logic
import sys
reload(sys)
sys.setdefaultencoding('utf8')

def init():
    try:
        metadata.drop_all(engine)
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
        group_mapping['ADMINISTRATOR'].users = [users_mapping['aa@aa.com'], ]
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
        group_mapping['CLINIC_MANAGER'].users = [users_mapping['c1@aa.com'], users_mapping['c2@aa.com'], ]
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

        area = {
                '香港島' : ['上環', '大坑', '山頂', '中環' , '蘇豪', '蘭桂坊', '天后', '太古', '北角', '半山', '石澳', '西環', '赤柱', '金鐘', '柴灣', '灣仔' , '西灣河', '杏花村', '香港仔', '淺水灣', '深水灣', '跑馬地', '筲箕灣', '銅鑼灣' , '鴨脷洲', '薄扶林', '數碼港', '鰂魚涌'],
                '九龍' : ['太子', '佐敦', '旺角', '油塘', '紅磡', '美孚', '彩虹', '樂富', '藍田', '觀塘', '九龍城', '九龍塘', '九龍灣', '土瓜灣', '大角咀', '牛頭角', '石硤尾', '尖沙咀', '諾士佛臺', '何文田', '油麻地', '長沙灣', '荔枝角', '深水埗', '黃大仙', '慈雲山', '新蒲崗', '鯉魚門', '鑽石山'],
                '新界' : ['上水', '大埔', '大圍', '元朗', '太和', '屯門', '火炭', '西貢', '沙田', '青衣', '粉嶺', '荃灣', '馬灣', '深井', '葵芳', '葵涌', '羅湖', '天水圍', '流浮山', '馬鞍山', '將軍澳', '落馬洲'],
                '離島' : ['大澳', '坪洲', '東涌', '長洲', '大嶼山', '赤鱲角', '南丫島', '愉景灣', '蒲苔島'],
                }

        for k, v in area.items():
            dis = District(name = unicode(k))
            DBSession.add(dis)
            for d in v :
                DBSession.add(Area(name = unicode(d), district = dis))


        DBSession.commit()
    except:
        traceback.print_exc()
        DBSession.rollback()

if __name__ == '__main__':
    print "start"
    init()
    print "finish"
