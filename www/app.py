#! /usr/bin/env python3

'''
async web app
'''

import logging, logging.basicConfig(level= logging.INFO)

import asyncio, os, json, time

from datetime import datetime

from aiohttp import web

from jinja2 import Environment, FileSystemLoader

import orm

from coroweb import add_routes, add_static

def init_jinja2(app, **kw):
	logging.info('init jinja2')

	options = dict(
		autoscapse = kw.get('autoscapse', True)
		block_start_string = kw.get('block_start_string','{%')
		block_end_string = kw.get('block_end_string', '%}')
		variable_start_string = kw.get('variable_start_string','{{')
		variable_end_string = kw.get('variable_end_string','}}')
		auto_reload = kw.get('auto_reload', True)
	)

	path = kw.get('path', None)
	if path is None:
		path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates')

	logging.info('set jinja2 templats path : %s' % path)

	env = Environment(loader = FileSystemLoader(path), **options)
	filters = kw.get('filters',None)
	if filters is not None:
		for name,f in filters.items():
			env.filters[name] = f
	app['__templating__'] = env

async def logger_factory(app, handler):
	async def logger(request):
		logging.info('request: %s, %s' % (request.method, request.path))
		return (await handler(request))
	return logger

