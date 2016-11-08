######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
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
import flask.ext.login as flask_login



#for image uploading
from werkzeug import secure_filename
import os, base64
import datetime


mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'zhoujian'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

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
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
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
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
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
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out', photos=getAllPhotos())

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		first_name=request.form.get('first_name')
		last_name=request.form.get('last_name')
		hometown=request.form.get('hometown')
		birthday=request.form.get('birthday')
		gender=request.form.get('gender')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print cursor.execute("INSERT INTO Users (email, password, first_name, last_name, hometown, birthday, gender) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}','{6}')".format(email, password, first_name, last_name, hometown, birthday,gender))
		conn.commit()
		#log user in

		# uid = getUserIdFromEmail(email)
		# cursor = conn.cursor()
		# cursor.execute("INSERT INTO Acts (user_id) VALUES ('{0}')".format(uid))
		# conn.commit()
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!', photos=getAllPhotos())
	else:
		print "couldn't find all tokens"
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True

def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_name FROM Albums WHERE buser_id = '{0}'".format(uid))
	return cursor.fetchall()

def getUsersTags(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT t.tag_string FROM Tags t, Pictures p, Users u WHERE u.user_id='{0}' AND u.user_id=p.user_id AND p.picture_id=t.picture_id GROUP BY t.tag_string".format(uid))
	return cursor.fetchall()

def getFriendsEmail(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT u.email FROM Users u, Friends f WHERE f.user1_id='{0}' AND f.user2_id= u.user_id".format(uid))
	return cursor.fetchall()

def getAllPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures")
	return cursor.fetchall()

def getPhotosId(picture_id):
	cursor = conn.cursor()
	cursor.execute("SELECT p.imgdata, p.caption FROM Pictures p WHERE p.picture_id='{0}'".format(picture_id))
	return cursor.fetchall()

def getAlbumId(album_name, uid):
	cursor = conn.cursor()
	cursor.execute("SELECT album_id FROM Albums WHERE album_name='{0}' AND buser_id='{1}'".format(album_name, uid))
	return cursor.fetchone()[0]

def getAlbumPhoto(album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE album_id='{0}'".format(album_id))
	return cursor.fetchall()

def getPicCom(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT content, email, updated_time FROM Comments WHERE picture_id='{0}'".format(photo_id))
	return cursor.fetchall()

def getPhotoLikes(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(*) FROM Likes WHERE picture_id='{0}'".format(photo_id))
	return cursor.fetchone()[0]

def getPhotoLikers(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT u.email FROM Likes l, Users u WHERE picture_id='{0}' AND l.user_id=u.user_id".format(photo_id))
	return cursor.fetchall()

def getPhotobyAlbumId(album_id):
	cursor = conn.cursor()
	cursor.execute("SELECT p.picture_id FROM Pictures p, Albums a  WHERE a.album_id='{0}' AND p.album_id=a.album_id".format(album_id))
	return cursor.fetchall()

def getAllUsers():
	cursor = conn.cursor()
	cursor.execute("SELECT u.email, COUNT(a.actId) AS num FROM Acts a RIGHT JOIN Users u ON u.user_id=a.user_id GROUP BY u.email ORDER BY num DESC")
	return cursor.fetchall()

def getPhotoTags(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT tag_string FROM Tags WHERE picture_id='{0}'".format(photo_id))
	return cursor.fetchall()

def yourPhoto(email, photo_id):
	cursor = conn.cursor()
	if cursor.execute("SELECT u.user_id FROM Pictures p, Users u WHERE u.email='{0}' AND  u.user_id = p.user_id AND p.picture_id='{1}'".format(email, photo_id)):
		return True
	else:
		return False

def getFriendPhotos(email):
	cursor = conn.cursor()
	cursor.execute("SELECT p.imgdata, p.picture_id, p.caption FROM Pictures p, Users u WHERE u.email='{0}' AND u.user_id = p.user_id".format(email))
	return cursor.fetchall()


#end login code
@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", photos=getAllPhotos(), mostTags=getPopularTags())

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('upload.html', albums=getUsersAlbums(uid) )

	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		album_name = request.form.get('album_name')
		photo_data = base64.standard_b64encode(imgfile.read())
		cursor = conn.cursor()
		if cursor.execute("SELECT album_id FROM Albums WHERE album_name='{0}' AND buser_id='{1}'".format(album_name, uid)):
			album_id = getAlbumId(album_name,uid)
			cursor.execute("INSERT INTO Pictures (imgdata, user_id, caption, album_id) VALUES ('{0}', '{1}', '{2}', '{3}')".format(photo_data, uid, caption, album_id))
			cursor.execute("INSERT INTO Acts (user_id) VALUES ('{0}')".format(uid))
			conn.commit()
			return render_template('upload.html', message='Photo uploaded!', albums=getUsersAlbums(uid))
		else:
			return render_template('upload.html', message='Wrong album!', albums=getUsersAlbums(uid))

@app.route('/albumphoto', methods=['GET','POST'])
@flask_login.login_required
def get_album():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('myalbum.html', albums=getUsersAlbums(uid), yourTags=getUsersTags(uid))

	if request.method =='POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		album_name = request.form.get('album_name')
		cursor = conn.cursor()
		if cursor.execute("SELECT album_id FROM Albums WHERE album_name='{0}' AND buser_id='{1}'".format(album_name, uid)):
			album_id = getAlbumId(album_name,uid)
			pid = request.form.get('pid')
			return render_template('myalbum.html',albums=getUsersAlbums(uid), photos=getAlbumPhoto(album_id), tags=getPhotoTags(pid))
		else:
			return render_template('myalbum.html', albums=getUsersAlbums(uid), message="you don't have this album!")

#album management System
@app.route('/createalbum', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
	if request.method =='GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('createalbum.html', message='Photo Management Page', albums=getUsersAlbums(uid))

	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		album_name = request.form.get('album_name')
		a = datetime.datetime.now()
		cursor = conn.cursor()
		if not cursor.execute("SELECT album_id FROM Albums WHERE album_name = '{0}' AND buser_id='{1}'".format(album_name, uid)):
			cursor.execute("INSERT INTO Albums (album_name, updated_time, buser_id) VALUES ('{0}', '{1}', '{2}')".format(album_name, a.strftime('%Y-%m-%d %H:%M:%S'), uid))
			conn.commit()
			return render_template('createalbum.html', message='Album Created!', albums=getUsersAlbums(uid))
		else:
			return render_template('createalbum.html', message="You or other user own this album alreay! Please enter another name!", albums=getUsersAlbums(uid))
	else:
		return render_template('createalbum.html')

@app.route('/delalbum', methods=['POST'])
@flask_login.login_required
def del_album():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	album_name = request.form.get('album_name')
	cursor = conn.cursor()
	if cursor.execute("SELECT album_id FROM Albums WHERE album_name = '{0}' AND buser_id='{1}'".format(album_name, uid)):
		album_id = getAlbumId(album_name,uid)
		photos = getPhotobyAlbumId(album_id)
		print photos
		for photo in photos:
			for pid in photo:
				cursor.execute("DELETE FROM Tags WHERE picture_id='{0}'".format(pid))
				cursor.execute("DELETE FROM likes WHERE picture_id='{0}'".format(pid))
				cursor.execute("DELETE FROM Comments WHERE picture_id='{0}'".format(pid))
				cursor.execute("DELETE FROM Pictures WHERE picture_id='{0}'".format(pid))
		cursor.execute("DELETE FROM Albums WHERE album_id='{0}'".format(album_id))
		conn.commit()
		return render_template('createalbum.html', message="Successfully deleted!", albums=getUsersAlbums(uid))
	else:
		return render_template('createalbum.html', message="Failed to delete!", albums=getUsersAlbums(uid))


#Friends System
@app.route('/friends', methods=['GET'])
@flask_login.login_required
def friend():
	if request.method == 'GET':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		return render_template('friend.html',message='Friends Management',friendlists=getFriendsEmail(uid),allusers=getAllUsers())

@app.route('/addFriend', methods=['POST'])
@flask_login.login_required
def add_friend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	email = request.form.get('user2_email')
	cursor = conn.cursor()
	if cursor.execute("SELECT user_id FROM Users WHERE email='{0}'".format(email)) and not cursor.execute("SELECT * FROM Users u, Friends f WHERE f.user1_id='{0}' AND f.user2_id = u.user_id AND u.email='{1}'".format(uid, email)):
		user2_id = getUserIdFromEmail(email)
		cursor.execute("INSERT INTO Friends (user1_id, user2_id) VALUES ('{0}', '{1}')".format(uid, user2_id))
		conn.commit()
		return render_template('friend.html', message='Successfully Friend Added!', friendlists=getFriendsEmail(uid),allusers=getAllUsers())
	else:
		return render_template('friend.html', message='Invalid email or You have already added this friend!',friendlists=getFriendsEmail(uid),allusers=getAllUsers())

@app.route('/delFriend', methods=['POST'])
@flask_login.login_required
def del_friend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	email = request.form.get('del_email')
	cursor = conn.cursor()
	if cursor.execute("SELECT user_id FROM Users WHERE email='{0}'".format(email)) and cursor.execute("SELECT u.email FROM Users u, Friends f WHERE f.user1_id='{0}' AND f.user2_id= u.user_id".format(uid)):
		del_id = getUserIdFromEmail(email)
		cursor.execute("DELETE FROM Friends WHERE user2_id='{0}'".format(del_id))
		conn.commit()
		return render_template('friend.html', message='Successfully Friend Deleted!', friendlists=getFriendsEmail(uid), allusers=getAllUsers())
	else:
		return render_template('friend.html', message="Invalid email or You don't have this friend",friendlists=getFriendsEmail(uid), allusers=getAllUsers())

@app.route('/getfriendphoto', methods=['POST','GET'])
@flask_login.login_required
def friend_photo():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	email = request.form.get('friendemail')
	return render_template('FriendPhoto.html', message="Friend's photos:", photos=getFriendPhotos(email))


# comment photos
@app.route('/comment', methods=['POST','GET'])
def comment():
	if request.method == 'POST':
		photo_id = request.form.get('picture_id')
		like = getPhotoLikes(photo_id)
		liker = getPhotoLikers(photo_id)
		return render_template('compage.html', message="Picture", photos=getPhotosId(photo_id), picId=photo_id, comments=getPicCom(photo_id), likes=like, likers=liker, tags=getPhotoTags(photo_id))

@app.route('/makecomment', methods=['POST','GET'])
def makecomment():
	if request.method == 'POST':
		try:
			email = flask_login.current_user.id
			photo_id = request.form.get('picture_id')
			like = getPhotoLikes(photo_id)
			liker = getPhotoLikers(photo_id)
			if yourPhoto(email, photo_id):
				return render_template('compage.html', comments=getPicCom(photo_id), photos=getPhotosId(photo_id), message="This is your picture!",picId=photo_id, likes=like, likers=liker)
			else:
				uid = getUserIdFromEmail(flask_login.current_user.id)
				content = request.form.get('content')
				a = datetime.datetime.now()
				cursor = conn.cursor()
				cursor.execute("INSERT INTO Comments (picture_id, content, email, updated_time ) VALUES ('{0}', '{1}', '{2}', '{3}')".format(photo_id, content, email, a.strftime('%Y-%m-%d %H:%M:%S')))
				cursor.execute("INSERT INTO Acts (user_id) VALUES ('{0}')".format(uid))
				conn.commit()
				return render_template('compage.html', comments=getPicCom(photo_id), photos=getPhotosId(photo_id), message="Picture!",picId=photo_id, likes=like,likers=liker)
		except:
			photo_id = request.form.get('picture_id')
			like = getPhotoLikes(photo_id)
			liker = getPhotoLikers(photo_id)
			content = request.form.get('content')
			a = datetime.datetime.now()
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Comments (picture_id, content, email, updated_time ) VALUES ('{0}', '{1}', 'Anonymous', '{2}')".format(photo_id, content, a.strftime('%Y-%m-%d %H:%M:%S')))
			conn.commit()
			return render_template('compage.html', comments=getPicCom(photo_id), photos=getPhotosId(photo_id), message="Picture", picId=photo_id, likes=like,likers=liker)

# like
@app.route('/like', methods=['GET', 'POST'])
@flask_login.login_required
def likePhoto():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		photo_id = request.form.get('picture_id')
		cursor = conn.cursor()
		if cursor.execute("SELECT * FROM Likes WHERE user_id='{0}' AND picture_id='{1}'".format(uid, photo_id)):
			like = getPhotoLikes(photo_id)
			liker = getPhotoLikers(photo_id)
			return render_template('compage.html', comments=getPicCom(photo_id), photos=getPhotosId(photo_id), message="You have already liked this photo before!", picId=photo_id, likes=like,likers=liker)
		else:
			cursor.execute("INSERT INTO Likes (picture_id, user_id) VALUES ('{0}', '{1}')".format(photo_id, uid))
			conn.commit()
			like = getPhotoLikes(photo_id)
			liker = getPhotoLikers(photo_id)
			return render_template('compage.html', comments=getPicCom(photo_id), photos=getPhotosId(photo_id), message="Successfully liked!", picId=photo_id, likes=like, likers=liker)

# Add a tag
@app.route('/tagpage', methods=['GET', 'POST'])
@flask_login.login_required
def tagpage():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		photo_id = request.form.get('picture_id')
		return render_template('tag.html', photos=getPhotosId(photo_id),picId=photo_id, tags=getPhotoTags(photo_id), mostTags=getPopularTags())

@app.route('/addTag', methods=['GET', 'POST'])
@flask_login.login_required
def addtag():
	if request.method == 'POST':
		photo_id = request.form.get('picture_id')
		tag_string = request.form.get('tag_string')
		tag_string = tag_string.replace(' ',"")
		cursor = conn.cursor()
		if not cursor.execute("SELECT tag_string FROM Tags WHERE tag_string='{0}' AND picture_id='{1}'".format(tag_string,photo_id)):
			cursor.execute("INSERT INTO Tags (tag_string, picture_id) VALUES ('{0}', '{1}')".format(tag_string, photo_id))
			conn.commit()
			return render_template('tag.html', photos=getPhotosId(photo_id), picId=photo_id, tags=getPhotoTags(photo_id), mostTags=getPopularTags())
		else:
			return render_template('tag.html', photos=getPhotosId(photo_id), picId=photo_id, tags=getPhotoTags(photo_id), mostTags=getPopularTags(),message="Your photo already has this tag!!!")

@app.route('/deltephoto',methods=['GET', 'POST'])
@flask_login.login_required
def delPhoto():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		photo_id = request.form.get('picture_id')
		cursor = conn.cursor()
		cursor.execute("DELETE FROM Tags WHERE picture_id='{0}'".format(photo_id))
		conn.commit()
		cursor = conn.cursor()
		cursor.execute("DELETE FROM likes WHERE picture_id='{0}'".format(photo_id))
		conn.commit()
		cursor = conn.cursor()
		cursor.execute("DELETE FROM Comments WHERE picture_id='{0}'".format(photo_id))
		conn.commit()
		cursor = conn.cursor()
		cursor.execute("DELETE FROM Pictures WHERE picture_id='{0}'".format(photo_id))
		conn.commit()
		return render_template('myalbum.html', albums=getUsersAlbums(uid), yourTags=getUsersTags(uid))


# Search a tag
@app.route('/search', methods=['POST', 'GET'])
def serach():
	if request.method == 'POST':
		search_string = request.form.get('serString')
		search_string = search_string.replace(" ","")
		if not search_string:
			return render_template('hello.html', message1="Pleas input tags!", photos=getAllPhotos())
		else:
			list_words = search_string.split(',')
			valid_words = getValids(list_words)
			return render_template('searchAllpage.html', photos=getAllPhotosById(valid_words))

def intersection(a, b):
	return set(a) & set(b)

def findPicIdWord(word):
	cursor = conn.cursor()
	cursor.execute("SELECT picture_id FROM Tags WHERE tag_string='{0}'".format(word))
	return cursor.fetchall()

def wordIsValid(word):
	cursor = conn.cursor()
	if cursor.execute("SELECT picture_id FROM Tags WHERE tag_string='{0}'".format(word)):
		return True
	else:
		return False

def getAllPhotosId():
	cursor = conn.cursor()
	cursor.execute("SELECT picture_id FROM Pictures")
	return cursor.fetchall()

def getValids(list_words):
	valid_words = []
	if list_words:
		for word in list_words:
			if wordIsValid(word):
				valid_words.append(word)
	return valid_words

def getAllPhotosById(valid_words):
	picture_ids = []
	allids = []
	photo = []
	if valid_words:
		allids = findPicIdWord(valid_words[0])
		for word in valid_words:
			picture_ids = findPicIdWord(word)
			allids = intersection(allids,picture_ids)
	print allids
	if allids:
		for photo_id in allids:
			for haha in photo_id:
				photo.append(getTagsPhotobyid(haha))
	return photo

def getTagsPhotobyid(photo_id):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id='{0}'".format(photo_id))
	return cursor.fetchone()

def getPopularTags():
	cursor = conn.cursor()
	cursor.execute("SELECT tag_string, COUNT(tag_string) AS num FROM Tags GROUP BY tag_string ORDER BY num DESC LIMIT 10")
	return cursor.fetchall()

def getPhotosByTag(tag_string):
	cursor = conn.cursor()
	cursor.execute("SELECT p.imgdata, p.picture_id, p.caption FROM Pictures p , Tags t WHERE t.tag_string='{0}' AND t.picture_id = p.picture_id".format(tag_string))
	return cursor.fetchall()

def getMyPhotoByTag(tag_string,uid):
	cursor = conn.cursor()
	cursor.execute("SELECT p.imgdata, p.picture_id, p.caption FROM Pictures p , Tags t, Users u WHERE t.tag_string='{0}' AND u.user_id='{1}' AND t.picture_id = p.picture_id AND u.user_id=p.user_id".format(tag_string,uid))
	return cursor.fetchall()


#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare', photos=getAllPhotos(), mostTags=getPopularTags())

#render tags photos
@app.route("/getphoto", methods=['POST','GET'])
def tagphoto():
	if request.method=='POST':
		tag_string=request.form.get('tag')
		return render_template('photoTags.html', message=tag_string, photos=getPhotosByTag(tag_string))

@app.route("/getmyphoto", methods=['POST','GET'])
@flask_login.login_required
def mytagphoto():
	if request.method=='POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		tag_string=request.form.get('tag')
		return render_template('photoTags.html', message=tag_string, photos=getMyPhotoByTag(tag_string,uid))


#youmayalsolike
@app.route('/youmayalsolike', methods=['POST','GET'])
@flask_login.login_required
def alsolike():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	tags = []
	for tag in topFiveTagsByUser(uid):
		tags.append(tag[0])
	tagLists = sublists(tags,4)
	photos = []
	tagLists.sort(lambda x,y: cmp(len(y),len(x)))
	print tagLists
	for tags in tagLists:
		for tag in tags:
			photo = getPhotosByTag(tag)
			for t in photo:
				if t not in photos:
					photos.append(t)
	return render_template('alsolike.html',photos=photos)

def topFiveTagsByUser(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT t.tag_string, COUNT(t.tag_string) AS num FROM Tags t, Pictures p, Users u WHERE u.user_id='{0}' AND u.user_id=p.user_id AND p.picture_id=t.picture_id GROUP BY t.tag_string ORDER BY num DESC LIMIT 5".format(uid))
	return cursor.fetchall()

def getphotoyoumaylike(tag_string, uid):
	cursor = conn.cursor()
	cursor.execute("SELECT p.imgdata, p.picture_id, p.caption FROM Pictures p, Users u, Tags t WHERE t.tag_string='{0}' AND u.user_id='{1}' AND u.user_id=p.user_id AND p.picture_id=t.picture_id".format(tag_string,uid))
	return cursor.fetchall()

def sublists(input, depth):
	output = []
	output.append(input)
	if depth > 0:
		for i in range(0,len(input)):
			sub = input[0:i] + input[i+1:]
			output += [sub]
			output.extend(sublists(sub,depth-1))
	return output

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
