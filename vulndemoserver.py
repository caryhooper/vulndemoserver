#!/usr/bin/python3
import os,base64,random,subprocess
import cherrypy
import sqlite3
import pdfkit
from weasyprint import HTML
import time
#Portable HTTP server to demonstrate web vulnerabilities
#Author - Cary Hooper @nopantrootdance
#Todo: Blind SQLi, XXE, 2nd order SQLi, Vue template injection, React injection? 

#Change these configs:
log_file_path = ''
if os.name == 'nt':
	webroot = 'wwwroot\\'
	isWindows = True
else:
	webroot = 'wwwroot/'
	isWindows = False
PATH = os.path.abspath(webroot)
port = 31337
#To bind on all ports, change this to: socket_host = "0.0.0.0" #AKA the "I like to live dangerously" option
socket_host = "0.0.0.0"
#Change the SQL flavor here (to be used in conjunction with MSSQL server docker container):
#For , see comments in create_connection_DBMS():
DBMS = "sqlite3"
#DBMS = "mssql"

#To use these, you'll need a file 'index.html' and 'favicon.ico' within the webroot.
configval = {
	'/' : 
		{
		'tools.staticdir.on' : True,
		'tools.staticdir.dir' : PATH,
		'tools.staticdir.index' : 'index.html',
		'tools.caching.on' : False,
		'tools.secureheaders.on' : True
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
	#headers["X-Frame-Options"] = "DENY"
	headers["X-XSS-Protection"] = "1; mode=block"
	headers["Content-Security-Policy"] = "script-src 'self' 'unsafe-inline' 'unsafe-eval'"
	headers["Cache-Control"] = "no-cache, no-store"
	headers["Expires"] = "0"
	headers["Pragma"] = "no-cache"
	headers["P3P"] = "CP='Potato'"
	headers["Server"] = "Tesla Model S/2019"
	#Need ACAO = * for cross-origin SSRF Exploits
	headers["Access-Control-Allow-Origin"] = "*"
	headers["X-Haiku"] = "CherryPy is fun, but difficult to work with.  This is a haiku."
	cookie = cherrypy.response.cookie
	cookie["Cookie"] = base64.b64encode(b"Here, have a cookie!").decode()

#Log File Settings
cherrypy.config.update({
	'server.socket_host' : socket_host,
	'server.socket_port' : port,
	'request.show_tracebacks' : False,
	'log.access_file' : log_file_path + "access.log",
	'log.error_file' : log_file_path + "error.log",
	'log.screen' : True
	})

def create_connection_mssql():
	#docker pull mcr.microsoft.com/mssql/server
	#docker run -e 'ACCEPT_EULA=Y' -e 'SA_PASSWORD=Password123' -p 1433:1433 -d mcr.microsoft.com/mssql/server	
	#Note... need to create database pwndepot
	#CREATE DATABASE pwndepot
	print("Connecting to MSSQL")
	import pyodbc
	cxnstring = f'DRIVER={{FreeTDS}};SERVER=127.0.0.1;PORT=1433;UID=sa;PWD=Password123'
	conn = pyodbc.connect(cxnstring)
	cursor = conn.cursor()
	# cursor.execute("CREATE DATABASE pwndepot")
	# cursor.execute("USE pwndepot")
	return conn

def create_connection_sqlite3(db_file):
	#Connect to sqlite db
	print("Connecting to sqlite3")
	try:
		conn = sqlite3.connect(db_file)
		print(sqlite3.version)
		return conn
	except Exception as e:
		print(e)

def initialize_db(db_file):
	#Creates the sqlite3 database if it does not exist already).
	#Try to create tables.  Throw exception if they already exist.
	tools = ["adze","allen wrench","wrench","anvil","axe","bellows","bevel","block","tackle","block","plane","bolt","bolt","cutter","brad","brush","calipers","carpenter","chalk","line","chisel","circular","saw","clamp","clippers","coping","countersink","crowbar","cutters","drill","drill","bit","drill","press","edger","electric","drill","fastener","glass","cutter","glue","glue","gun","grinder","hacksaw","hammer","handsaw","hex","wrench","hoe","hone","jig","jigsaw","knife","ladder","lathe","level","lever","machete","mallet","measuring","tape","miter","box","monkey","wrench","nail","nail","set","needle-nose","pliers","nut","Phillips","screwdriver","pickaxe","pin","pincer","pinch","pitchfork","plane","pliers","plow","plumb","bob","poker","pruning","shears","pry","bar","pulley","putty","knife","rasp","ratchet","razor","reamer","rivet","roller","rope","router","ruler","safety","glasses","sand","paper","sander","saw","sawhorse","scalpel","scissors","scraper","screw","screwdriver","scythe","sharpener","shovel","sickle","snips","spade","spear","sponge","square","squeegee","staple","stapler","tack","tiller","tongs","toolbox","toolmaker","torch","trowel","utility","knife","vise","wedge","wheel","woodworker","workbench","wrench","DIY DIRTY BOMB KIT"]
	usernames = {'guest':'guest','h00p':'H4ckD@P1aN3t4theW1N','administrator':'iamthesystemadministrator'}

	#Create Connection
	if DBMS == "sqlite3":
		conn = create_connection_sqlite3(db_file)
	else:
		conn = create_connection_mssql()
	
	#Create tools table
	cursor = conn.cursor()
	if DBMS == "sqlite3":
		query = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='TOOLS'"
	else:
		query = "SELECT COUNT(*) FROM pwndepot..sysobjects WHERE xtype = 'U' and name = 'tools'"
	cursor.execute(query)
	result = cursor.fetchone()[0]
	#print(f"Create tools table {result}")

	#Create tools if a table doesn't exist
	if result != 1:
		print("\n\n\nCreating table: TOOLS\n\n\n")
		
		if DBMS == "sqlite3":
			cursor.execute('''CREATE TABLE TOOLS (ID INT PRIMARY KEY NOT NULL,
			TOOL TEXT NOT NULL,
			PRICE TEXT NOT NULL,
			QUANTITY TEXT NOT NULL);''')
		else:
			#CREATE TABLE pwndepot..tools (tool_id INT PRIMARY KEY,name VARCHAR (50) NOT NULL,price VARCHAR (50) NOT NULL,quantity VARCHAR (50) NOT NULL);
			cursor.execute('''CREATE TABLE pwndepot..tools (
				tool_id INT PRIMARY KEY,
				name VARCHAR (50) NOT NULL,
				price VARCHAR (50) NOT NULL,
				quantity VARCHAR (50) NOT NULL);''')
	
	#Is the tools table populated?
	if DBMS == "sqlite3":
		query = "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='TOOLS'"
	else:
		query = "SELECT COUNT(*) FROM pwndepot..tools"
	cursor.execute(query)
	result = cursor.fetchone()[0]
	#print(f"Populate tools table {result}")

	#If not, populate tools
	if result < 1:
		primarykey = 0
		print("\n\n\nFilling table: TOOLS\n\n\n")
		for tool in tools:
			price = random.randint(1,301)
			qty = random.randint(0,1001)
			if tool == "DIY DIRTY BOMB KIT":
				print(f"Adding flag! {str(primarykey)}")
				price = "YouFoundTheFlag."
				qty = "Congrats!"
			if DBMS == "sqlite3":
				statement = "INSERT INTO TOOLS (ID,TOOL,PRICE,QUANTITY) VALUES (" + str(primarykey) + ",'" + tool + "','" + str(price) + "','" + str(qty) + "')"
			else:
				statement = f"INSERT INTO pwndepot..tools (tool_id,name,price,quantity) VALUES ({primarykey},'{tool}','{price}','{qty}')"
			cursor.execute(statement)
			print("Added tool with primarykey " + str(primarykey))
			primarykey += 1
			conn.commit()

	#Now create and populate the USERS table
	if DBMS == "sqlite3":
		query = "SELECT count(name) FROM sqlite_master WHERE type='table' AND name='USERS'"
	else:
		query = "SELECT COUNT(*) FROM pwndepot..sysobjects WHERE xtype = 'U' and name = 'users'"
	cursor.execute(query)
	result = cursor.fetchone()[0]
	#print(f"Create users table {result}")

	if result == 0:
		print("\n\n\nCreating table: USERS\n\n\n")
		if DBMS == "sqlite3":
			cursor.execute('''CREATE TABLE USERS (ID INT PRIMARY KEY NOT NULL,
			USERNAME TEXT NOT NULL,
			PASSWORD INT NOT NULL)''')
		else:
			#CREATE TABLE pwndepot..users (user_id INT PRIMARY KEY,username VARCHAR (50) NOT NULL,password VARCHAR (50) NOT NULL);
			cursor.execute('''CREATE TABLE pwndepot..users (
				user_id INT PRIMARY KEY,
				username VARCHAR (50) NOT NULL,
				password VARCHAR (50) NOT NULL)''')
	
	if DBMS == "sqlite3":
		query = "SELECT count(*) FROM USERS"
	else:
		query = "SELECT COUNT(*) FROM pwndepot..tools"
	cursor.execute(query)
	result = cursor.fetchone()[0]
	#print(f"Populate users table {result}")

	if result < 1:
		primarykey = 0
		print("\n\n\nFilling table: USERS\n\n\n")
		for user in usernames:
			if DBMS == "sqlite3":
				statement = f"INSERT INTO USERS (ID,USERNAME,PASSWORD) VALUES ({primarykey},'{user}','{usernames[user]}')"
			else:
				statement = f"INSERT INTO pwndepot..users (user_id,username,password) VALUES ({primarykey},'{user}','{usernames[user]}')"
			cursor.execute(statement)
			primarykey += 1
			conn.commit()
	return conn

def getPreamble(attack,level,extra="",technology=""):
	if attack == "xss":
		extra = ""
		xssPreamble = f"""<!DOCTYPE html>
			<html>
			<head>
			    <title>XSS Demo ({level})</title>
			</head>
			<body ng-app="app" ng-controller="demo" bgcolor="#e0dcdc">
			    <h1>{{{{message}}}}</h1>
			    <text>AngularJS Demo ({level})</text><br>
			    <text>Goal: Invoke XSS within this app.</text>
			    <br><br><text>Site works best in Chrome</text>
			    <div align="left"><br><a href="/index.html">Go back to index.html</a><br></div>
			    <script src="angular.1.6.9.min.js"></script>
			    <script>
			        var app = angular.module('app',[]);
			        app.controller('demo', function demo($scope){{
			            $scope.message="Welcome to My First AngularJS Site";
			        }});
			    </script>{extra}<br><br>"""
		return xssPreamble
	if attack == "sqli":
		sqlPreamble = f"""<!DOCTYPE html>
			<html>
			<head><title>SQLi Demo ({level})</title></head>
			<body bgcolor="#e0dcdc">
			    <br><br>
			    <h1>Welcome to PWN Depot ({level})</h1>
			    <h4>Where you can buy just about anything...</h4>
			    <div align="left"><br><a href="/index.html">Go back to index.html</a><br></div>
			    <img src="../pwndepot.png" height="10%" width="10%">
			    <br>
			    {technology}
			    <form action="/{extra}" method="get">
			    <div>
			        <label for="search">Search:</label>
			        <input type="text" id="search" name="search">
			        <input type="submit" value="Go">
			    </div>
			    <div>
			        <br><label>Example: saw</label>
			    </div><br><br><br>
			</form>
			<table class="table table-bordered" style='width:100%'>
			    <tr align="left">
			        <th><u>Item</u></th>
			        <th><u>Price</u></th>
			        <th><u>Quantity</u></th>   
			    </tr>
		"""
		return sqlPreamble
	if attack == "crypto":
		weakCryptoPreamble = f"""<!DOCTYPE html>
			<html>
			<head><title>Weak Crypto Demo ({level})</title></head>
			<body bgcolor="#e0dcdc">
			    <br><br>
			    <h1>PWN Depot Token Generator ({level})</h1>
			    <h3>We use world-class 256-bit encryption to protect your transactions. </br> 
			    Don't believe us? We'll prove it to you.  There is surely no way to leak </br>
			    our account number! The smartest scientists in the world invented this stuff, right? </br>
			    </h3>
			   	<div align="left"><br><a href="/index.html">Go back to index.html</a><br></div>
			    <img src="../pwndepot.png" height="10%" width="10%">
			    <ol>
			    	<h4>Input your name.</h4>
			    	<h4>We'll append our 16-digit Bank account number and encrypt it with our world-class AES ECB encryption algorithm.</h4>
			    	<h4>Receive the encrypted value below!</h4>
			    </ol><br><br>
				<form action="/crypto" method="get">
				    <div>
				        <label for="name">Enter your name:</label>
				        <input type="text" name="name">
				        <input type="submit" value="Go">
				    </div><br>
				</form>"""
		return weakCryptoPreamble
	if attack == "cmdi":
		cmdiPreamble = f"""<!DOCTYPE html>
			<html>
			<head><title>Weak Crypto Demo ({level})</title></head>
			<body bgcolor="#e0dcdc">
			    <br><br>
			    <h1>PWN Depot Server Status Manager ({level})</h1>
			    <h3>Warning: for sysadmins only!</br> 
			    The unauthorized use of this information system is prohibited.</br>
			    </br>
			    </h3>
			   	<div align="left"><br><a href="/index.html">Go back to index.html</a><br></div>
			    <img src="../pwndepot.png" height="20%" width="20%">
			    <ol>
			    	<h4>{extra}</h4>
			    </ol><br><br>
				<form action="/serverstatus" method="get">
				    <div>
				        <label for="name">Enter a server IP address:</label>
				        <input type="text" name="server">
				        <input type="submit" value="Go">
				    </div><br>
				</form>"""
		return cmdiPreamble
	if attack == "ssrf":
		ssrfPreamble =  f"""<html>
				<head>
					<title>SSRF Demo ({level})</title>
				</head>
				<body bgcolor="#e0dcdc">
					<h1>Generate a PDF ({level})</h1>
					<h3>Using {technology}</h3>
					<img src="../pwndepot.png" height="10%" width="10%"><br>
					<form action="/{extra}" id="pdfform" method="post">
						File Name: <input type="text" name="filename">
						<input type="submit">
					</form>
					<textarea rows="4" cols="50" name="html" form="pdfform">Enter HTML here.</textarea>
				</body>
			  </html>"""
		return ssrfPreamble

class PwnDepot(object):

#XSS{
	pages = ['XSS','CSS','css']
	@cherrypy.expose(pages)
	def xss(self,h00p=None,**params):
		#DEMO - Simple XSS
		#Goal: Invoke JavaScript through XSS within a GET parameter
		#http://127.0.0.1:31337/xss?h00p=%3Cscript%3Ealert(1)%3C/script%3E
		xssPreamble = getPreamble("xss",1)
		response = "Unexpected Error<br>"
		if h00p == None:
			response = "<br><code>Error: h00p is not defined</code><br>"
		else:
			response = f"Hello {h00p}!<br>"
		return xssPreamble + response

	pages = ['XSS2','CSS2','css2']
	@cherrypy.expose(pages)
	def xss2(self,h00p=None,**params):
		#DEMO - Simple XSS 2
		#Goal: Invoke JavaScript through XSS within a GET parameter
		#http://127.0.0.1:31337/xss2?h00p=%3Cimage%20src=x%20onerror=alert(1)%3E
		xssPreamble = getPreamble("xss",2)
		evilflag = 0
		response = "Unexpected Error<br>"
		if h00p == None:
			response = "<br>Error: h00p is not defined<br>"
		else:
			for badchar in ['script','onload','img']:
				if badchar in h00p.lower():
					response = "String not allowed (script,onload,img).<br>"
					evilflag = 1
			if evilflag != 1:
				response = f"Hello {h00p}!<br>"
		return xssPreamble + response

	pages = ['XSS3','CSS3','css3']
	@cherrypy.expose(pages)
	def xss3(self,h00p=None,**params):
		#DEMO - Simple XSS 3
		#Goal: Invoke JavaScript through XSS within a GET parameter
		#Create aliases for the same path
		#http://127.0.0.1:31337/xss3?h00p=%3Csvg//onload=alert`1`%3E
		xssPreamble = getPreamble("xss",3)
		evilflag = 0
		response = "Unexpected Error<br>"
		if h00p == None:
			response = "<br>Error: h00p is not defined<br>"
		else:
			for badchar in ['\'','"',' ','(',')']:
				if badchar in h00p.lower():
					response = "Character not allowed (',\",space,()).<br>"
					evilflag = 1
			if evilflag != 1:
				response = f"Hello {h00p}!<br>"
		return xssPreamble + response

	pages = ['CSTI','AngularJS']
	@cherrypy.expose(pages)
	def csti(self,h00p=None,**params):
		#DEMO - Client Side Template Injection
		#Goal: Invoke JavaScript through an AngularJS Template within a GET parameter
		#Create aliases for the same path
		#TODO Check if file exists, then download AngularJS module.
		#http://127.0.0.1:31337/xss2?h00p={{constructor.constructor(%22alert(1)%22)()}}
		extra = "<p>Note: input is sanitized with a function similar to PHP's htmlspecialchars.</p>"
		xssPreamble = getPreamble("xss",4,extra)
		response = "Unexpected Error<br>"
		if h00p == None:
			response = "<br>Error: h00p is not defined<br>"
		else:
			#This for loop emulates PHP's htmlspecialchars()
			badchardict = {
				'<':'&lt;',
				'>':'&gt;',
				'&':'&amp;',
				'"':'&quot;',
				'\'':'&#039'
			}
			for key,value in badchardict.items():
				if key in h00p:
					h00p = h00p.replace(key,value)
			response = "Hello " + h00p + "<br>"
		return xssPreamble + response
#}

#SSRF in PDF Generation{
	pages = ['SSRF','pdfgen']
	@cherrypy.expose(pages)
	def ssrf(self,html=None,filename=None,**params):
		#DEMO - SSRF 1 
		#Goal: abuse the PDF generation functionality to forge a HTTP request from the server
		#Note: this module requires wkhtmltopdf.  Install with pip and
		#apt-get install wkhtmltopdf
		#<iframe src="http://j8ss5y0ayf4502ssu8zlbosip9vzjo.burpcollaborator.net" width="500px" height="500px"></iframe>
		if html == None:
			#Input HTML (POST)
			response = getPreamble("ssrf",1,extra="pdfgen",technology="wkhtmltopdf")
		else:
			#Output link to PDF.
			if (os.path.isdir(PATH + "/pdf")):
				print("pdf directory exists.  ")
			else:
				if isWindows:
					os.mkdir(PATH + '\\pdf')
				else:
					os.mkdir(PATH + '/pdf')

			if filename != None:
				if ".pdf" in filename:
					pdfname = filename
				else:
					pdfname  = filename + ".pdf"
			else:
				pdfname = "test.pdf"
			pdfkit.from_string(html,f"{PATH}/pdf/{pdfname}")
			response = "<html><body>Please view your PDF at this <a href=\"pdf/"+pdfname+"\">link.</a></body></html>"
		return response


	pages = ['SSRF2','pdfgen2']
	@cherrypy.expose(pages)
	def ssrf2(self,html=None,filename=None,**params):
		#DEMO - SSRF 2 / LFI
		#Goal: abuse the PDF generation functionality to read secret file located at C:\Temp\admin.log
		#Note: this module requires weasyprint.  Installation instructions here:
		#https://weasyprint.readthedocs.io/en/stable/install.html
		#Installation is a bit involved, but I promise it's worth it.
		#Need to fix <a href="file://c:/TEMP/admin.log" rel="attachment">harmless link</a>
		if html == None:
			#Input HTML (POST)
			response = getPreamble("ssrf",2,"pdfgen2","WeasyPrint")
		else:
			#Output link to PDF.
			if (os.path.isdir("wwwroot/pdf")):
				print("pdf directory exists.  ")
			else:
				os.mkdir('wwwroot/pdf')
			if filename != None:
				if ".pdf" in filename:
					pdfname = filename
				else:
					pdfname  = filename + ".pdf"
			else:
				pdfname = "test.pdf"
			html = HTML(string=html)
			html.write_pdf(f"{PATH}/pdf/{pdfname}")
			response = f"<html><body>Please view your PDF at this <a href=\"pdf/{pdfname}\">link.</a></body></html>"
		return response

	pages = ['SSRF3','pdfgen3']
	@cherrypy.expose(pages)
	def ssrf3(self,html=None,filename=None,**params):
		#DEMO - SSRF 3 / RCE
		#Goal: abuse the PDF generation functionality to execute JavaScript on the server
		#Note: this module requires Chrome.  Point to a local chrome install
		#Watch out... this modules requires full paths to EXEs/binaries
		#<h1>inject</h1><script>document.write(123)</script>
		if html == None:
			#Input HTML (POST)
			response = getPreamble("ssrf",3,"pdfgen3","Headless Chrome")
		else:
			#Output link to PDF.
			response = ""
			if (os.path.isdir(f"{PATH}/pdf")):
				pass
			else:
				os.mkdir(f'{PATH}/pdf')
			if filename != None:
				if ".pdf" in filename:
					pdfname = filename
				else:
					pdfname  = filename + ".pdf"
			else:
				pdfname = "test.pdf"

			if isWindows:
				CHROME_PATH = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe" 
			else:
				CHROME_PATH = "/usr/bin/google-chrome-stable"

			tempname = filename.split('.')[0] + '.html'
			if isWindows:
				pdfpath = f"{PATH}\\pdf\\"
			else:
				pdfpath = f"{PATH}/pdf/"
			file = open(f"{pdfpath}{tempname}",'w+')
			print(f"DEBUG - Writing {html} to file {pdfpath}{tempname}")
			file.write(html)
			file.close()
			#"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --headless --disable-gpu --print-to-pdf="C:\Temp\a.pdf" --no-margins file:///C:/Users/Cary/Documents/Programming/Python/vulndemoserver/wwwroot/pdf/foobar.html
			if isWindows:
				execarray = [CHROME_PATH, "--headless", "--disable-gpu", "--no-sandbox", "--user-data-dir",f"--print-to-pdf={pdfpath}{pdfname}", "--no-margins", f"file:///{pdfpath}{tempname}"]
			else:
				execarray = [f"{CHROME_PATH} --headless --disable-gpu --no-sandbox --user-data-dir --print-to-pdf={pdfpath}{pdfname} --no-margins file:///{pdfpath}{tempname}"]

			p = subprocess.Popen(execarray,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
			#DEBUG Purposes Only
			stdout, stderr = p.communicate()
			retcode = p.returncode
			if retcode != 0:
				foo = f"DEBUG - stderr {stderr}"
				bar = f"DEBUG - stdout {stdout}"
				response += foo + "<br><br>" + bar + "<br><br>"
				response += f"DEBUG - returncode {retcode}"
			time.sleep(2)
			response = f"<html><body>Please view your PDF at this <a href=\"pdf/{pdfname}\">link.</a></body></html>"
		return response

	pages = ['secret']
	@cherrypy.expose(pages)
	def secret(self,**params):
		#Secret to exfiltrate in SSRF modules
		#<iframe src="http://127.0.0.1:31337/secret"><iframe>
		response = "{'Message':'Top Secret - Unauthorized Access is Not Allowed','key':'5ebe2294ecd0e0f08eab7690d2a6ee69'}"
		return response
#}

#Crypto{
	pages = ['ECB','crypto']
	@cherrypy.expose(pages)
	def ecb(self,name=None,**params):
		#DEMO - Weak Encryption Implementation
		#Goal: Leak the account number from the web site
		weakCryptoPreamble = getPreamble("crypto",1)
		from Crypto.Cipher import AES
		from Crypto.Util.Padding import pad, unpad
		#uses pycryptodome
		import binascii 
		SECRET_ACCT_NUMBER = "ML031337-8675309"
		response ="""<h3><b>The Encrypted Value is: <code>"""

		def raw2hex(value):
		    return binascii.hexlify(value)
		def do_encrypt(inputname):
			key = "8d127684cbc37c17616d806cf50473cc" #16bytes
			#Note: this is crackable with a brute-force attack md5(rockyou.txt)
			plaintext = f"{inputname}:{SECRET_ACCT_NUMBER}".encode('utf-8')
			encryptor = AES.new(bytes.fromhex(key),AES.MODE_ECB)
			plaintext_pad = pad(plaintext,16)
			ciphertext = encryptor.encrypt(plaintext_pad)
			ciphertext_x = raw2hex(ciphertext).decode()
			return ciphertext_x
		if name == None:
			response = response + "ENCRYPTED VALUE HERE"
		else:
			ciphertext = do_encrypt(name)
			response += ciphertext
		return weakCryptoPreamble + response + "</code></b><h3></body></html>"
#}

#SQLi {
	pages = ['sql','sqli','store']
	@cherrypy.expose(pages)
	def pwndepot(self, search=None, **params):
		#DEMO - SQL Injection
		#Level 1 - Dump the contents of the tools database.
		#Try to connect to DB.  If it doesn't exist, it will create it.
		#http://127.0.0.1:31337/pwndepot2?search=saw%27%20OR%201==1%3b--
		goal = " Goal: dump the contents of the tools table to find the secret tools."
		sqlPreamble = getPreamble("sqli",1,"pwndepot",goal)
		
		conn = initialize_db('tools.db')
		cursor = conn.cursor()

		#Search function
		if search != None:
			response = ""
			if DBMS == "sqlite3":
				statement = f"SELECT * FROM TOOLS WHERE TOOL LIKE '%{search}%' LIMIT 5;"
			else:
				statement = f"SELECT TOP 5 * FROM pwndepot..tools WHERE name LIKE '%{search}%'"
			print(f"\nExecuting: {statement}\n")
			cursor.execute(statement)
			for i in cursor.fetchall():
				response += "<tr align='left'>\n\t<td id='tool'>" + str(i[1]) + "</td>\n\t<td id='price'>$" + str(i[3]) + "</td>\n\t<td id='quantity'>" + str(i[2]) + "</td>\n</tr>"
			response += "</table></body></html>"
		else:
			response = ""

			#Output the page
		
		return sqlPreamble + response

	pages = ['sql2','sqli2','store2']
	@cherrypy.expose(pages)
	def pwndepot2(self, search=None, **params):
		#DEMO - SQL Injection 2
		#Level 2 - Using a UNION attack, read the contents of another table.
		#http://127.0.0.1:31337/pwndepot2?search=saw%27%20UNION%20SELECT%201,2,3,4%3b--
		goal = " Goal: find the administrator password."
		sqlPreamble = getPreamble("sqli",2,"pwndepot2",goal)

		conn = initialize_db('tools.db')
		cursor = conn.cursor()

		#Search function
		if search != None:
			response = ""
			if DBMS == "sqlite3":
				statement = f"SELECT * FROM TOOLS WHERE TOOL LIKE '%{search}%' LIMIT 5;"
			else:
				statement = f"SELECT TOP 5 * FROM pwndepot..tools WHERE name LIKE '%{search}%'"
			print(f"\nExecuting: {statement}\n")
			cursor.execute(statement)
			for i in cursor.fetchall():
				response += "<tr align='left'>\n\t<td id='tool'>" + str(i[1]) + "</td>\n\t<td id='price'>$" + str(i[3]) + "</td>\n\t<td id='quantity'>" + str(i[2]) + "</td>\n</tr>"
			response += "</table></body></html>"
		else:
			response = ""

		return sqlPreamble + response

	pages = ['sql3','sqli3','store3']
	@cherrypy.expose(pages)
	def pwndepot3(self, search=None, **params):
		#DEMO - SQL Injection 3
		#Filters on SQL verbs/words
		#Level3 - Using a UNION attack, bypass SQLi filters to read the contents of another table.
		#http://127.0.0.1:31337/pwndepot3?search=saw%27%20UnION%20SElECT%201,2,3,4%3b--
		goal = " Goal: bypass filters and find the administrator password."
		sqlPreamble = getPreamble("sqli",3,"pwndepot3",goal)

		conn = initialize_db('tools.db')
		cursor = conn.cursor()

		#Search function
		evilflag = 0
		evilwords = ["select","SELECT","FROM","from","WHERE","where","UNION","union"]
		response = ""
		if search != None:
			for evilword in evilwords:
				if evilword in search:
					evilflag = 1
					response = "Mischief detected! SQL Injection attempt logged."

			if evilflag == 0:
				if DBMS == "sqlite3":
					statement = f"SELECT * FROM TOOLS WHERE TOOL LIKE '%{search}%' LIMIT 5;"
				else:
					statement = f"SELECT TOP 5 * FROM pwndepot..tools WHERE name LIKE '%{search}%'"
				print(f"\nExecuting: {statement}\n")
				cursor.execute(statement)
				for i in cursor.fetchall():
					response += "<tr align='left'>\n\t<td id='tool'>" + str(i[1]) + "</td>\n\t<td id='price'>$" + str(i[3]) + "</td>\n\t<td id='quantity'>" + str(i[2]) + "</td>\n</tr>"
				response += "</table></body></html>"

			#Output the page
		
		return sqlPreamble + response

	pages = ['sql4','sqli4','store4']
	@cherrypy.expose(pages)
	def pwndepot4(self, search=None, **params):
		#DEMO - SQL Injection 4
		#Filters on SQL verbs and spaces
		#Level4 - Using a UNION attack, bypass SQLi filters to read the contents of another table.
		goal = " Goal: bypass filters and find the administrator password."
		sqlPreamble = getPreamble("sqli",4,"pwndepot4",goal)

		conn = initialize_db('tools.db')
		cursor = conn.cursor()

		#Search function
		evilflag = 0
		evilwords = ["select","from","where","union"]
		response = ""
		if search != None:
			for evilword in evilwords:
				if evilword in search.lower():
					for word in evilwords:
						search.replace(word,"")
					evilflag = 1
					response = "Mischief detected! Illegal words have been removed."
				if " " in search.lower():
					evilflag = 1
					response = "Mischief detected! Illegal character."

			if evilflag == 0:
				print("Search is populated...")

				if DBMS == "sqlite3":
					statement = f"SELECT * FROM TOOLS WHERE TOOL LIKE '%{search}%' LIMIT 5;"
				else:
					statement = f"SELECT TOP 5 * FROM pwndepot..tools WHERE name LIKE '%{search}%'"
				print(f"\nExecuting: {statement}\n")
				cursor.execute(statement)
				for i in cursor.fetchall():
					response += "<tr align='left'>\n\t<td id='tool'>" + str(i[1]) + "</td>\n\t<td id='price'>$" + str(i[3]) + "</td>\n\t<td id='quantity'>" + str(i[2]) + "</td>\n</tr>"
				response += "</table></body></html>"

			#Output the page
		return sqlPreamble + response
#}

#Command Injection {
	pages = ['cmdi','serverstatus','commandinjection','osinjection']
	@cherrypy.expose(pages)
	def serverstatus(self,server=None, **params):
		#http://127.0.0.1:31337/serverstatus?server=127.0.0.1%26%26whoami
		prompt = "Which server would you like to check?"
		cmdiPreamble = getPreamble("cmdi",1,prompt)
		response = "No servers selected.<br>"
		if server:
			if isWindows:
				execstring = ["ping","-n","2",server]
			else:
				execstring = [f"ping -c 2 {server}"]
			p = subprocess.Popen(execstring,shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
			stdout, stderr = p.communicate()
			retcode = p.returncode
			response = f"You provided {server}<br>"
			result = stdout.decode().replace("\n","</br>")
			response += result
			if "Ping request could not find" in result:
				response += f"The server at {server} is DOWN."
		return cmdiPreamble + response

	pages = ['cmdi2','serverstatus2','commandinjection2','osinjection2']
	@cherrypy.expose(pages)
	def serverstatus2(self,server=None, **params):
		#http://127.0.0.1:31337/serverstatus2?server=127.0.0.1|whoami
		prompt = "Which server would you like to check? Now with increased security!"
		cmdiPreamble = getPreamble("cmdi",1,prompt)
		
		evilflag = 0
		response = "No servers selected.<br>"
		if server:
			if "&" in server or ";" in server:
				evilflag = 1
				response += "<h2>No hacking allowed!</h2>"
			else:
				if isWindows:
					flag = "n"
				else:
					flag = "c"
				p = subprocess.Popen(["ping",f"-{flag}","2",server],shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
				stdout, stderr = p.communicate()
				retcode = p.returncode
				response = f"You provided {server}<br>"
				if retcode == 0:
					result = stdout.decode().replace("\n","</br>")
					response += result
				else:
					response = f"The server at {server} is DOWN."
		return cmdiPreamble + response
#}

	@cherrypy.expose('shutdown')
	def shutdown(self):  
	    cherrypy.engine.exit()

cherrypy.tree.mount(PwnDepot(),'/', config=configval)

cherrypy.engine.start()
cherrypy.engine.block()