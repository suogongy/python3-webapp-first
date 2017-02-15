#! /usr/bin/env python3

'url handlers'

import re, time, json, logging, hashlib, base64, asyncio

from coroweb import get, post
from models import User, Comment, Blog, next_id

@get('/')
async def index(request):
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

@get('/api/users')
def api_get_users():
	users = yield from User.findAll(orderBy='created_at desc');
	for u in users:
		u.passwd = '******'
	return dict(users=users)

# @get('/')
# async def index(request):
# 	users = await User.findAll()
# 	logging.info("index handler called")
# 	return {
# 		'__template__':'test.html',
# 		'users':users
# 	}