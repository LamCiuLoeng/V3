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
        for d in ["0102", "0123", "0124", "012", "0404", "0406", "0407", "0409", "0428",
              "0501", "0623", "0702", "1001", "1002", "1023", "1225", "1226"]:
            DBSession.add(Holiday(year = 2012, month = d[:2], day = d[2:], region = 'HK'))

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
             ("aa@aa.com", "Admin",),
             ("c1@aa.com", "Clinic Manager 1",),
             ("c2@aa.com", "Clinic Manager 2",),
             ("u1@aa.com", "User 1"),
             ("u2@aa.com", "User 2"),
             ]

        users_mapping = {}
        for u in users:
            obj = User(email = u[0], password = 'aa', display_name = u[1])
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
        for (code, name, address, address_tc, tel, area_id, coordinate) in clinics:
            obj = Clinic(code = unicode(code.strip()), name = unicode(name.strip()),
                         address = unicode(address.strip()), address_tc = unicode(address_tc.strip()),
                         tel = unicode(tel.strip()), area_id = area_id or None,
                         coordinate = coordinate.strip()
                         )
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

            email = u"%sDOC_%d@aa.com" % (code, doctors_count[code])

            obj = User(email = email, password = u'aa', display_name = email)
            obj.groups = [group_mapping['DOCTOR']]
            DBSession.add(obj)
            DBSession.flush()

            tempWorkTime = default_worktime.copy()
            tempWorkTime.update(worktime)
            wt = {}
            for k, v in tempWorkTime.items():
                wt[k] = map(lambda o:{"times" : o, "seats" : 4}, v)

            objprofile = DoctorProfile(user_id = obj.id, worktime_setting = wt)
            if code in clinics_mapping : objprofile.clinics = [clinics_mapping[code]]
            DBSession.add(objprofile)

        area = {
            ('香港島', 'Hong Kong') : [('上環', 'Sheung Wan'), '大坑', '山頂', ('中環', 'Central') , '蘇豪', '蘭桂坊', ('天后', 'Tin Hau'), ('太古', 'Tai Koo'), ('北角', 'North Point'), '半山', '石澳', ('西環', 'Sai Wan'), '赤柱', '金鐘', ('柴灣', 'Chai Wan'), ('灣仔', 'Wan Chai') , ('西灣河', 'Sai Wan Ho'), ('杏花村', 'Heng Fa Chuen'), '香港仔', '淺水灣', '深水灣', ('跑馬地', 'Happy Valley'), ('筲箕灣', 'Shau Kei Wan'), ('銅鑼灣', 'Causeway Bay') , ('鴨脷洲', 'Ap Lei Chau'), '薄扶林', '數碼港', ('鰂魚涌', 'Quarry Bay')],
            ('九龍', 'Kowloon') : [('太子', 'Prince Edward'), ('佐敦', 'Jordan'), ('旺角', 'Mong Kok'), '油塘', ('紅磡', 'Hung Hom'), ('美孚', 'Mei Foo'), ('彩虹', 'Choi Hung'), ('樂富', 'Lok Fu'), ('藍田', 'Lam Tin'), ('觀塘', 'Kwun Tong'), ('九龍城', 'Kowloon City'), '九龍塘', ('九龍灣', 'Kowloon Bay'), ('土瓜灣', 'To Kwa Wan'), ('大角咀', 'Tai Kok Tsui'), ('牛頭角', 'Ngau Tau Kok'), ('石硤尾', 'Shek Kip Mei'), ('尖沙咀', 'Tsim Sha Tsui'), '諾士佛臺', ('何文田', 'Ho Man Tin'), ('油麻地', 'Yau Ma Tei'), ('長沙灣', 'Cheung Sha Wan'), ('荔枝角', 'Lai Chi Kok'), ('深水埗', 'Sham Shui Po'), ('黃大仙', 'Wong Tai Sin'), ('慈雲山', 'Tsz Wan Shan'), ('新蒲崗', 'San Po Kong'), ('鯉魚門', 'Lei Yue Mun'), ('鑽石山', 'Diamond Hill')],
            ('新界', 'New Territories') : [('上水', 'Sheung Shui'), ('大埔', 'Tai Po'), ('大圍', 'Tai Wai'), ('元朗', 'Yuen Long'), ('太和', 'Tai Wo'), ('屯門', 'Tuen Mun'), '火炭', ('西貢', 'Sai Kung'), ('沙田', 'Sha Tin'), ('青衣', 'Tsing Yi'), ('粉嶺', 'Fanling'), ('荃灣', 'Tsuen Wan'), '馬灣', ('深井', 'Sham Tseng'), ('葵芳', 'Kwai Fong'), ('葵涌', 'Kwai Chung'), '羅湖', ('天水圍', 'Tin Shui Wai'), '流浮山', ('馬鞍山', 'Ma On Shan'), ('將軍澳', 'Tseung Kwan O'), '落馬洲'],
            ('離島', 'Outlying Islands') : ['大澳', '坪洲', ('東涌', 'Tung Chung'), '長洲', '大嶼山', ('赤鱲角', 'Chek Lap Kok'), '南丫島', '愉景灣', '蒲苔島'],
        }

        for k, v in area.items():
            dis = District(name = unicode(k[1]), name_tc = unicode(k[0]))
            DBSession.add(dis)
            for d in v :
                if type(d) == tuple:
                    DBSession.add(Area(name = unicode(d[0]), name_tc = unicode(d[1]), district = dis))
                else:
                    DBSession.add(Area(name = unicode(d), district = dis))




        DBSession.commit()
    except:
        traceback.print_exc()
        DBSession.rollback()

if __name__ == '__main__':
    print "start"
    init()
    print "finish"
