#twitterbot-date.py
#looping python bot to post tweets at specific times
#twitter.com/fanboat
#fanboat.co, fanboat@gmail.com
#fanboat 2020-02-17

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
	#t = twitter_login(user)
	#tweet = get_new_tweet(type) #get tweet to post
	#main loop
	while True:
		now = datetime.datetime.utcnow()
		print(' ')
		print('twitterbot-date.py')
		print('Loop Start at time: ' + str(now))
		tweet = get_new_tweet(now)
		if tweet != None and tweet[3] > 0:
			body = tweet[1]
			t = twitter_login(tweet[3])
			if tweet[4] == 1: #if datestamp requested
				body = body + ' ' + str(now.year) + '-' + str(now.month) + '-' + str(now.day)
			if tweet[5] == 1: #if timestamp requested
				body = body + ' ' + str(now.hour) + ':' + str(now.minute) + ':' + str(now.second)
			post = post_tweet(t, tweet, body) #post the tweet and return feedback
			record_post(post, tweet) #update the database to record the tweet's post time and ID
			print('tweet ' + str(tweet[0]) + ' has been posted.')
		else:
			print('no tweets to post!')
		now = datetime.datetime.utcnow()
		print('Loop end at time: ' + str(now))
		print('Wait 55 minutes')
		time.sleep(3300) #wait 55 minutes

def twitter_login(userid): #interface with the twitter api via twython library
	bothkeys = get_access_keys_from_db(userid) #set account to post from here (must be authorized and logged in db)
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

def get_access_keys_from_db(userid):
	#print(username)
	cursor = db.cursor()
	keys = ("","")
	appkeys = ("","")
	query = """SELECT u.authkey, u.authsecret
		FROM users u
		WHERE u.id = {}""".format(userid)
	try:
		cursor.execute(query)
		keys = cursor.fetchone()
	except MySQLdb.Error as e:
		db.rollback()
		print("Error (get_access_keys_from_db)")
	query = """SELECT u.authkey, u.authsecret
		FROM users u
		WHERE u.id = 'fanboatapp'"""
	try:
		cursor.execute(query)
		appkeys = cursor.fetchone()
	except MySQLdb.Error as e:
		db.rollback()
		print("Error (get_access_keys_from_db)")
	cursor.close()
	return keys

def open_database(): #connect to db with the tweets
	global db
	db = MySQLdb.connect('localhost', config.dbUsername, config.dbPassword, 'twitter')

def get_new_tweet(now): #obtain a random (or not?) unposted tweet from the database
	cursor = db.cursor()
	tweet = ('',0,0,0,0,0,0)
	query = """SELECT t.id, t.body, t.reply, t.user,
			CASE WHEN ISNULL(tt.datestamp) = 1 THEN 0 ELSE tt.datestamp END,
			CASE WHEN ISNULL(tt.timestamp) = 1 THEN 0 ELSE tt.timestamp END,
			CASE WHEN ISNULL(tt.annual) = 1 THEN 0 ELSE tt.annual END
		FROM timed_tweets tt
		JOIN tweets t on t.id = tt.twid
		LEFT JOIN tweets t2 ON t2.id = t.reply
		WHERE t.postdate IS NULL
			AND (t.reply is NULL or t2.postdate IS NOT NULL)
			AND t.type = 6
			AND tt.date = CAST('{}' AS DATE)
			AND (tt.time <= CAST('{}' AS TIME) or (tt.time IS NULL AND CAST('13:00:00' AS TIME) < CAST('{}' AS TIME)))
		LIMIT 1""".format(str(now), str(now), str(now))
	try:
		cursor.execute(query)
		tweet = cursor.fetchone()
	except MySQLdb.Error as e:
		db.rollback()
		print("database error (get_new_tweet). Check if out of unused tweets?")
	cursor.close()
	return tweet

def post_tweet(t, tweet, body): #post the provided tweet body (as a reply to the provided tweet id?) and return information (ID, post time)
	if body != '':
		post = t.update_status(status = body)
	else:
		post = None
	return post

def record_post(post, tweet): #log post's post time and twitter ID in the db
	id = tweet[0]
	annual = tweet[6]
	cursor = db.cursor()
	posttime = datetime.datetime.strptime(post["created_at"],"%a %b %d %H:%M:%S +0000 %Y")
	query = """UPDATE tweets t
		SET t.postdate = '{}', t.twid = '{}'
		WHERE t.id = {}""".format(posttime,post["id"],str(id))
	query2 = """UPDATE timed_tweets tt
		SET tt.date = DATE_ADD(tt.date, INTERVAL 1 YEAR)
		WHERE tt.twid = '{}'""".format(str(id))
	try:
		if annual == 0:
			cursor.execute(query)
		else:
			cursor.execute(query2)
		db.commit()
	except MySQLdb.Error as e:
		db.rollback()
		print("update error (record_post)")
	cursor.close()

if __name__ == '__main__':
        main()
