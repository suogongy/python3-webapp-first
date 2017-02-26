#! /usr/bin/env python3

'url handlers'

import re, time, json, logging, hashlib, base64, asyncio

import markdown2

from aiohttp import web 

from coroweb import get, post
from apis import APIValueError,APIError,APIResourceNotFoundError

from models import User, Comment, Blog, next_id
from config import configs

COOKIE_NAME = "awesession"
_COOKIE_KEY = configs.session.secret

def user2cookie(user,max_age):
	
	#build cookiestring by: id-expires-sha1
	expires = str(int(time.time() + max_age))
	s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
	L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
	return '-'.join(L)

@asyncio.coroutine
def cookie2user(cookie_str):

	if not cookie_str:
		return None 

	try:
		L = cookie_str.split('-')
		if len(L) != 3:
			return None 
		uid, expires, sha1 = L
		if int(expires) < time.time():
			return None 
		user = yield from User.find(uid)
		if user  is None:
			return None
		s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
		if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
			logging.info('invalid sha1')
			return None
		user.passwd = '******'
		return user 
	except Exception as e:
		logging.exception(e)
		return None

@get('/')
def index(request):
	summary = '总结，summary。第八天。python web实战'
	
	blogs = [
		Blog(id='1',name='blog1',summary=summary,created_at=time.time()-120),
		Blog(id='2',name='blog2',summary=summary,created_at=time.time()-3600),
		Blog(id='3',name='blog3',summary=summary,created_at=time.time()-7200)
	]

	return {
		'__template__':'blogs.html',
		'blogs':blogs
	}

@get('/register')
def register():
	return{
		'__template__':'register.html'
	}

@get('/signin')
def signin():
	return{
		'__template__':'signin.html'
	}

@get('/signout')
def signout(request):
	referer = request.headers.get('Referer')
	r = web.HTTPFound(referer or '/')
	r.set_cookie(COOKIE_NAME,'-deleted-',max_age = 0, httponly = True)
	logging.info('user sign out.')
	return r

@get('/api/user')
def api_get_users():
	users = yield from User.findAll(orderBy='created_at desc');
	for u in users:
		u.passwd = '******'
	
	return dict(users=users)

@post('/api/user')
def api_register_user(*,email,name,passwd):

	logging.info("payams" + email + name + passwd)

	if not name or not name.strip():
		raise ApiValueError('name')
	if not email or not email.strip():
		raise ApiValueError('email')
	if not passwd or not passwd.strip():
		raise ApiValueError('passwd')

	users = yield from User.findAll('email = ?',[email])

	if len(users) > 0 :
		raise APIError('register failed!','email','email is already in use!')

	uid = next_id()
	sha1_passwd = '%s:%s' % (uid, passwd)
	user = User(id=uid,name = name.strip(),email = email,passwd= hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),image="http://www.gravatar.com/avatar/%s?d=mm&s=120" % hashlib.md5(email.encode('utf-8')).hexdigest())
	yield from user.save()

	# make session cookie
	r = web.Response()
	r.set_cookie(COOKIE_NAME,user2cookie(user,86400),max_age=86400,httponly=True)
	user.passwd = '******'
	r.content_type='application/json'
	r.body = json.dumps(user,ensure_ascii=False).encode('utf-8')
	return r

@post('/api/authenticate')
def authenticate(*, email, passwd):

	logging.info("/api/authenticate called")
	if not email:
		raise APIValueError('email','invalid email')
	if not passwd:
		raise APIValueError('passwd','invalid passwd')

	users = yield from User.findAll('email=?',[email])
	if len(users) == 0:
		raise ApiValueError('email','email not exits')
	user = users[0]

	# check passwd
	sha1 = hashlib.sha1()
	sha1.update(user.id.encode('utf-8'))
	sha1.update(b':')
	sha1.update(passwd.encode('utf-8'))

	if user.passwd != sha1.hexdigest():
		raise ApiValueError('passwd','invalid passwd')

	# set cookie
	r = web.Response()
	r.set_cookie(COOKIE_NAME, user2cookie(user,86400),max_age=86400,httponly=True)
	user.passwd = '******'
	r.content_type = 'application/json'
	r.body = json.dumps(user,ensure_ascii=False).encode('utf-8')
	return r


