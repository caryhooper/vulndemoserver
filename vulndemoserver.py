import os
import cherrypy
import base64
import re
import sqlite3
import html
import random
import string

#Portable HTTP server to demonstrate web vulnerabilities
# - CSTI - /csti
# - SQLi (sqlite3) - /sql
#Author - Cary Hooper @nopantrootdance
#Change these configs:
log_file_path = ''
webroot = 'wwwroot/'
PATH = os.path.abspath(webroot)
port = 31337
socket_host = "0.0.0.0"

#To use these, you'll ne a file 'index.html' and 'favicon.ico' within the webroot.
configval = {
	'/' : 
		{
		'tools.staticdir.on' : True,
		'tools.staticdir.dir' : PATH,
		'tools.staticdir.index' : webroot + 'index.html',
		'tools.caching.on' : False,
		'tools.secureheaders.on' : True
		},
	'/favicon.ico' : 
		{
		'tools.staticfile.on' : True,
		'tools.staticfile.filename' : webroot + 'favicon.ico'
		}
}

# Start CherryPy server
# Setup security headers
@cherrypy.tools.register('before_finalize', priority=60)
def secureheaders():
	#No promise these are the most secure config. 
	#Thanks, to Andy (https://github.com/andyacer) for introducing me to CherryPy 
	#and sharing his implementation 
	headers = cherrypy.response.headers
	headers["X-Frame-Options"] = "DENY"
	headers["X-XSS-Protection"] = "1; mode=block"
	headers["Content-Security-Policy"] = "script-src 'self' 'unsafe-inline'"
	headers["Cache-Control"] = "no-cache, no-store"
	headers["Expires"] = "0"
	headers["Pragma"] = "no-cache"
	headers["P3P"] = "CP='Potato'"
	headers["Server"] = "Tesla Model S/2019"
	headers["X-Haiku"] = "CherryPy is fun, but difficult to work with.  This is a haiku."
	cookie = cherrypy.response.cookie
	cookie["Cookie"] = base64.b64encode(b"Here, have a cookie!")


cherrypy.config.update({
	'server.socket_host' : socket_host,
	'server.socket_port' : port,
	'request.show_tracebacks' : False,
	'log.access_file' : log_file_path + "access.log",
	'log.error_file' : log_file_path + "error.log",
	'log.screen' : True
	})

def create_connection(db_file):
	#Connect to sqlite db
	try:
		conn = sqlite3.connect(db_file)
		print(sqlite.version)
	except Error as e:
		print(e)
	finally:
		conn.close()

cstiPreamble = """
<!DOCTYPE html>
<html>
<head>
    <title>CSTI Demo</title>
</head>
<body ng-app="app" ng-controller="demo" bgcolor="#e0dcdc">
    <h1>{{message}}</h1>
    <text>XSS Me!</text>
    <text>Goal: Invoke XSS within this webapp.</text>
    <br><text>Site works best in Chrome</text>
    <script src="angular.1.6.9.min.js"></script>
    <script>
        var app = angular.module('app',[]);
        app.controller('demo', function demo($scope){
            $scope.message="My First AngularJS App";
        });
    </script>
    <br>
    <br>
    """


class Root(object):
	#Create aliases for the same path
	@cherrypy.expose(['csti','CSTI','angular','AngularJS'])
	def generate(self,h00p=None):
		#TODO Check if file exists, then download AngularJS module.


		evilflag = 0
		response = "Unexpected Error<br>"
		if h00p == None:
			response = "<br>Error: h00p is not defined<br>"
		else:
			for badchar in ['<','>','`']:
				if badchar in h00p:
					response = "Character not allowed.<br>"
					evilflag = 1
			if evilflag != 1:
				response = "Hello " + h00p + "<br>"

		return cstiPreamble + response

sqlPreamble = """
<!DOCTYPE html>
<html>
<head><title>SQLi Demo</title></head>
<body bgcolor="#e0dcdc">
    <br><br>
    <h1>Welcome to PWN Depot</h1>
    <h4>Where you can buy just about anything...</h4>
    <img src="pwndepot.png" height="10%" width="10%">
    <br><br>
    <!-- Goal: Find the administrative user's password.-->
    <form action="/pwndepot/store" method="get">
    <div>
        <label for="search">Search:</label>
        <input type="text" id="search" name="search">
    </div>
    <div>
        <input type="submit" value="Go">
    </div><br><br><br>
</form>
<table class="table table-bordered" style='width:100%'>
    <tr align="left">
        <th><u>Item</u></th>
        <th><u>Price</u></th>
        <th><u>Quantity</u></th>   
    </tr>
"""

class Sql(object):
	#Aliases for same path
	@cherrypy.expose(['sql','sqlite','sqlite3','sqli','store'])
	def generate(self, search=None):
		tools = ["adze","Allen","wrench","anvil","axe","bellows","bevel","block","and","tackle","block","plane","bolt","bolt","cutter","brad","brush","calipers","carpenter","chalk","line","chisel","circular","saw","clamp","clippers","coping","saw","countersink","crowbar","cutters","drill","drill","bit","drill","press","edger","electric","drill","fastener","glass","cutter","glue","glue","gun","grinder","hacksaw","hammer","handsaw","hex","wrench","hoe","hone","jig","jigsaw","knife","ladder","lathe","level","lever","machete","mallet","measuring","tape","miter","box","monkey","wrench","nail","nail","set","needle-nose","pliers","nut","Phillips","screwdriver","pickaxe","pin","pincer","pinch","pitchfork","plane","pliers","plow","plumb","bob","poker","pruning","shears","pry","bar","pulley","putty","knife","rasp","ratchet","razor","reamer","rivet","roller","rope","router","ruler","safety","glasses","sand","paper","sander","saw","sawhorse","scalpel","scissors","scraper","screw","screwdriver","scythe","sharpener","shovel","sickle","snips","spade","spear","sponge","square","squeegee","staple","stapler","tack","tiller","tongs","toolbox","toolmaker","torch","trowel","utility","knife","vise","wedge","wheel","woodworker","workbench","wrench"]
		usernames = {'guest':'guest','h00p':'H4ckD@P1aN3t4theW1N','administrator':'iamthesystemadministrator'}

		#Try to connect to DB.  If it doesn't exist, it will create it.
		conn = sqlite3.connect('tools.db')
		cursor = conn.cursor()
		#Try to create tables.  Throw exception if they already exist.
		cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TOOLS'")

		#Create and populate the TOOLS Table
		if cursor.fetchone()[0] != 1:
			print("\n\n\nCreating table: TOOLS\n\n\n")
			cursor.execute('''CREATE TABLE TOOLS (ID INT PRIMARY KEY NOT NULL,
				TOOL TEXT NOT NULL,
				PRICE INT NOT NULL,
				QUANTITY INT NOT NULL);''')
			primarykey = 0
			print("\n\n\nFilling table: TOOLS\n\n\n")
			for tool in tools:
				price = random.randint(1,301)
				qty = random.randint(0,1001)
				statement = "INSERT INTO TOOLS (ID,TOOL,PRICE,QUANTITY) VALUES (" + str(primarykey) + ",'" + tool + "'," + str(price) + "," + str(qty) + ")"
				cursor.execute(statement)
				primarykey += 1
				conn.commit()

			#Now create and populate the USERS table
			cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='USERS'")
			if cursor.fetchone()[0] != 1:
				print("\n\n\nCreating table: USERS\n\n\n")
				cursor.execute('''CREATE TABLE USERS (ID INT PRIMARY KEY NOT NULL,
					USERNAME TEXT NOT NULL,
					PASSWORD INT NOT NULL);
					''')
				primarykey = 0
				print("\n\n\nFilling table: USERS\n\n\n")
				for user in usernames:
					statement = "INSERT INTO USERS (ID,USERNAME,PASSWORD) VALUES (" + str(primarykey) + ",'" + user + "','" + usernames[user] + "')"
					cursor.execute(statement)
					primarykey += 1
					conn.commit()

		#Search function
		if search != None:
			print("SEarch is populated...")
			response = ""
			statement = "SELECT * FROM TOOLS WHERE TOOL LIKE '%" + search + "%' LIMIT 5;"
			cursor.execute(statement)
			#print("Entries retrieved... " + str(len(cursor.fetchall())))
			for i in cursor.fetchall():
				response += "<tr align='left'>\n\t<td>" + str(i[1]) + "</td>\n\t<td>$" + str(i[3]) + "</td>\n\t<td>" + str(i[2]) + "</td>\n</tr>"
			response += "</table></body></html>"
			print(response)
		else:
			response = ""

			#Output the page
		return sqlPreamble + response


cherrypy.tree.mount(Root(),'/', config=configval)
cherrypy.tree.mount(Sql(),'/pwndepot', config=configval)

cherrypy.engine.start()
cherrypy.engine.block()