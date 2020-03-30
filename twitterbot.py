#twitterbot.py
#simple python bot to post tweets
#twitter.com/ModernStarTrek
#fanboat.co, fanboat@gmail.com
#fanboat 2020-01-17

import config
#import twitter
from twython import Twython
import time
import datetime
import MySQLdb
import sys
import json

def main():
	open_database()
	user = str(sys.argv[1])
	type = str(sys.argv[2])
	t = twitter_login(user)
	tweet = get_new_tweet(type) #get tweet to post
	if tweet != None:
		post = post_tweet(t, tweet) #post the tweet and return feedback
		record_post(post, tweet[0]) #update the database to record the tweet's post time and ID
		print('tweet ' + str(tweet[0]) + ' has been posted.')
	else:
		print('no tweets to post!')

def twitter_login(user): #interface with the twitter api via twython library
	bothkeys = get_access_keys_from_db(user) #set account to post from here (must be authorized and logged in db)
	keys = bothkeys[0]
	appkeys = bothkeys[1]
	access_token_key = keys[0]
	access_token_secret = keys[1]
	app_key = appkeys[0]
	app_secret = appkeys[1]
	t = Twython(
		app_key,
		app_secret,
		access_token_key,
		access_token_secret
		)
	return t

def get_access_keys_from_db(username):
	#print(username)
	cursor = db.cursor()
	keys = ("","")
	appkeys = ("","")
	query = """SELECT u.authkey, u.authsecret
		FROM users u
		WHERE u.username = '{}'""".format(username)
	try:
		cursor.execute(query)
		keys = cursor.fetchone()
	except MySQLdb.Error as e:
		db.rollback()
		print("Error (get_access_keys_from_db)")
	query = """SELECT u.authkey, u.authsecret
		FROM users u
		WHERE u.username = 'fanboatapp'"""
	try:
		cursor.execute(query)
		appkeys = cursor.fetchone()
	except MySQLdb.Error as e:
		db.rollback()
		print("Error (get_access_keys_from_db)")
	cursor.close()
	return keys, appkeys

def open_database(): #connect to db with the tweets
	global db
	db = MySQLdb.connect('localhost', config.dbUsername, config.dbPassword, 'twitter')

def get_new_tweet(type): #obtain a random (or not?) unposted tweet from the database
	cursor = db.cursor()
	body = ''
	id = 0
	replyid = 0
	query = """SELECT t.id, t.body, t.reply
		FROM tweets t
		LEFT JOIN tweets t2 ON t2.id = t.reply
		WHERE t.postdate IS NULL
			AND (t.reply IS NULL OR t2.postdate IS NOT NULL)
			AND t.type = {}
		ORDER BY t.type ASC, RAND()
		LIMIT 1""".format(type)
	try:
		cursor.execute(query)
		tweet = cursor.fetchone()
		id = tweet[0]
		body = str(tweet[1])
		replyid = tweet[2]
	except MySQLdb.Error as e:
		db.rollback()
		print("database error (get_new_tweet). Check if out of unused tweets?")
	cursor.close()
	return id, body, replyid

def post_tweet(t, tweet): #post the provided tweet body (as a reply to the provided tweet id?) and return information (ID, post time)
	body = str(tweet[1])
	if body != '':
		post = t.update_status(status = body)
	else:
		post = None
	return post

def record_post(post, id): #log post's post time and twitter ID in the db
	cursor = db.cursor()
	posttime = datetime.datetime.strptime(post["created_at"],"%a %b %d %H:%M:%S +0000 %Y")
	query = """UPDATE tweets t
		SET t.postdate = '{}', t.twid = '{}'
		WHERE t.id = {}""".format(posttime,post["id"],str(id))
	try:
		cursor.execute(query)
		db.commit()
	except MySQLdb.Error as e:
		db.rollback()
		print("update error (record_post)")
	cursor.close()

if __name__ == '__main__':
        main()
