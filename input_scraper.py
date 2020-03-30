#input_scraper.py
#simple python bot to record tweets
#twitter.com/rysinput, mstinput1
#fanboat.co, fanboat@gmail.com
#fanboat 2020-01-17

#params [username] [tweet_type]

import config
#import twitter
from twython import Twython
import time
import datetime
import MySQLdb
import sys
import json
import string

def main():
	user = str(sys.argv[1])
	type = str(sys.argv[2])
	open_database()
	userinfo = twitter_login(user)
	t = userinfo[0]
	userid = userinfo[1]
	scrape_tweets(t, user, type, userid)
	print('Scrape complete for {}.'.format(user))

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
	return t, keys[2]

def get_access_keys_from_db(username):
	cursor = db.cursor()
	keys = ("","")
	appkeys = ("","")
	query = """SELECT u.authkey, u.authsecret, u.input_for
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

def scrape_tweets(t, user, type, userid): #Check the input account for new tweets and record them to the db
	body = ''
	id = ''
	since_id = str(get_since_id(user)).replace("('","").replace("',)","")
	#print("since_id = " + since_id) #why is the since_id parameter not working on the API call?
	#tweets = t.request("https://api.twitter.com/1.1/statuses/user_timeline.json", "GET", {'screen_name':user}, {'since_id':int(since_id)})
	#previous line was old approach I guess? Getting tweets l>140 requires following approach. since_id worth revisiting.
	tweets = t.get_user_timeline(screen_name = user, tweet_mode = 'extended')
	time.sleep(5)
	i = 0
	for tweet in tweets:
		i+=1
		#print(str(tweet))
		if i < 15: #just do 14 at a time
			body = tweet["full_text"].replace('&amp;','&')
			print("INSERTING: " + body) #must use "full_text", not "text" or cause error when tweet_mode = 'extended'
			insert_tweet(body,tweet["id_str"],t,type,userid) #logs tweet into db, deletes from input timeline
			#t.destroy_status(id = int(tweet["id_str"])) #deletes from input timeline
			time.sleep(5) #make sure we avoid rate limiting

def get_since_id(user):
	cursor = db.cursor()
	since_id = 1
	query = """SELECT MAX(inputtwid)
		FROM tweets
		WHERE type = 1"""
	try:
		cursor.execute(query)
		since_in = cursor.fetchone()
		if since_in is not None:
			since_id = since_in
		else:
			since_id = 1
	except MySQLdb.Error as e:
		db.rollback()
		print("Error (get_since_id)")
	cursor.close()
	return since_id

def insert_tweet(body, id, t, type, userid): #Record tweet to database
	cursor = db.cursor()
	query = """INSERT INTO tweets
		(body, inputtwid, type, user) VALUES
		('{}','{}',{},{})""".format(body.replace("'","''"),id,type,userid)
	try:
		cursor.execute(query)
		db.commit()
		t.destroy_status(id = int(id)) #deletes from input timeline
	except MySQLdb.Error as e:
		db.rollback()
		print("update error (insert_tweet)")
	#except:
	#	print("update error (insert_tweet) Tweet should remain on input timeline")
	cursor.close()

if __name__ == '__main__':
        main()
