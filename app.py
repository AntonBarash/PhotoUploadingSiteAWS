######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
# Edited to create photo-uploading localhost by: Anton Barash <antonbar@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login
import datetime
from datetime import date

#for image uploading
import os, base64
mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'pass1234'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'database-2.cdwkgehsrjdn.us-east-2.rds.amazonaws.com'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()
cursor.close()

def getUserList():
        conn.ping(reconnect=True)
        cursor = conn.cursor()
        cursor.execute("SELECT email from Users")
        ret = cursor.fetchall()
        cursor.close()
        return ret

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = conn.cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	cursor.close()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='email' name='email' id='email' placeholder='email' required='true'></input>
				<input type='password' name='password' id='password' placeholder='password' required='true'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in useruploadupload
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file
	cursor.close()

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register1", methods=['GET'])
def register1():
    return render_template('register.html')

@app.route("/register", methods=['POST'])
def register_user():
    try:
        email=request.form.get('email')
        password=request.form.get('password')
        fname=request.form.get('fname')
        lname=request.form.get('lname')
        DOB=request.form.get('DOB')
        hometown=request.form.get('hometown')
        gender=request.form.get('gender')
        if len(fname.split()) == 0 or len(lname.split()) == 0 or len(password.split()) == 0:
                return render_template('register.html', supress = True, message = "Please input actual text for fname, lname, and password! One of those is missing it!")
    except:
        print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for('register'))
    test = isEmailUnique(email)
    if test:
        cursor = conn.cursor()    
        cursor.execute("INSERT INTO Users (email, password, fname, lname, DOB, hometown, gender) VALUES ('{0}', '{1}', '{2}', '{3}','{4}', '{5}', '{6}')".format(email, password, fname, lname, DOB, hometown, gender))
        conn.commit()
        cursor.close()
        #log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('hello.html', name=email, message='Account Created!')
    else:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('register1'))



def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, photo_id, caption FROM Photos WHERE user_id = '{0}'".format(uid))
	cursor.close()
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	cursor.close()
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
                cursor.close()
		#this means there are greater than zero entries with that email
                return False
	else:
                cursor.close()
                return True
#end login code

def isTagUnique(tag):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT T.tag_name FROM Tags T WHERE T.tag_name = '{0}'".format(tag)):
                cursor.close()
		#this means there are greater than zero entries with that email
                return False
	else:
                cursor.close()
                return True
#end login code

def getFriendList(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT U2.fname, U2.lname FROM Users U1, Users U2, Friends F WHERE U1.user_id = '{0}' AND F.user_id1 = U1.user_id AND F.user_id2 = U2.user_id".format(uid))
	return cursor.fetchall()

def getAlbumList(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT A.name, A.albums_id FROM Albums A WHERE A.user_id = '{0}'".format(uid))
	cursor.close()
	return cursor.fetchall()

def getAlbumPhotos(uid, aid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, photo_id, caption, albums_id FROM Photos WHERE user_id = '{0}' AND albums_id = '{1}'".format(uid,aid))
	cursor.close()
	return cursor.fetchall()

def getTags(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT DISTINCT T.tag_name, T.tag_id FROM Tags T, Tagged T1, Photos P WHERE T.tag_id = T1.tag_id AND P.photo_id = T1.photo_id AND P.user_id = '{0}'".format(uid))
	cursor.close()
	return cursor.fetchall()

def getUserTagPhotos(uid,tagid):
        cursor = conn.cursor()
        cursor.execute("SELECT P.imgdata, P.photo_id, P.caption FROM Photos P, Tagged T1 WHERE P.user_id = '{0}' AND T1.photo_id = P.photo_id AND T1.tag_id = '{1}'".format(uid,tagid))
        cursor.close()
        return cursor.fetchall()

def getAllTagPhotos(tagid):
        cursor = conn.cursor()
        cursor.execute("SELECT P.imgdata, P.photo_id, P.caption, P.albums_id, P.user_id FROM Photos P, Tagged T1 WHERE T1.photo_id = P.photo_id AND T1.tag_id = '{0}'".format(tagid))
        cursor.close()
        return cursor.fetchall()

def getRecommendedFriendList(uid):
	cursor = conn.cursor()
	cursor.execute("""SELECT Count(*) counter, F2.user_id2, U3.email
        FROM Users U1, Users U2, Users U3, Friends F1, Friends F2
        WHERE U1.user_id = '{0}' AND F1.user_id1 = '{0}' AND U2.user_id = F1.user_id2 AND U2.user_id = F2.user_id1 AND U3.user_id = F2.user_id2 AND '{0}' <> F2.user_id2 AND F2.user_id2 NOT IN 
        (SELECT user_id2 FROM Friends WHERE user_id1 = '{0}')
        GROUP BY F2.user_id2
        ORDER BY counter DESC
        """.format(uid))
	cursor.close()
	return cursor.fetchall()

def getTagList(photoid):
        cursor = conn.cursor()
        cursor.execute("SELECT T.tag_name FROM Tags T, Tagged T1 WHERE T.tag_id = T1.tag_id AND T1.photo_id = '{0}'".format(photoid))
        cursor.close()
        return cursor.fetchall()

def getPhotoList(albumid):
        cursor = conn.cursor()
        cursor.execute("SELECT photo_id FROM Photos WHERE albums_id = '{0}'".format(albumid))
        cursor.close()
        return cursor.fetchall()

def getTagDict(albumid):
        photos = getPhotoList(albumid)
        tag = {}
        for photoid in photos:
                tag[photoid[0]] = getTagList(photoid[0])
        return tag

#this one is for when you get dictionary of tags of 
def getTagDictUsingTag(uid,tagid):
        photos = getUserTagPhotos(uid,tagid)
        tag = {}
        for photoid in photos:
                tag[photoid[1]] = getTagList(photoid[1])
        return tag

def getTagDictUsingPhotos(photos):
        tag = {}
        for photoid in photos:
                tag[photoid[1]] = getTagList(photoid[1])
        return tag

def getCommentDictUsingPhotos(photos):
        comment = {}
        for photoid in photos:
                comment[photoid[1]] = getCommentList(photoid[1])
        return comment

def getCommentList(photoid):
        cursor = conn.cursor()
        cursor.execute("SELECT U.fname, U.lname, C.date, C.text FROM Users U, Comments C WHERE U.user_id = C.user_id AND C.photo_id = '{0}'".format(photoid))
        cursor.close()
        return cursor.fetchall()

def getCommentDict(albumid):
        photos = getPhotoList(albumid)
        comment = {}
        for photoid in photos:
                comment[photoid[0]] = getCommentList(photoid[0])
        return comment

def getCommentDictUsingTag(uid,tagid):
        photos = getUserTagPhotos(uid,tagid)
        comment = {}
        for photoid in photos:
                comment[photoid[1]] = getCommentList(photoid[1])
        return comment

def getUsersFromComment(comment):
        cursor = conn.cursor()
        cursor.execute("SELECT U.fname, U.lname, COUNT(*) FROM Users U, Comments C WHERE U.email is NOT NULL AND U.user_id = C.user_id AND C.text = '{0}' GROUP BY U.user_id".format(comment))
        cursor.close()
        return cursor.fetchall()

def getAllTags():
        cursor = conn.cursor()
        cursor.execute("SELECT tag_name, tag_id FROM Tags")
        cursor.close()
        return cursor.fetchall()

def getPopularTags():
        cursor = conn.cursor()
        cursor.execute("""SELECT T.tag_name, T.tag_id
        FROM Tags T
        WHERE 
        (SELECT COUNT(*)
        FROM Tagged T1
        WHERE T.tag_id = T1.tag_id) =
        (SELECT COUNT(*)
	FROM Tagged T2, Tags T3
	WHERE T2.tag_id = T3.tag_id
        GROUP BY T2.tag_id
        ORDER BY COUNT(*) DESC
        LIMIT 1)""")
        cursor.close()
        return cursor.fetchall()

def getLikesDict():
        cursor = conn.cursor()
        cursor.execute("SELECT photo_id FROM Photos")
        photos = cursor.fetchall()
        likes = {}
        for photoid in photos:
                cursor.execute("SELECT Count(*) FROM Likes L WHERE (%s) = L.photo_id", (photoid))
                numoflikes = cursor.fetchall()[0][0]
                cursor.execute("SELECT U.fname, U.lname FROM Users U, Likes L WHERE (%s) = L.photo_id AND U.user_id = L.user_id", (photoid))
                listofusers = cursor.fetchall()
                likes[photoid] = [numoflikes, listofusers]
        cursor.close()
        return likes

def getUserPopularTags():
        uid = getUserIdFromEmail(flask_login.current_user.id)
        cursor = conn.cursor()
        cursor.execute("""SELECT T.tag_name, T.tag_id, COUNT(*) counter
        FROM Tags T, Photos P, Tagged T1
        WHERE P.user_id = (%s) AND T1.photo_id = P.photo_id AND T1.tag_id = T.tag_id
        GROUP BY T.tag_id
        ORDER BY counter DESC
        LIMIT 5""",(uid))
        cursor.close()
        return cursor.fetchall()

def getRecommendedPhotos():
        uid = getUserIdFromEmail(flask_login.current_user.id)
        tags = getUserPopularTags()
        try:
                t1 = tags[0][1]
        except:
                t1 = None
        try:
                t2 = tags[1][1]
        except:
                t2 = None
        try:
                t3 = tags[2][1]
        except:
                t3 = None
        try:
                t4 = tags[3][1]
        except:
                t4 = None
        try:
                t5 = tags[4][1]
        except:
                t5 = None
        cursor = conn.cursor()
        cursor.execute("""SELECT P.imgdata, P.photo_id, P.caption, COUNT(*) counter, P.user_id
        FROM Photos P, Tagged T1
        WHERE (T1.tag_id = (%s) OR T1.tag_id = (%s) OR T1.tag_id = (%s) OR T1.tag_id = (%s) OR T1.tag_id = (%s)) AND T1.photo_id = P.photo_id AND P.user_id <> (%s) AND (%s) NOT IN
        (SELECT L.user_id
        FROM Likes L
        WHERE L.photo_id = P.photo_id)
        GROUP BY P.photo_id
        ORDER BY counter DESC""",(t1,t2,t3,t4,t5,uid,uid))
        cursor.close()
        return cursor.fetchall()

def getContributionScore(uid):
        cursor = conn.cursor()
        cursor.execute("""SELECT (SELECT COUNT(*) FROM Photos P, Users U WHERE P.user_id = (%s) AND U.user_id = (%s) AND U.email is NOT NULL) + (SELECT COUNT(*) FROM Comments C, Users U WHERE C.user_id = (%s) AND U.user_id = (%s) AND U.email is NOT NULL) AS COUNTER""",(uid,uid,uid,uid))
        cursor.close()
        return cursor.fetchall()[0][0]

def getAllUsers():
        cursor = conn.cursor()
        cursor.execute("""SELECT user_id, fname, lname FROM Users""")
        cursor.close()
        return cursor.fetchall()

def getLeaderboardDict():
        users = getAllUsers()
        scores = []
        for user in users:
                cscore = getContributionScore(user[0])
                scores.append([user[1],user[2],cscore,user[0]])
        scores = sorted(scores, key=lambda x: x[2], reverse=True)
        leaderboard = {}
        i = 1
        index = 0
        cursor = conn.cursor()
        while i < 11 and index < len(scores):
                uid = scores[index][3]
                cursor.execute("SELECT email FROM Users WHERE user_id = (%s)",(uid))
                email = cursor.fetchall()[0][0]
                if email == None:
                        index = index + 1
                else:
                        leaderboard[i] = scores[index]
                        i = i + 1
                        index = index + 1
        cursor.close()
        return leaderboard

def getTagsFromPhoto(pid):
        cursor = conn.cursor()
        cursor.execute("SELECT T.tag_name FROM Tagged T1, Tags T WHERE T.tag_id = T1.tag_id AND T1.photo_id = (%s)",(pid))
        cursor.close()
        return cursor.fetchall()

def getPhotosFromMultiTags(multitags):
        tags = multitags.split()
        cursor = conn.cursor()
        cursor.execute("SELECT tag_id FROM Tags WHERE tag_name = (%s)",(tags[0]))
        cursor.close()
        try:
                tempphotos = getAllTagPhotos(cursor.fetchall()[0][0])
        except:
                tempphotos = []
        photos = []
        for photo in tempphotos:
                for i in range(len(tags)):
                        for tagged in getTagsFromPhoto(photo[1]):
                                tag = tags[i]
                                if tagged[0] == tag:
                                        if i == len(tags) - 1:
                                                photos.append(photo)
                                        else:
                                                break
                                else:
                                        continue
        return multitags, photos

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
        uid = getUserIdFromEmail(flask_login.current_user.id)
        if request.method == 'POST':
                albumid = request.form.get('aid')
                photoid = request.form.get('pid')
                if photoid != None:
                        albumid = request.form.get('aidinphoto')
                        tag = request.form.get('tag')
                        try:
                                tagname = tag.split()[0]
                        except:
                                return render_template('upload.html', message = 'You have to input text for the tag it cant just be spaces!', tags = getTags(uid), likes = getLikesDict(), commentdict = getCommentDict(albumid), viewalbum=getAlbumPhotos(uid, albumid), albums=getAlbumList(uid), tagdict = getTagDict(albumid), base64=base64)
                        message = None
                        if isTagUnique(tagname):
                                cursor = conn.cursor()
                                cursor.execute('''INSERT INTO Tags (tag_name) VALUES (%s)''' ,(tagname))
                                cursor.close()
                        cursor = conn.cursor()
                        cursor.execute("SELECT T.tag_id FROM Tags T WHERE T.tag_name = '{0}'".format(tagname))
                        tagid = cursor.fetchall()
                        try:
                                cursor.execute('''INSERT INTO Tagged (photo_id, tag_id) VALUES (%s, %s)''' ,(photoid, tagid))
                        except:
                                message = "You've already applied this tag to this photo!"
                        conn.commit()
                        cursor.close()
                        return render_template('upload.html', message = message, tags = getTags(uid), likes = getLikesDict(), commentdict = getCommentDict(albumid), viewalbum=getAlbumPhotos(uid, albumid), albums=getAlbumList(uid), tagdict = getTagDict(albumid), base64=base64)
                else:
                        caption = request.form.get('caption')
                        album = request.form.get('album')
                        if len(caption.split()) == 0:
                                viewalbum = getAlbumPhotos(uid,albumid)
                                if len(viewalbum) == 0:
                                        return render_template('upload.html', message = "Your caption cannot be just spaces! ;(", tags = getTags(uid), albums=getAlbumList(uid), zero = albumid) 
                                return render_template('upload.html', message = "Your caption cannot be just spaces! ;(", tags = getTags(uid), likes = getLikesDict(), viewalbum=getAlbumPhotos(uid, albumid), albums=getAlbumList(uid), commentdict = getCommentDict(albumid), tagdict = getTagDict(albumid), base64=base64) 
                        imgfile = request.files['photo']
                        photo_data = imgfile.read()
                        cursor = conn.cursor()
                        cursor.execute('''INSERT INTO Photos (imgdata, user_id, caption, albums_id) VALUES (%s, %s, %s, %s)''' ,(photo_data,uid, caption, albumid))
                        conn.commit()
                        cursor.close()
                        return render_template('upload.html', tags = getTags(uid), likes = getLikesDict(), viewalbum=getAlbumPhotos(uid, albumid), albums=getAlbumList(uid), commentdict = getCommentDict(albumid), tagdict = getTagDict(albumid), base64=base64)
        #The method is GET so we return a  HTML form to upload the a photo.
        else:
                #setAlbumId(request.args.get('para'))
                albumid = request.args.get('para')
                tagid = request.args.get('tpara')
                likes = getLikesDict()
                if albumid != None:
                        if getAlbumPhotos(uid, albumid) == ():
                                return render_template('upload.html', tags = getTags(uid), zero = albumid, albums=getAlbumList(uid))
                        return render_template('upload.html', likes = likes, tags = getTags(uid), viewalbum=getAlbumPhotos(uid, albumid), albums=getAlbumList(uid), commentdict = getCommentDict(albumid), tagdict = getTagDict(albumid), base64=base64)
                elif tagid != None:
                        return render_template('upload.html', tags = getTags(uid), likes = likes, viewtag=getUserTagPhotos(uid, tagid), albums=getAlbumList(uid), commentdict2 = getCommentDictUsingTag(uid,tagid), tagdict2 = getTagDictUsingTag(uid,tagid), base64=base64)
                else:
                        return render_template('upload.html', tags = getTags(uid), albums=getAlbumList(uid))

@app.route('/search', methods=['POST'])
def search():
        if request.form.get('uemail') != None:
                try:
                        uid = getUserIdFromEmail(request.form.get('uemail'))
                except:
                        return render_template('search.html', message='A user with that email doesnt exist, please put in an email of a user that does exist!', taglist = getAllTags(), ptaglist = getPopularTags())
                if len(getAlbumList(uid)) != 0:
                        return render_template('search.html', founduser = uid, albums=getAlbumList(uid), taglist = getAllTags(), ptaglist = getPopularTags())
                else:
                        return render_template('search.html', message='This user has no albums! ;(', taglist = getAllTags(), ptaglist = getPopularTags())
        elif request.form.get('commenttext') != None:
                users = getUsersFromComment(request.form.get('commenttext'))
                if len(users) != 0:
                        return render_template('search.html', taglist = getAllTags(), foundcomment = users, ptaglist = getPopularTags())
                else:
                        return render_template('search.html', message='No users have made this comment ;(', taglist = getAllTags(), ptaglist = getPopularTags())

@app.route('/recommended', methods=['GET'])
@flask_login.login_required
def recommended():
        photos = getRecommendedPhotos()
        if len(photos) == 0:
                        return render_template('search.html', message = 'You have no recommended photos', taglist = getAllTags(), ptaglist = getPopularTags())
        return render_template('search.html', likes = getLikesDict(), taglist = getAllTags(), recphotos = photos, tagdict = getTagDictUsingPhotos(photos), commentdict = getCommentDictUsingPhotos(photos), base64=base64, ptaglist = getPopularTags())

@app.route('/like', methods=['POST'])
@flask_login.login_required
def like():
        photoid = request.form.get('lbutton')
        uid = getUserIdFromEmail(flask_login.current_user.id)
        albumid = request.form.get('aid')
        tagid = request.form.get('tid')
        multitags = request.form.get('mtid')
        cursor = conn.cursor()
        try:
                cursor.execute("INSERT INTO Likes (user_id, photo_id) VALUES (%s, %s)",(uid, photoid))
                conn.commit()
                cursor.close()
        except:
                cursor.close()
                if albumid != None:
                        return render_template('search.html', likes = getLikesDict(), message = "You have already liked this photo!", founduser = uid, commentdict = getCommentDict(albumid), viewalbum=getAlbumPhotos(uid, albumid), albums=getAlbumList(uid), tagdict = getTagDict(albumid), base64=base64, taglist = getAllTags(), ptaglist = getPopularTags())
                elif multitags != None:
                        multitags, photos = getPhotosFromMultiTags(multitags)
                        return render_template('search.html', likes = getLikesDict(), message = "You have already liked this photo!", multitags = multitags, viewmultitags = photos, commentdict = getCommentDictUsingPhotos(photos), tagdict = getTagDictUsingPhotos(photos), base64=base64, taglist = getAllTags(), ptaglist = getPopularTags())
                else:
                        photos = getAllTagPhotos(tagid)
                        return render_template('search.html', likes = getLikesDict(), message = "You have already liked this photo!", foundtag = tagid, commentdict = getCommentDictUsingPhotos(photos), viewtags=photos, tagdict = getTagDictUsingPhotos(photos), base64=base64, taglist = getAllTags(), ptaglist = getPopularTags())
        if albumid != None:
                return render_template('search.html', likes = getLikesDict(), founduser = uid, commentdict = getCommentDict(albumid), viewalbum=getAlbumPhotos(uid, albumid), albums=getAlbumList(uid), tagdict = getTagDict(albumid), base64=base64, taglist = getAllTags(), ptaglist = getPopularTags())
        elif tagid != None:
                photos = getAllTagPhotos(tagid)
                return render_template('search.html', likes = getLikesDict(), foundtag = tagid, commentdict = getCommentDictUsingPhotos(photos), viewtags=photos, tagdict = getTagDictUsingPhotos(photos), base64=base64, taglist = getAllTags(), ptaglist = getPopularTags())
        elif multitags != None:
                multitags, photos = getPhotosFromMultiTags(multitags)
                return render_template('search.html', likes = getLikesDict(), multitags = multitags, viewmultitags = photos, commentdict = getCommentDictUsingPhotos(photos), tagdict = getTagDictUsingPhotos(photos), base64=base64, taglist = getAllTags(), ptaglist = getPopularTags())
        else:
                photos = getRecommendedPhotos()
                if len(photos) == 0:
                        return render_template('search.html', message = 'You have no more recommended photos', taglist = getAllTags(), ptaglist = getPopularTags())
                return render_template('search.html', likes = getLikesDict(), taglist = getAllTags(), recphotos = photos, tagdict = getTagDictUsingPhotos(photos), commentdict = getCommentDictUsingPhotos(photos), base64=base64, ptaglist = getPopularTags())

@app.route('/search', methods=['GET'])
def get_search():
        albumid = request.args.get('para')
        uid = request.args.get('para1')
        if uid != None:
                return render_template('search.html', likes = getLikesDict(), founduser = uid, commentdict = getCommentDict(albumid), viewalbum=getAlbumPhotos(uid, albumid), albums=getAlbumList(uid), tagdict = getTagDict(albumid), base64=base64, taglist = getAllTags(), ptaglist = getPopularTags())
        else:
                return render_template('search.html', taglist = getAllTags(), ptaglist = getPopularTags())

@app.route('/multisearch', methods=['POST'])
def multi_search():
        tags = request.form.get('mtid')
        if len(tags.split()) == 0:
                return render_template('search.html', message = "Please input some actual text when searching for the tag!", taglist = getAllTags(), ptaglist = getPopularTags())         
        else:
                multitags, photos = getPhotosFromMultiTags(tags)
                if len(photos) == 0:
                        return render_template('search.html', message = "There are no photos with these tags!", taglist = getAllTags(), ptaglist = getPopularTags())         
                return render_template('search.html', viewmultitags = photos, multitags = multitags, likes = getLikesDict(), commentdict = getCommentDictUsingPhotos(photos), tagdict = getTagDictUsingPhotos(photos), base64=base64, taglist = getAllTags(), ptaglist = getPopularTags())         

@app.route('/tagsearch', methods=['GET'])
def tag_search():
        tagid = request.args.get('para')
        photos = getAllTagPhotos(tagid)
        return render_template('search.html', foundtag = tagid, likes = getLikesDict(), commentdict = getCommentDictUsingPhotos(photos), viewtags=photos, tagdict = getTagDictUsingPhotos(photos), base64=base64, taglist = getAllTags(), ptaglist = getPopularTags())        

@app.route('/comment', methods=['POST'])
def new_comment():
        try:
                currentuid = getUserIdFromEmail(flask_login.current_user.id)
        except:
                currentuid = None
        uid = request.form.get('uid')
        if currentuid == int(uid):
                return render_template('search.html', message = "You can't comment on your own photos! ;(", taglist = getAllTags(), ptaglist = getPopularTags())
        today = date.today()
        d = today.strftime("%y-%m-%d")
        text = request.form.get('newcomment')
        pid = request.form.get('pid')
        tagid = request.form.get('tid')
        multitags = request.form.get('mtid')
        cursor = conn.cursor()
        if currentuid != None:
                cursor.execute("INSERT INTO Comments (user_id, photo_id, text, date) VALUES (%s, %s, %s, %s)",(currentuid, pid, text, d))
        else:
                cursor.execute("INSERT INTO Users (fname, lname, password) VALUES ('Anonymous', '', 'p')")
                cursor.execute("SELECT user_id FROM Users ORDER BY user_id DESC")
                tempuid = cursor.fetchone()[0]
                cursor.execute("INSERT INTO Comments (user_id, photo_id, text, date) VALUES (%s, %s, %s, %s)",(tempuid, pid, text, d))
        conn.commit()
        cursor.close()
        albumid = request.form.get('aid')
        if albumid != None:
                return render_template('search.html', likes = getLikesDict(), founduser = uid, commentdict = getCommentDict(albumid), viewalbum=getAlbumPhotos(uid, albumid), albums=getAlbumList(uid), tagdict = getTagDict(albumid), base64=base64, taglist = getAllTags(), ptaglist = getPopularTags())
        elif tagid != None:
                photos = getAllTagPhotos(tagid)
                return render_template('search.html', likes = getLikesDict(), foundtag = tagid, commentdict = getCommentDictUsingPhotos(photos), viewtags=photos, tagdict = getTagDictUsingPhotos(photos), base64=base64, taglist = getAllTags(), ptaglist = getPopularTags())
        elif multitags != None:
                multitags, photos = getPhotosFromMultiTags(multitags)
                return render_template('search.html', likes = getLikesDict(), multitags = multitags, viewmultitags = photos, commentdict = getCommentDictUsingPhotos(photos), tagdict = getTagDictUsingPhotos(photos), base64=base64, taglist = getAllTags(), ptaglist = getPopularTags())
        else:
                photos = getRecommendedPhotos()
                return render_template('search.html', likes = getLikesDict(), taglist = getAllTags(), recphotos = photos, tagdict = getTagDictUsingPhotos(photos), commentdict = getCommentDictUsingPhotos(photos), base64=base64, ptaglist = getPopularTags())

        
@app.route('/makealbum', methods=['POST'])
@flask_login.login_required
def make_album():
        uid = getUserIdFromEmail(flask_login.current_user.id)
        album = request.form.get('album')
        if len(album.split()) == 0:
                return render_template('upload.html', message = "Album names cannot be just spaces! ;(", albums=getAlbumList(uid), tags = getTags(uid))
        today = date.today()
        d = today.strftime("%y-%m-%d")
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO Albums (name, date, user_id) VALUES (%s, %s, %s)''' ,(album, d, uid))        
        conn.commit()
        cursor.close()
        return render_template('upload.html', albums=getAlbumList(uid), tags = getTags(uid))



@app.route('/deletephoto', methods=['POST'])
@flask_login.login_required
def delete_photo():
        uid = getUserIdFromEmail(flask_login.current_user.id)
        albumid = request.form.get('aid')
        photoid = request.form.get('pid')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Photos WHERE photo_id = (%s)" ,(photoid))
        conn.commit()
        cursor.close()
        if getAlbumPhotos(uid, albumid) == ():
                return render_template('upload.html', tags = getTags(uid), zero = albumid, albums=getAlbumList(uid))
        return render_template('upload.html', tags = getTags(uid), likes = getLikesDict(), viewalbum=getAlbumPhotos(uid, albumid), albums=getAlbumList(uid), commentdict = getCommentDict(albumid), tagdict = getTagDict(albumid), base64=base64)

@app.route('/deletealbum', methods=['POST'])
@flask_login.login_required
def delete_album():
        uid = getUserIdFromEmail(flask_login.current_user.id)
        albumid = request.form.get('aid')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Albums WHERE albums_id = (%s)" ,(albumid))
        conn.commit()
        cursor.close()
        return render_template('upload.html', tags = getTags(uid), albums=getAlbumList(uid))
        
@app.route('/friend', methods=['GET', 'POST'])
@flask_login.login_required
def add_friend():
        uid = getUserIdFromEmail(flask_login.current_user.id)
        if request.method == 'POST':
                email = request.form.get('email')
                cursor = conn.cursor()
                cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
                try:
                        otherid = cursor.fetchone()[0]
                except:
                        cursor.close()
                        return render_template('friends.html', message='A user with that email doesnt exist, please put in an email of a user that does exist!', friends=getFriendList(uid), friends2=getRecommendedFriendList(uid))
                if email != flask_login.current_user.id:
                        try:
                                cursor.execute('''INSERT INTO Friends (user_id1, user_id2) VALUES (%s, %s)''' ,(uid,otherid))
                        except:
                                cursor.close()
                                return render_template('friends.html', message='You are already friends with that user, please enter an email of a user you are not friends with yet!', friends=getFriendList(uid), friends2=getRecommendedFriendList(uid))
                else:
                        cursor.close()
                        return render_template('friends.html', message='You cannot friend yourself!', friends=getFriendList(uid), friends2=getRecommendedFriendList(uid))
                conn.commit()
                cursor.close()
                return render_template('friends.html', message='Friend added!', friends=getFriendList(uid), friends2=getRecommendedFriendList(uid))
        else:
                return render_template('friends.html', friends=getFriendList(uid), friends2=getRecommendedFriendList(uid))

@app.route('/leaderboard', methods=['GET'])
def leaderboard():
        leaderboard = getLeaderboardDict()
        try:
                uid = getUserIdFromEmail(flask_login.current_user.id)
                return render_template('leaderboard.html', topusers = leaderboard, loggedin = True, userscore = getContributionScore(uid))
        except:
                return render_template('leaderboard.html', topusers = leaderboard)

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
