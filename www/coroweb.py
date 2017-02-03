#! /usr/bin/env python3
# -*- coding:utf-8 -*-

import asyncio,os,inspect,logging,functools 
from urllib import parse
from aiohttp import web
from apis import APIError

def get(path):
	'''
	define decorator @get('/path')
	'''
	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args, **kw):
			return func(*args, **kw)
		wrapper.__method__ = 'GET'
		wrapper.__route__ = path

		return wrapper

	return decorator

def post(path):
	'''
	define decorator @post('/path')
	'''
	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args, **kw):
			return func(*args, **kw)
		wrapper.__method__ = 'POST'
		wrapper.__route__ = path

		return wrapper
	return decorator

def get_required_kw_args(fn):
	args = []
	params = inspect.signature(fn).parameters

	for name,param in params.items():
		if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty：
		args.append(name)
	return tuple(args)

def get_named_kw_args(fn):
	args = []
	params = inspect.signature(fn).parameters
	for name,param in params.items():
		if param.kind == inspect.Parameter.KEYWORD_ONLY:
			args.append(name)

		return tuple(args)

def has_named_kw_args(fn):
	params = inspect.signature(fn).parameters
	for name,param in params.items():
		if param.kind == inspect.Parameter.KEYWORD_ONLY:
			return True

def has_var_kw_arg(fn):
	params = inspect.signature(fn).parameters
	for name,param in params.items():
		if param.kind == inspect.Parameter.VAR_KEYWORD:
			return True

def has_request_arg(fn):
	sig = inspect.signature(fn)
	params = sig.parameters
	found = False

	for name,param in params.items():
		if name == 'request':
			found = True
			continue
		if found and (param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.KEYWORD_ONLY and param.kind != inspect.Parameter.VAR_KEYWORD):
			raise ValueError('request param must be the last named param in function')
	return found

class RequestHandler(object):
	
	def __init__(self, app, fn):
		self.app = app
		self.fn = fn
		self._has_request_arg = has_request_arg(fn)
		self._has_var_kw_arg = has_var_kw_arg(fn)
		self._has_named_kw_args = has_named_kw_args(fn)
		self._named_kw_args = get_named_kw_args(fn)
		self._required_kw_args = get_required_kw_args(fn)

	async def __call__(self,request):
	kw = None
	if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
		if request.method == 'POST':
			if not request.content_type:
				return web.HttpBadRequest('missing content-type')

			ct = request.content_type.lower()
			
			if ct.startwith('application/json'):
				params = await request.json()
				if not isinstance(params, dict):
					return web.HttpBadRequest('json body must be object')
				kw = params
			elif ct.startwith('application/x-www-form-urlencoded') or ct.startwith('application/form-data'):
				params = await request.post()
				kw = dict(** params)
			else:
				return web.HttpBadRequest('unsupport content type')

		if request.method == 'GET':
			qs = request.query_string
			if qs:
				kw = dict()
				for k,v in parse.parse_qs(qs,True).items():
					kw[k] = v[0]

	if kw is None:
		kw = dict(**request.match_info)

	else:
		if not self._has_var_kw_arg and self._named_kw_args:
			copy = dict()
			for name in self._named_kw_args:
				if name in kw:
					copy[name] = kw[name]
			kw = copy

		for k,v in request.match_info.items():
			if k in kw:
				logging.warning('duplicate arg name in named args. arg name : %s' % k)
			kw[k] = v

	if self._has_request_arg:
		kw['request'] = request

	if self._required_kw_args:
		for name in self._required_kw_args:
			if not name in kw:
				return web.HttpBadRequest('missing argument: %s' % name)

	logging.info('call with args: %s' % str(kw))

	try:
		r = await self._func(**kw)
		return r
	except APIError as e:
		return dict(error = e.error, data = e.data, message = d.message)

def handle_url_xxx(request):
	url_param = request.match_info['key']
	query_params = parse_qs(request.query_string)

	text = render('template',data)

	return web.Response(text.encode('utf-8')



