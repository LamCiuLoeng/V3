# -*- coding: utf-8 -*-
'''
Created on 2011-5-4

@author: cl.lam
'''
from datetime import datetime as dt, timedelta
import calendar, traceback
from webhelpers.paginate import Page
from sqlalchemy.sql.expression import and_, desc
#import pymongo
from flask import g, render_template, flash, session, redirect, url_for, request
from flask import current_app as app
from flask.helpers import jsonify

from sys2do.model import DBSession, Clinic
from sys2do.util.decorator import templated, login_required
from sys2do.model.logic import DoctorProfile, Events, Holiday, Message

ITEM_PER_PAGE = 20

@login_required
@templated("list_clinic.html")
def list_clinic():
    try:
        page = request.values.get("page", 1)
    except:
        page = 1
    cs = DBSession.query(Clinic).filter(Clinic.active == 0).order_by(Clinic.name)
    paginate_clinics = Page(cs, page = page, items_per_page = 5, url = lambda page:"%s?page=%d" % (url_for("list_clinic"), page))
    return {"clinics" :paginate_clinics}


@login_required
@templated("list_doctors.html")
def list_doctors():
    id = request.values.get("id", None)
    if not id:
        dps = DBSession.query(DoctorProfile).filter(DoctorProfile.active == 0)
#        dps = connection.DoctorProfile.find({'active':0})
        data = [dp.populate() for dp in dps]
    else:
        c = DBSession.query(Clinic).get(id)
#        c = connection.Clinic.one({'active':0, 'id':int(id)})
#        data = [connection.DoctorProfile.one({'id':i}).populate() for i in c.doctors]
        data = [i.populate() for i in c.doctors]
    return {"doctors" : data}


@login_required
def list_doctors_by_clinic():
    id = request.values.get("id", None)
    if not id:
        flash("No clinic supplied !")
        return redirect(url_for("index"))
    else:
        c = DBSession.query(Clinic).get(id)

    return render_template("list_doctors_by_clinic.html", doctors = c.doctors, clinic = c)


@login_required
def schedule():
    id = request.values.get("id", None)
    if not id :
        flash("No doctor id is supplied!", "WARNING")
        return redirect("/index")

    year = int(request.values.get("y", dt.now().year))
    month = int(request.values.get("m", dt.now().month))
    current = dt(year, month, 15)
    pre = current - timedelta(days = 30)
    next = current + timedelta(days = 30)
    calendar.setfirstweekday(6)

    dp = DBSession.query(DoctorProfile).get(id)
    es = DBSession.query(Events).filter(and_(Events.active == 0, Events.doctor_id == id,
                                             Events.date > current.strftime('%Y%m'), Events.date < next.strftime('%Y%m'))).order_by(Events.date)

    events = {}
    for b in es:
        if b.date in events:
            events[b.date].append(b)
        else:
            events[b.date] = [b]

    s = []
    days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    for d in calendar.Calendar().itermonthdates(year, month):
        info = {
                "date" : d,
                "this_month" : True,
                "is_booked" : False,
                "event_time" : None,
                "holiday" : False,
                "avaiable" : False,
                }
        if d.month != month:
            info['this_month'] = False
            s.append(info)
            continue

        info['this_month'] = True
        info['events'] = events[d.strftime("%Y%m%d")] if d.strftime("%Y%m%d") in events else []
        for e in info['events']:
            if e.user_id == session['user_profile']['id']:
                info['is_booked'] = True
                info['event_time'] = e.time
                break

        if d < dt.today().date():
            info['avaiable'] = False
        elif d.strftime("%Y%m%d") in dp.worktime_setting["SPECIAL"]:
            info['avaiable'] = False
        elif Holiday.isHoliday(d):
            ws = dp.worktime_setting["HOLIDAY"]
            info['avaiable'] = len(ws) > 0
            info['holiday'] = True
        else:
            ws = dp.worktime_setting[days[d.weekday()]]
            info['avaiable'] = len(ws) > 0

        s.append(info)
    return render_template("/schedule.html", schedule = s, doctor = dp, current = current, pre = pre, next = next)





@login_required
def get_date_info():
    pdate = request.values.get("pdate", None)
    pdoctor = request.values.get("pdoctor", None)
    if not pdate or not pdoctor:
        return jsonify({"success" : False, "message" : "No date or doctor supplied!"})

    doctor = DBSession.query(DoctorProfile).get(pdoctor)
    require_date = dt.strptime(pdate, "%Y%m%d")
    day = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"][require_date.weekday()]
    time_spans = {}
    for setting in doctor.worktime_setting[day]:
        begin, end = setting['times']
        bHour, bEnd = begin.split(":")
        eHour, eEnd = end.split(":")

        if bHour == eHour:
            time_spans[bHour] = [begin, end, setting['seats'], 0]
        else:
            h1 = int(bHour)
            h2 = int(eHour)
            for h in range(h1 + 1, h2):
                time_spans[h] = [("0%d:00" % h)[-5:], ("0%d:00" % (h + 1))[-5:], 0, 0]
            if eEnd != "00":
                time_spans[h2] = [("0%d:00" % h2)[-5:], end, 0, 0]
            time_spans[h1] = [begin, ("0%d:00" % (h1 + 1))[-5:], 0, 0]

            spans = sorted(time_spans.keys())
            for i in range(setting['seats']) : time_spans[spans[i % len(spans)]][2] += 1

    for e in DBSession.query(Events).filter(and_(Events.active == 0, Events.doctor_id == pdoctor, Events.date == pdate)):

        h, m = e.time.split(":")
        if int(h) in time_spans:
            time_spans[int(h)][3] += 1

    return jsonify({
                    "success" : True,
                    "time_spans" : time_spans
                    })





@login_required
def save_events():
    uid = request.values.get("uid", None)
    did = request.values.get("did", None)
    d = request.values.get("d", None)
    t = request.values.get("t", None)

    if not uid or not did or not d or not t:
        return jsonify({
                        "success" : False,
                        "message" : "The required info is not supplied !"
                        })
    format_date = lambda v : "-".join([v[:4], v[4:6], v[-2:]])

    try:
        e = Events(user_id = uid, doctor_id = did, date = d, time = t, remark = request.values.get("remark", None))
        DBSession.add(e)
        doctor = DBSession.query(DoctorProfile).get(did).getUserProfile()
        m = Message(subject = u'Booking request submit', user_id = session['user_profile']['id'],
                    content = u'%s make a booking with doctor %s at %s , %s.' % (session['user_profile']['name'], doctor['name'], t, format_date(d)))
        DBSession.add(m)
        DBSession.commit()
        return jsonify({
                        "success" : True,
                        "message" : "Save your request successfully !",
                        "event_time" : e.time,
                        })
    except:
        DBSession.rollback()
        app.logger.error(traceback.format_exc())
        return jsonify({
                        "success" : False,
                        "message" : "Error occur when submiting the request !"
                        })


@login_required
def my_booking():
    try:
        page = request.values.get("page", 1)
    except:
        page = 1
    id = session['user_profile']['id']

    events = DBSession.query(Events).filter(and_(Events.active == 0, Events.user_id == id)).order_by(Events.date).all()
    paginate_events = Page(events, page = page, items_per_page = 20, url = lambda page:"%s?page=%d" % (url_for("my_booking"), page))
    return render_template("/my_booking.html", events = paginate_events)



@login_required
def my_message():
    try:
        page = request.values.get("page", 1)
    except:
        page = 1
    id = session['user_profile']['id']

    msgs = DBSession.query(Message).filter(and_(Message.active == 0, Message.user_id == id)).order_by(desc(Message.create_time)).all()

#    msgs = list(connection.Message.find({'active':0, 'uid':id}).sort("create_time", pymongo.DESCENDING))
    paginate_msgs = Page(msgs, page = page, items_per_page = 20, url = lambda page:"%s?page=%d" % (url_for("my_message"), page))
    return render_template("/my_message.html", messages = paginate_msgs)


@login_required
def search():
    d = request.values.get("d", '')
    q = request.values.get("q", '')
    try:
        page = request.values.get("page", 1)
    except:
        page = 1

    if not d:
        cs = DBSession.query(Clinic).filter(and_(Clinic.active == 0, Clinic.name.op("like")("%%%s%%" % q))).all()
    else:
        cs = DBSession.query(Clinic).filter(and_(Clinic.active == 0, Clinic.name.op("like")("%%%s%%" % q))).all()

    paginate_clinics = Page(cs, page = page, items_per_page = ITEM_PER_PAGE, url = lambda page:"%s?d=%s&q=%s&page=%d" % (url_for("search"), d or '', q or '', page))
    return render_template("search.html", paginate_clinics = paginate_clinics, q = q or '', d = d or '')
