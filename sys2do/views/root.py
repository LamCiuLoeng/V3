# -*- coding: utf-8 -*-
import traceback
from PIL import Image
import os
from datetime import datetime as dt
from flask import g, render_template, flash, session, redirect, url_for, request

from sys2do import app
from sys2do.model import connection
from flask.helpers import jsonify
from sys2do.util.decorator import templated, login_required, has_all_permissions
from sys2do.util.common import _g, MESSAGE_ERROR, MESSAGE_INFO, upload
from sys2do.setting import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, UPLOAD_FOLDER_URL




@login_required
@templated("index.html")
def index():
    if 'login' not in session or not session['login']:
        return redirect(url_for('login'))
    user_profile = session['user_profile']
    app.logger.debug('A value for debugging')
    return {"user_profile" : user_profile}



@templated("login.html")
def login():
    if session.get('login', None):
        return redirect(url_for("index"))
    return {}


def login_handler():
    email = request.values.get('email', None)
    password = request.values.get('password', None)
    next = request.values.get('next', None)
    u = connection.User.one({'active' : 0, 'email':email, 'password':password})
    app.logger.info(next)
    if not u:
        flash("e-mail or password is not correct !")
        if next : return redirect(url_for("login", next = next))
        return redirect(url_for("login"))
    else:
        session['login'] = True
        session['user_profile'] = u.populate()
        roles = []
        permissions = set()
        for i in u.roles:
            r = connection.Role.one({"id" : i})
            roles.append(r.name)
            for pid in r.permissions:
                permissions.add(connection.Permission.one({"id" : pid}).name)
        session['user_profile']['roles'] = roles
        session['user_profile']['permissions'] = permissions
#        session.permanent = True
        app.logger.info("*********** permission")
        app.logger.info(roles)
        app.logger.info(permissions)
        if next:  return redirect(next)
        return redirect(url_for("index"))



def logout_handler():
    session.pop('login', None)
    return redirect("/login")


def search():
    q = request.values.get('q', None)
    r = connection.Role.one({"name":"DOCTOR"})
    contain = {"$regex" : "/.*%s.*/i" % q}
    contain = "/.*%s.*/i" % q
    #search the user
    us = connection.User.find({
                               'active' : 0,
                               'roles':{'$all':[r.id]},
                               '$or':[{'first_name' : contain},
#                                      {'last_name' : contain},
                                 ]
                          })
    data = [u.populate() for u in us]
    app.logger.info(data)
    return jsonify(data)

@templated("register.html")
def register():
    return {}

def save_register():
    u = connection.User.one({'active':0, 'email':_g("email")})
    if u :
        flash("The user has been already exist !", MESSAGE_ERROR)
        return redirect(url_for("register"))
    if _g("password") != _g("repassword"):
        flash("The password and confirmed password are not the same !", MESSAGE_ERROR)
        return redirect(url_for("register"))
    if not _g("first_name") or not _g("last_name"):
        flash("The first name or the last name is not supplied !", MESSAGE_ERROR)
        return redirect(url_for("register"))

    nu = connection.User()
    nu.id = nu.getID()
    nu.email = _g("email")
    nu.password = _g("password")
    nu.first_name = _g("first_name")
    nu.last_name = _g("last_name")
    nu.phone = _g("phone")
    nu.birthday = _g("birthday")

    r = connection.Role.one({"name" : "NORMALUSER"})
    nu.roles = [r.id]
    r.users = r.users + [nu.id]
    nu.save()
    r.save()

    flash("Register successfully", MESSAGE_INFO)
    return redirect(url_for("login"))


def check_email():
    u = connection.User.one({"active" : 0 , "email" : _g("email")})
    return jsonify({"is_exist" : bool(u)})

@templated("profile.html")
def profile():
    id = session['user_profile']["id"]
    u = connection.User.one({"id" : id})
    return {"user" : u}


def save_profile():
    id = session['user_profile']["id"]
    u = connection.User.one({"id" : id})
    u.first_name = _g("first_name")
    u.last_name = _g("last_name")
    u.phone = _g("phone")
    u.birthday = _g("birthday")
    try:
        f = upload("image_url")
        u.image_url = f.id
    except:
        app.logger.error(traceback.format_exc())
    u.save()
    flash("Update the profile successfully!", MESSAGE_INFO)
    return redirect(url_for("index"))


@login_required
@templated("change_password.html")
def change_password():
    id = session['user_profile']["id"]
    u = connection.User.one({"id" : int(id)})
    return {"user" : u}



@login_required
def save_password():
    id = session['user_profile']["id"]
    u = connection.User.one({"id" : int(id)})
    if u.password != _g("old_password", None):
        flash("Old Password is wrong", MESSAGE_ERROR)
        return redirect(url_for("change_password"))

    if not _g("new_password", None):
        flash("The new password could not be blank", MESSAGE_ERROR)
        return redirect(url_for("change_password"))
    if _g("new_password", None) != _g("new_repassword", None):
        flash("The new password and the confirm password are not the same !", MESSAGE_ERROR)
        return redirect(url_for("change_password"))

    u.password = _g("new_password")
    u.save()
    flash("Update the password successfully !", MESSAGE_INFO)
    return redirect(url_for("change_password"))




@login_required
@templated("thumbnail.html")
def thumbnail():
    id = session['user_profile']["id"]
    u = connection.User.one({"id" : int(id)})

    image = u.getImage()
    if image:
        f = Image.open(image.path)
        data = {
                "image_id" : image.id,
                "image_url" : image.url,
                "image_size" : f.size,
                }
#        f.close()
        return {"data" : data}
    else:
        return {"data" : {}}



@login_required
@templated("thumbnail.html")
def ajax_thumbnail_file():
    try:
        f = upload("fileToUpload")
        i = Image.open(f.path)
        data = {
                "image_id" : f.id,
                "image_url" : f.url,
                "image_size" : i.size,
                }
#        i.close()
        return {"data" : data}
    except:
        app.logger.error(traceback.format_exc())
        return {"data" : {}}


@login_required
def trumbnail_save():
    image_id = request.values.get("image_id", None)
    if not image_id:
        flash("No image upload", MESSAGE_ERROR)
        return redirect(url_for("thumbnail"))

    left = request.values.get("x1", None)
    top = request.values.get("y1", None)
    right = request.values.get("x2", None)
    bottom = request.values.get("y2", None)

    if not all([left, top, right, bottom]):
        flash("No all the params supplied", MESSAGE_ERROR)
        return redirect(url_for("thumbnail"))

    left, top, right, bottom = map(int, (left, top, right, bottom))


    infile = connection.UploadFile.one({"id" : int(image_id)})
    outfile = connection.UploadFile()

    outfile.id = outfile.getID()
    outfile.name = infile.name
    outfile.uid = session['user_profile']["id"]

    new_file_name = "%s%s" % (dt.now().strftime("%Y%m%d%H%M%S"), os.path.splitext(infile.path)[1])
    outfile.path = os.path.join(UPLOAD_FOLDER, new_file_name)
    outfile.url = "/".join([UPLOAD_FOLDER_URL, new_file_name])
    outfile.save()



    im = Image.open(infile.path)
    thumbnail = im.crop((left, top, right, bottom))
    thumbnail.save(outfile.path)

    id = session['user_profile']["id"]
    u = connection.User.one({"id" : int(id)})
    u.image_url = outfile.id
    u.save()

    flash("Upldate the profile successfully!")
    return redirect(url_for("profile"))



@templated("test.html")
def test():
    return {}
