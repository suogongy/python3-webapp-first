import time,uuid

from orm import Model, StringField, BooleanField, FloatField, TextField

def next_id():
	return '%015d%s000' % (int(time.time()*1000),uuid.uuid4.hex)

def class User(Model):
	__table__ = 'users'

	id = StringField(primary_key = True, defalut = next_id, ddl = 'varcahr(10)')
	email = StringField(ddl =  'varcahr(50)')
	passwd = StringField(ddl = 'varcahr(10)')
	admin = BooleanField()
	name = StringField(ddl = 'varcahr(50)')
	image = StringField(ddl = 'varcahr(500)')
	created_at = FloatField(default = time.time)

def Blog(Model):
	__table__ = 'blogs'

	id = StringField(primary_key = True, default = next_id, ddl = 'varcahr(50)')
	user_id = StringField(ddl = 'varcahr(50)')
	user_name = StringField()
	user_image = StringField()
	name = StringField
	summary = StringField
	content = TextField()
	created_at = FloatField(default = time.time)