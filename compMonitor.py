#title           :compMonitor.py
#description     :Sends an email alert if people pass a threshold on the Kaggle public leaderboards
#author          :William Cukierski
#date            :2013-05-06
#python_version  :2.7 
#==============================================================================
from bs4 import BeautifulSoup
import urllib2
import numpy as np
import json
import smtplib #For sending emails
import logging
#==============================================================================

# Configure log file
logging.basicConfig(filename="/Users/wcuk/Kaggle/leaderboardScan.log", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Scan started")

# Competition settings (JSON)
# title = URL of competition
# operator = One of {eq = equals, gt = greater than, lt = less than}
# value = threshold to trigger a warning (usually, a perfect score)
s = json.loads("""[
	{"title":"yelp-recsys-2013","operator":"eq","value":0},
	{"title":"yelp-recruiting","operator":"eq","value":0},
	{"title":"kdd-cup-2013-author-disambiguation","operator":"gt","value":0.99},
	{"title":"kdd-cup-2013-author-paper-identification-challenge","operator":"gt","value":0.99},
	{"title":"titanic-gettingStarted","operator":"eq","value":1},
	{"title":"cause-effect-pairs","operator":"gt","value":0.99},
	{"title":"facial-keypoints-detection","operator":"eq","value":0}
	]""")

# Optional: load email creditials from a secrets file
secrets_file = open('/Users/wcuk/Kaggle/secrets.json')
secrets = json.load(secrets_file)
secrets_file.close()

# Email settings
gmail_user = secrets["gmail"]['uname'] #gmail_user = 'x@gmail.com'
gmail_pwd = secrets["gmail"]['pword'] #gmail_pwd = 'hunter2'
FROM = secrets["gmail"]['uname'] #FROM = 'x@gmail.com'
TO = [secrets["gmail"]['uname']] #TO = ['x@gmail.com'] (must be a list)

#==============================================================================

warnings = ""
for competition in range(0,len(s)):

	# Get competition public leaderboard
	try:
		print("Checking " + s[competition]["title"])
		page = urllib2.urlopen("http://www.kaggle.com/c/"+s[competition]["title"]+"/leaderboard")
		soup = BeautifulSoup(page.read())
		allLinks = soup.find_all('abbr', {"class":"score"} )
	except:
		print("Could not resolve competition:" + s[competition]["title"])
		continue

 	# Parse public leaderboard values
 	w = ""
	leaderboardScores = np.zeros(len(allLinks))
	for i in range(0,len(allLinks)):leaderboardScores[i] = float(allLinks[i].string)

	if s[competition]["operator"]=="eq":
	    if  s[competition]["value"] in leaderboardScores:
			w = "WARNING: A score equal to " + str(s[competition]["value"]) + " was found in " + s[competition]["title"]
	elif s[competition]["operator"]=="lt":
		if  s[competition]["value"] > min(leaderboardScores):
			w = "WARNING: A score less than " + str(s[competition]["value"]) + " was found in " + s[competition]["title"]
	elif s[competition]["operator"]=="gt":
		if  s[competition]["value"] < max(leaderboardScores):
			w = "WARNING: A score greater than " + str(s[competition]["value"]) + " was found in " + s[competition]["title"]
	if w != "":
		print(w)
		warnings = warnings + "\n" + w
	
if warnings != "":	# Send email
	logging.error(warnings)
	TEXT = "The following issues were found during an automated scan of Kaggle's public leaderboard scores:\n" + warnings
	SUBJECT = "Kaggle Leaderboard Police - Scan Result"
	message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
	""" % (FROM, ", ".join(TO), SUBJECT, TEXT)
	try:
	    server = smtplib.SMTP("smtp.gmail.com", 587) #or port 465 doesn't seem to work!
	    server.ehlo()
	    server.starttls()
	    server.login(gmail_user, gmail_pwd)
	    server.sendmail(FROM, TO, message)
	    server.close()
	    print("Email sent.")
	except:
	    print("Failed to send email.")
else:
	logging.info("No warnings found")

