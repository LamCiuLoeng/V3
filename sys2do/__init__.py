# -*- coding: utf-8 -*-

from flask import Flask, Module

__all__ = ["app"]

app = Flask(__name__, static_path = '/static')
app.config.from_object("sys2do.setting")

#if not app.debug:
#    import logging
#    from themodule import TheHandlerYouWant
#    file_handler = TheHandlerYouWant(...)
#    file_handler.setLevel(logging.WARNING)
#    app.logger.addHandler(file_handler)

if app.config.get("LOGGING_FILE", True):
    import logging, logging.handlers
    file_handler = logging.handlers.TimedRotatingFileHandler(app.config.get("LOGGING_FILE_PATH"), when = 'D', interval = 1, backupCount = 5, encoding = "utf-8", delay = False)
    file_handler.setLevel(app.config.get("LOGGING_LEVEL"))
    file_handler.setFormatter(logging.Formatter('''
    Message type:       %(levelname)s
    Location:           %(pathname)s:%(lineno)d
    Function:           %(funcName)s
    Time:               %(asctime)s
    Message:            %(message)s
    '''))
    app.logger.addHandler(file_handler)

#===============================================================================
# sys.py
#===============================================================================
import views.sys as s
for error_code in [403, 404, 500] : app.error_handler_spec[error_code] = s.error_page(error_code)


#===============================================================================
# api.sys
#===============================================================================
import views.api as api
app.add_url_rule("/api", view_func = api.doAction, methods = ['GET', 'POST'])
#===============================================================================
# root.py
#===============================================================================
import views.root as r
app.add_url_rule("/test", view_func = r.test)
app.add_url_rule("/", view_func = r.index)
app.add_url_rule("/index", view_func = r.index)
app.add_url_rule("/search", view_func = r.search)
app.add_url_rule("/login", view_func = r.login)
app.add_url_rule("/register", view_func = r.register)
app.add_url_rule("/check_email", view_func = r.check_email)
app.add_url_rule("/save_register", view_func = r.save_register, methods = ['POST'])
app.add_url_rule("/login_handler", view_func = r.login_handler, methods = ['GET', 'POST'])
app.add_url_rule("/logout_handler", view_func = r.logout_handler, methods = ['GET', 'POST'])
app.add_url_rule("/profile", view_func = r.profile)
app.add_url_rule("/save_profile", view_func = r.save_profile, methods = ['POST'])
app.add_url_rule("/change_password", view_func = r.change_password)
app.add_url_rule("/save_password", view_func = r.save_password, methods = ['POST'])
app.add_url_rule("/thumbnail", view_func = r.thumbnail)
app.add_url_rule("/ajax_thumbnail_file", view_func = r.ajax_thumbnail_file, methods = ['POST'])
app.add_url_rule("/trumbnail_save", view_func = r.trumbnail_save, methods = ['POST'])




import views.action as a
app.add_url_rule("/list_clinic", view_func = a.list_clinic)
app.add_url_rule("/list_doctors", view_func = a.list_doctors)
app.add_url_rule("/list_doctors_by_clinic", view_func = a.list_doctors_by_clinic)
app.add_url_rule("/schedule", view_func = a.schedule)
app.add_url_rule("/search", view_func = a.search, methods = ['GET', 'POST'])
app.add_url_rule("/get_date_info", view_func = a.get_date_info, methods = ['GET', 'POST'])
app.add_url_rule("/save_events", view_func = a.save_events, methods = ['GET', 'POST'])
app.add_url_rule("/my_booking", view_func = a.my_booking, methods = ['GET', 'POST'])
app.add_url_rule("/my_message", view_func = a.my_message, methods = ['GET', 'POST'])





import views.manage as m
app.add_url_rule("/m_clinic", view_func = m.m_clinic_list)
app.add_url_rule("/m_clinic_update", view_func = m.m_clinic_update)
app.add_url_rule("/m_clinic_save", view_func = m.m_clinic_save, methods = ['POST'])
app.add_url_rule("/m_doctor", view_func = m.m_doctor_list)
app.add_url_rule("/m_doctor_update", view_func = m.m_doctor_update)
app.add_url_rule("/m_doctor_save", view_func = m.m_doctor_save, methods = ['POST'])
app.add_url_rule("/m_nurse", view_func = m.m_nurse_list)
app.add_url_rule("/m_nurse_update", view_func = m.m_nurse_update)
app.add_url_rule("/m_nurse_save", view_func = m.m_nurse_save, methods = ['POST'])
app.add_url_rule("/m_user", view_func = m.m_user_list)
app.add_url_rule("/m_user_update", view_func = m.m_user_update)
app.add_url_rule("/m_events_list", view_func = m.m_events_list)
app.add_url_rule("/m_events_update", view_func = m.m_events_update)


#===============================================================================
# import the cuxtomize filter
#===============================================================================
import util.filters as filters
for f in filters.__all__ : app.jinja_env.filters[f] = getattr(filters, f)

import util.tests as tests
for t in tests.__all__ : app.jinja_env.tests[t] = getattr(tests, t)

#===============================================================================
# import the default env value
#===============================================================================
from util.master_helper import getDistrictInfo
app.jinja_env.globals['DISTRICT_INFO'] = getDistrictInfo()
