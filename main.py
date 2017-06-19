#Packages:
import psycopg2
import sys
import datetime
import pprint
import urllib,urllib2
from collections import defaultdict

#Lists:
checked = [] #this is used later on, to delete obsolete entries

#Dictionaries:
uniprotdata = defaultdict(str) #creating empty dictionary with Uniprot Accession number and uniprotID(to link with the db)
seqDict = defaultdict(str) #contains uniprot accession and length

#Export for the log files:
export = open("log{0}.csv".format(datetime.date.today()), "w") #keeping a log file
export.write("ProteinUpDate (YY-MM-DD):,{0}\n".format(datetime.date.today())) #Header

#Parameters: To keep the main structure of API to work (email address is needed).
params = {
'from':'ID',
'to':'P_REFSEQ_AC',
'format':'tab',
'query':''
}

#Functions:
def uniprotAPI(acc_n): #Defining uniprotAPI
	"Creates a call to the API with the given UniProtAC (acc_n) to return the length of a protein."
	settings = urllib.urlencode(params) #calling parameters
	try: #tries to call the API.
		url = 'http://www.uniprot.org/uniprot/{0}.fasta'.format(acc_n) #URL format to include isoforms
		request = urllib2.Request(url, settings)
		contact = "email" # Please set your email address here to help us debug in case of problems.
		request.add_header('User-Agent', 'Python %s' % contact)
		response = urllib2.urlopen(request)
		header = response.readline() #taking the first line
		head = header.split("|")
		accession = head[1] #taking the accession number
		# print(type(response))
	except urllib2.HTTPError: #if API call fails, it displays which one of the entry has a problem
		print("There is an error for the {0} entry".format(acc_n))
		export.write("Error with API for {0}, please check manually at http://www.uniprot.org/uniprot/{0}.fasta \n".format(acc_n))
		accession = "error" #returns error so that db is not updated.

	return(accession)


#Connection to the DB: Useful > https://www.youtube.com/watch?v=Z9txOWCWMwA, https://wiki.postgresql.org/wiki/Using_psycopg2_with_PostgreSQL
conn_string = "host='localhost' dbname='unicarbkb' user='postgres'"

# get a connection, if a connect cannot be made an exception will be raised here
conn = psycopg2.connect(conn_string)

# conn.cursor will return a cursor object, you can use this cursor to perform queries
cur = conn.cursor()

#To select the table:
cur.execute("SELECT * FROM uckb.uniprot")
data = cur.fetchall()

#Main Loop 1:
for line in data: #for each line in the database
	dbuniprotAC = line[1] #uniprot Accession
	realuniprotAC = uniprotAPI(dbuniprotAC) #uniprotAPI to get the realuniprotAC
	if dbuniprotAC != realuniprotAC and realuniprotAC != "error": #if they are not the same, and the API didn't give an error
		cur.execute("UPDATE uckb.uniprot SET uniprot=%s WHERE uniprot=%s",(realuniprotAC,dbuniprotAC)) #updated the db with the real accession from uniprot
		export.write("Entry {0} has been updated to {1}\n".format(dbuniprotAC,realuniprotAC))

#Closing:
conn.commit() #Saves changes in the database.
cur.close()
conn.close()
