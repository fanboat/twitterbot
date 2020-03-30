from twython import Twython
import config
import MySQLdb


APP_KEY = config.consumer_key
APP_SECRET = config.consumer_secret

twitter = Twython(APP_KEY, APP_SECRET)

auth = twitter.get_authentication_tokens(callback_url = "oob")

OAUTH_TOKEN = auth['oauth_token']

OAUTH_TOKEN_SECRET = auth['oauth_token_secret']

user = input('Username:')

print(auth['auth_url'])

# I manually open this url in the browers and
# set oaut_verifier to the value like seen below.

oauth_verifier = input('Enter your pin:')

twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

final_step = twitter.get_authorized_tokens(oauth_verifier)

FINAL_OAUTH_TOKEN = final_step['oauth_token']
FINAL_OAUTH_TOKEN_SECRET = final_step['oauth_token_secret']

twitter = Twython(APP_KEY, APP_SECRET,
                  FINAL_OAUTH_TOKEN, FINAL_OAUTH_TOKEN_SECRET)

print("Final Oath Token, Final Secret")
print(FINAL_OAUTH_TOKEN)
print(FINAL_OAUTH_TOKEN_SECRET)

db = MySQLdb.connect('localhost', config.dbUsername, config.dbPassword, 'twitter')
cursor = db.cursor()
query = """INSERT INTO users (username, authkey, authsecret)
	VALUES ('{}','{}','{}')""".format(user,FINAL_OAUTH_TOKEN,FINAL_OAUTH_TOKEN_SECRET)
try:
	cursor.execute(query)
	db.commit()
	print("Added to database")
except:
	print("el fuck-o")

#print(twitter.verify_credentials())
