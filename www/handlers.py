#! /usr/bin/env python3

'url handlers'

import re, time, json, logging, hashlib, base64, asyncio

import markdown2

from aiohttp import web 

from coroweb import get, post
from apis import Page, APIValueError,APIError,APIPermissionError,APIResourceNotFoundError

from models import User, Comment, Blog, next_id
from config import configs

COOKIE_NAME = "awesession"
_COOKIE_KEY = configs.session.secret

def check_admin(request):
	if request.__user__ is None or not request.__user__.admin:
		raise APIPermissionError()

def get_page_index(page_str):
	p = 1
	try:
		p = int(page_str)
	except ValueError as e:
		pass
	
	if p < 1:
		p = 1

	return p

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

@get('/manage/blog/create')
def manage_create_blog():
	return {
		'__template__':'manage_blog_edit.html',
		'id': '',
		'action': '/api/blog'
	}

@get('/manage/blog')
def manage_blogs(*, page = '1'):
	return {
	'__template__':'manage_blogs.html',
	'page_index':get_page_index(page)
	}

@get('/blog/{id}')
def get_blog(*,id):
	logging.info('param id is :%s' % id)
	blog = yield from Blog.find(id)
	logging.info('found blog :%s' % str(blog))
	comments = yield from Comment.findAll('blog_id=?',[id],orderBy='created_at desc')
	for c in comments:
		c.html_content = text2html(c.content)
	blog.html_content = markdown2.markdown(blog.content)

	return {
		'__template__':'blog.html',
		'blog':blog,
		'comments': comments
	}

@get('/api/blog/{id}')
def api_get_blog(*,id):
	logging.info('param id is :%s' % id)
	blog = yield from Blog.find(id)
	return blog

@get('/api/blog')
def api_get_blogs(*,page='1'):
	page_index = get_page_index(page)
	num = yield from Blog.findNumber('count(id)')
	p = Page(num,page_index)
	if num == 0:
		return dict(page=p, blogs=())
	blogs = yield from Blog.findAll(orderBy='created_at desc', limit = (p.offset,p.limit))
	return dict(page=p,blogs = blogs)

@post('/api/blog')
def api_create_blog(request, *, name, summary, content):
	check_admin(request)
	if not name or not name.strip():
		raise APIValueError('name','name can\'t be null')
	if not summary or not summary.strip():
		raise APIValueError('summary',r'summary can\'t be null')
	if not content or not content.strip():
		raise APIValueError('content', 'conent can\'t be null')

	blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name,user_image=request.__user__.image,
		name=name.strip(), summary = summary.strip(), content = content.strip())
	yield from blog.save()

	return blog 
