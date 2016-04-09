#!/usr/bin/env python
from urllib2 import Request, urlopen
from urllib import urlencode
import base64
import json
import requests
import MySQLdb
import datetime
import time

"""
Fill in the entries below
username        - the username you use to log in to app.scanalyticsinc.com.  Typically your e-mail address.
password        - the password you use to log in to app.scanalyticsinc.com.  
clientId        - generate a clientId and secret from https://app.scanalyticsinc.com/developers
clientSecret    - generated along with clientId
array_keys_list - the 5-character array key, visible in the URL when editing a deployment
                - https://app.scanalyticsinc.com/deployments/XXXXX/zones/YYYYY
                - "YYYYY" is the array key
"""

#username        = "user@email.com"
#password        = "password"
#clientId        = "clientId"
#clientSecret    = "clientSecret"
#from credentials import username, password, clientId, clientSecret
array_keys_list = ["1AMDJ"]  # may have one or more array keys in the list

def get_token(username, password, clientId, clientSecret):
    """
    get an oAuth token
    """
    data = {'username':username, 'password':password, "grant_type":"password"}
    values = urlencode(data)
    clientkey = base64.b64encode(clientId+":"+clientSecret)

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic '+clientkey
    }

    request = Request('https://api-v2.scanalyticsinc.com/token', data=values, headers=headers)
    #request = Request('https://api-v2.scanalyticsinc.com/token', headers=headers)

    token = urlopen(request).read()
    #print token
    token_dict=json.loads(token)

    return token_dict["access_token"]

def get_entrances_report(access_token, array_keys_list, ISODATE1, ISODATE2):
    """
    use the token to get visits
    """

    data = {
        "keys": array_keys_list,
        "metrics": ["entrances.entrances","entrances.exits"],
        "interval": None,
        "group" : False,
        "date_range" : {"startDate" : ISODATE1,
                        "endDate"   : ISODATE2}
    }
    values = json.dumps(data)
    #print(values)
    headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer '+access_token
    }
    query_r = requests.post('https://api-v2.scanalyticsinc.com/reports/query', data=values, headers=headers, verify=False)
    #print(query_r.text)

    query_json = query_r.json()
    #print json.dumps(query_json, sort_keys=True, indent=4, separators=(',', ': ')) #pretty 

    report_list = query_json["report"]["collection"]
    return report_list

#def get_available_metrics(access_token):
#    headers = {
#      'Content-Type': 'application/json',
#      'Authorization': 'Bearer '+access_token
#    }
#    query_r = requests.post('https://api-v2.scanalyticsinc.com/metrics?limit=15&page=1', headers=headers, verify=False)
#    print query_r.text


def roundTime(dt=None):
    """Round a datetime object to a multiple of a timedelta
    dt : datetime.datetime object, default now.
    dateDelta : timedelta object, we round to a multiple of this, default 1 minute.
    Author: Thierry Husson 2012 - Use it as you want but don't blame me.
            Stijn Nevens 2014 - Changed to use only datetime objects as variables
    """
    now = datetime.datetime.now()
    if dt == None : dt = now

    return datetime.time(dt.hour,0,0)


def getAndSaveData(db):
    now = datetime.datetime.now()
    thisHourRounded = datetime.datetime.combine(now.date(),roundTime())
    prevHourRounded = datetime.datetime.combine(now.date(),roundTime(now-datetime.timedelta(hours=1)))

    isoDateThisHourRounded = thisHourRounded.isoformat()
    isoDateprevHourRounded = prevHourRounded.isoformat()
    sqlFormatthisHourRounded = datetime.datetime.strftime(thisHourRounded,'%Y-%m-%d %H:%M:%S')
    sqlFormatprevHourRounded = datetime.datetime.strftime(prevHourRounded,'%Y-%m-%d %H:%M:%S')
    
    username = 'tran_h3@denison.edu'
    password = 'makeitcount'
    clientId = '41082c49d21ec03ab278adadca407567585621e5'
    clientSecret = 'e74845de757512ca7d9ca78a809a8d9335ad5d7cebc385c192f71e47d0be9d7a'
    access_token = get_token(username, password, clientId, clientSecret)
    #print "access_token=",access_token
    print(sqlFormatprevHourRounded, " - ", sqlFormatthisHourRounded)
    
    #get_available_metrics(access_token)

    for doc in get_entrances_report(access_token, array_keys_list, isoDateThisHourRounded, isoDateprevHourRounded):
        entrances = doc["entrances"]
        exits = doc["exits"]
        occupancy = entrances - exits
        print(doc["name"])
        print(entrances)
        print(exits)
        print(occupancy)
    
    # Process with list command in db
    c = db.cursor()

    try:
        sql_cmd = "INSERT INTO hourly_traffic (zone_id, zone_name, time_from, time_to, entrances, exits, occupancy) VALUES (1,'Crowne Fitness Center','"+ sqlFormatprevHourRounded + "','" + sqlFormatthisHourRounded + "'," + str(entrances) + "," + str(exits) + "," + str(occupancy) + ")" 
        c.execute(sql_cmd)
        db.commit()
    except Exception as e:
        print(e)
        pass
   
if __name__ == "__main__":
    # Connection to Heroku mysql db
    db=MySQLdb.connect(host="us-cdbr-iron-east-03.cleardb.net",user="bbaf414965fded", passwd="2f3310e8",db="heroku_fa3c47157b8ffc1",charset='utf8',use_unicode=True)

    # Simple scheduler to get and save data every 5 minutes
    #while True:
    getAndSaveData(db)
    #time.sleep(300) # 300s = 1 minutes
    
