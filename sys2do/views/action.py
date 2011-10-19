# -*- coding: utf-8 -*-
'''
Created on 2011-5-4

@author: cl.lam
'''
from datetime import datetime as dt, timedelta
import calendar, traceback
from webhelpers.paginate import Page
import pymongo
from flask import g, render_template, flash, session, redirect, url_for, request
from flask import current_app as app
from flask.helpers import jsonify

from sys2do.model import connection
from sys2do.util.decorator import templated, login_required


@login_required
@templated("list_clinic.html")
def list_clinic():
    try:
        page = request.values.get("page", 1)
    except:
        page = 1
    cs = list(connection.Clinic.find({'active':0}).sort('name'))
    paginate_clinics = Page(cs, page = page, items_per_page = 10, url = lambda page:"%s?page=%d" % (url_for("list_clinic"), page))
    return {"clinics" :paginate_clinics}


@login_required
@templated("list_doctors.html")
def list_doctors():
    id = request.values.get("id", None)
    if not id:
        dps = connection.DoctorProfile.find({'active':0})
        data = [dp.populate() for dp in dps]
    else:
        c = connection.Clinic.one({'active':0, 'id':int(id)})
        data = [connection.DoctorProfile.one({'id':i}).populate() for i in c.doctors]
    return {"doctors" : data}


@login_required
def list_doctors_by_clinic():
    id = request.values.get("id", None)
    if not id:
        flash("No clinic supplied !")
        return redirect(url_for("index"))
    else:
        c = connection.Clinic.one({'active':0, 'id':int(id)})
        data = [connection.DoctorProfile.one({'id':i})for i in c.doctors]

    return render_template("list_doctors_by_clinic.html", doctors = data, clinic = c)


@login_required
def schedule():
    id = request.values.get("id", None)
    if not id :
        flash("No doctor id is supplied!", "WARNING")
        return redirect("/index")

    dp = connection.DoctorProfile.one({'id':int(id)})
    year = int(request.values.get("y", dt.now().year))
    month = int(request.values.get("m", dt.now().month))
    current = dt(year, month, 15)
    pre = current - timedelta(days = 30)
    next = current + timedelta(days = 30)
    calendar.setfirstweekday(6)

    es = connection.Events.find({'active':0,
                                  'did':int(id),
                                  'date':{'$gt':current.strftime('%Y%m'), '$lt':next.strftime('%Y%m')}
                                  }).sort("date")
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
            if e.uid == session['user_profile']['id']:
                info['is_booked'] = True
                info['event_time'] = e.time
                break

        if d < dt.today().date():
            info['avaiable'] = False
        elif d.strftime("%Y%m%d") in dp.worktime_setting["SPECIAL"]:
            info['avaiable'] = False
        elif connection.Holiday.isHoliday(d):
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

    doctor = connection.DoctorProfile.one({"id" : int(pdoctor)})
    require_date = dt.strptime(pdate, "%Y%m%d")

    day = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"][require_date.weekday()]
    time_spans = {}
    for setting in doctor.worktime_setting[day]:
        begin, end = setting['times']

        app.logger.info(setting)
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


    for e in connection.Events.find({"active":0, "did" : int(pdoctor), "date" : pdate}):
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
        e = connection.Events()
        e.id = e.getID()
        e.uid = int(uid)
        e.did = int(did)
        e.date = d
        e.time = t
        e.remark = request.values.get("remark", None)
        e.save()

        doctor = connection.DoctorProfile.one({'id':int(did)}).populate()
        m = connection.Message()
        m.id = m.getID()
        m.subject = u'Booking request submit'
        m.uid = session['user_profile']['id']
        m.content = u'%s make a booking with doctor %s at %s , %s.' % (session['user_profile']['name'], doctor['name'], t, format_date(d))
        m.save()

        return jsonify({
                        "success" : True,
                        "message" : "Save your request successfully !",
                        "event_time" : e.time,
                        })
    except:
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

    events = list(connection.Events.find({'active':0, 'uid':id}).sort("date"))
    paginate_events = Page(events, page = page, items_per_page = 20, url = lambda page:"%s?page=%d" % (url_for("my_booking"), page))
    return render_template("/my_booking.html", events = paginate_events)



@login_required
def my_message():
    try:
        page = request.values.get("page", 1)
    except:
        page = 1
    id = session['user_profile']['id']

    msgs = list(connection.Message.find({'active':0, 'uid':id}).sort("create_time", pymongo.DESCENDING))
    paginate_msgs = Page(msgs, page = page, items_per_page = 20, url = lambda page:"%s?page=%d" % (url_for("my_message"), page))
    return render_template("/my_message.html", messages = paginate_msgs)
