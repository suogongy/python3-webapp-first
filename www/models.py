import time,uuid

from orm import Model, StringField, BooleanField, FloatField, TextField

def next_id():
	return '%015d%s000' % (int(time.time()*1000),uuid.uuid4.hex)

class User(Model):
	__table__ = 'users'

	id = StringField(primary_key = True, default = next_id, ddl = 'varcahr(10)')
	email = StringField(ddl =  'varcahr(50)')
	passwd = StringField(ddl = 'varcahr(10)')
	admin = BooleanField()
	name = StringField(ddl = 'varcahr(50)')
	image = StringField(ddl = 'varcahr(500)')
	created_at = FloatField(default = time.time)

class Blog(Model):
	__table__ = 'blogs'

	id = StringField(primary_key = True, default = next_id, ddl = 'varcahr(50)')
	user_id = StringField(ddl = 'varcahr(50)')
	user_name = StringField(ddl = 'varcahr(50)')
	user_image = StringField(ddl = 'varcahr(500)')
	name = StringField(ddl = 'varcahr(50)')
	summary = StringField(ddl = 'varcahr(50)')
	content = TextField()
	created_at = FloatField(default = time.time)

class Comment(Model):
	__table__ = 'comments'

	id = StringField(primary_key = True, default = next_id, ddl = 'varcahr(50)')
	blog_id = StringField(ddl = 'varcahr(50)')
	user_id = StringField(ddl = 'varcahr(50)')
	user_name = StringField(ddl = 'varcahr(50)')
	user_image = StringField(ddl = 'varcahr(500)')
	content = TextField()
	created_at = FloatField(default = time.time)
