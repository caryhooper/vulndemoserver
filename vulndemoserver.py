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
#Todo: consolidate like functionality into functions or classes.  

#Change these configs:
log_file_path = ''
if os.name == 'nt':
	webroot = 'wwwroot\\'
else:
	webroot = 'wwwroot/'
PATH = os.path.abspath(webroot)
port = 31337
#To bind on all ports, change this to: socket_host = "0.0.0.0" #AKA the "I like to live dangerously" option
socket_host = "127.0.0.1"

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

sqlPreamble = """<!DOCTYPE html>
	<html>
	<head><title>SQLi Demo</title></head>
	<body bgcolor="#e0dcdc">
	    <br><br>
	    <h1>Welcome to PWN Depot</h1>
	    <h4>Where you can buy just about anything...</h4>
	    <div align="left"><br><a href="/index.html">Go back to index.html</a><br></div>
	    <img src="../pwndepot.png" height="10%" width="10%">
	    <br><br><!-- """

cstiPreamble = """<!DOCTYPE html>
	<html>
	<head>
	    <title>CSTI Demo</title>
	</head>
	<body ng-app="app" ng-controller="demo" bgcolor="#e0dcdc">
	    <h1>{{message}}</h1>
	    <text>AngularJS Demo</text><br>
	    <text>Goal: Invoke XSS within this app.</text>
	    <br><br><text>Site works best in Chrome</text>
	    <script src="angular.1.6.9.min.js"></script>
	    <script>
	        var app = angular.module('app',[]);
	        app.controller('demo', function demo($scope){
	            $scope.message="Welcome to My First AngularJS Site";
	        });
	    </script><br><br>
	    """

class PwnDepot(object):
#DEMO - SSRF 1
#Goal: abuse the PDF generation functionality to read secrets located at http://127.0.0.1:31337/secret 
#Note: this module requires wkhtmltopdf.  This may be downloaded here:
#https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_msvc2015-win64.exe
#Once installed, the bin/ directory must be within the path.  (alternatively, apt-get install wkhtmltopdf)	
	pages = ['SSRF','pdfgen']
	@cherrypy.expose(pages)
	def ssrf(self,html=None,filename=None,**params):

		if html == None:
			#Input HTML (POST)
			response = """<html>
							<head>
								<title>SSRF Demo</title>
							</head>
							<body>
								<h1>Generate a PDF!</h1>
								<h3>Using wkhtmltopdf</h3>
								<img src="../pwndepot.png" height="10%" width="10%"><br>
								<form action="/pdfgen" id="pdfform" method="post">
									File Name: <input type="text" name="filename">
									<input type="submit">
								</form>
								<textarea rows="4" cols="50" name="html" form="pdfform">Enter HTML here.</textarea>
							</body>
						  </html>"""
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
			pdfkit.from_string(html,"wwwroot/pdf/" + pdfname)
			response = "<html><body>Please view your PDF at this <a href=\"pdf/"+pdfname+"\">link.</a></body></html>"
		return response

#DEMO - SSRF 2 / LFI
#Goal: abuse the PDF generation functionality to read secret file located at C:\Temp\admin.log
#Note: this module requires weasyprint.  Installation instructions here:
#https://weasyprint.readthedocs.io/en/stable/install.html
#Installation is a bit involved, but I promise it's worth it.
	pages = ['SSRF2','pdfgen2']
	@cherrypy.expose(pages)
	def ssrf(self,html=None,filename=None,**params):

		if html == None:
			#Input HTML (POST)
			response = """<html>
							<head>
								<title>SSRF Demo #2</title>
							</head>
							<body>
								<h1>Generate a PDF again!</h1>
								<h3>Using weasyprint</h3>
								<img src="../pwndepot.png" height="10%" width="10%"><br>
								<form action="/pdfgen2" id="pdfform" method="post">
									File Name: <input type="text" name="filename">
									<input type="submit">
								</form>
								<textarea rows="4" cols="50" name="html" form="pdfform">Enter HTML here.</textarea>
							</body>
						  </html>"""
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
			html.write_pdf("wwwroot/pdf/" + pdfname)
			response = "<html><body>Please view your PDF at this <a href=\"pdf/"+pdfname+"\">link.</a></body></html>"
		return response


#DEMO - SSRF 3 / RCE
#Goal: abuse the PDF generation functionality to execute JavaScript on the server
#Note: this module requires Chrome.  Point to a local chrome install
#Watch out... this modules requires full paths to 
	pages = ['SSRF3','pdfgen3']
	@cherrypy.expose(pages)
	def ssrf(self,html=None,filename=None,**params):
		if html == None:
			#Input HTML (POST)
			response = """<html>
							<head>
								<title>SSRF Demo #3</title>
							</head>
							<body>
								<h1>Generate a PDF for Pwnage!</h1>
								<h3>Using Headless Chrome</h3>
								<img src="../pwndepot.png" height="10%" width="10%"><br>
								<form action="/pdfgen3" id="pdfform" method="post">
									File Name: <input type="text" name="filename">
									<input type="submit">
								</form>
								<textarea rows="4" cols="50" name="html" form="pdfform">Enter HTML here.</textarea>
							</body>
						  </html>"""
		else:
			#Output link to PDF.
			if (os.path.isdir("wwwroot/pdf")):
				pass
			else:
				os.mkdir('wwwroot/pdf')
			if filename != None:
				if ".pdf" in filename:
					pdfname = filename
				else:
					pdfname  = filename + ".pdf"
			else:
				pdfname = "test.pdf"
			
			CHROME_PATH = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe" 
			tempname = filename.split('.')[0] + '.html'
			pdfpath = "C:\\Users\\Cary\\Documents\\Projects\\vulndemoserver\\wwwroot\\pdf\\"
			file = open(pdfpath + tempname,'w')
			print(f"DEBUG - Writing {html} to file {pdfpath + tempname}")
			file.write(html)
			file.close()
			#"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --headless --disable-gpu --print-to-pdf="C:\Temp\a.pdf" --no-margins file:///C:/Users/Cary/Documents/Programming/Python/vulndemoserver/wwwroot/pdf/foobar.html
			execarray = [CHROME_PATH, "--headless", "--disable-gpu", f"--print-to-pdf={pdfpath + pdfname}", "--no-margins", f"file:///{pdfpath}{tempname}"]
			p = subprocess.Popen(execarray,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
			#DEBUG Purposes Only
			stdout, stderr = p.communicate()
			retcode = p.returncode
			if retcode != 0:
				foo = f"DEBUG - stderr {stderr}"
				bar = f"DEBUG - stdout {stdout}"
				return foo + "<br><br>" + bar
			print(f"DEBUG - returncode {retcode}")
			time.sleep(2)
			response = "<html><body>Please view your PDF at this <a href=\"pdf/"+pdfname+"\">link.</a></body></html>"
		return response


#Secret
	pages = ['secret']
	@cherrypy.expose(pages)
	def secret(self,**params):
		#<iframe src="http://127.0.0.1:31337/secret"><iframe>
		response = "{'Message':'Top Secret - Unauthorized Access is Not Allowed','key':'5ebe2294ecd0e0f08eab7690d2a6ee69'}"
		return response


#DEMO - Client Side Template Injection
#Goal: Invoke JavaScript through an AngularJS Template within a GET parameter
	#Create aliases for the same path
	pages = ['CSTI','AngularJS']
	@cherrypy.expose(pages)
	def csti(self,h00p=None,**params):
		#TODO Check if file exists, then download AngularJS module.
		response = "Unexpected Error<br>"
		if h00p == None:
			response = "<br>Error: h00p is not defined<br>"
		else:
			#This for loop emulates PHP's htmlspecialchars()
			badchardict = {'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;','\'':'&#039'}
			for badchar in ['&','<','>','"','\'']:
				if badchar in h00p:
					h00p = h00p.replace(badchar,badchardict[badchar])
			response = "Hello " + h00p + "<br>"
		return cstiPreamble + response

#DEMO - Simple XSS
#Goal: Invoke JavaScript through XSS within a GET parameter
	#Create aliases for the same path
	pages = ['XSS','CSS','css']
	@cherrypy.expose(pages)
	def xss(self,h00p=None,**params):
		evilflag = 0
		response = "Unexpected Error<br>"
		if h00p == None:
			response = "<br>Error: h00p is not defined<br>"
		else:
			for badchar in []:
				if badchar in h00p:
					response = "Character not allowed.<br>"
					evilflag = 1
			if evilflag != 1:
				response = "Hello " + h00p + "<br>"
		return cstiPreamble + response

#DEMO - Simple XSS 2
#Goal: Invoke JavaScript through XSS within a GET parameter
	#Create aliases for the same path
	pages = ['XSS2','CSS2','css2']
	@cherrypy.expose(pages)
	def xss2(self,h00p=None,**params):
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
				response = "Hello " + h00p + "<br>"
		return cstiPreamble + response

#DEMO - Simple XSS 3
#Goal: Invoke JavaScript through XSS within a GET parameter
	#Create aliases for the same path
	pages = ['XSS3','CSS3','css3']
	@cherrypy.expose(pages)
	def xss3(self,h00p=None,**params):
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
				response = "Hello " + h00p + "<br>"
		return cstiPreamble + response

#DEMO - SQL Injection
#Level1 - Dump the contents of the tools database.
	#Aliases for same path
	pages = ['sql','sqli','store']
	@cherrypy.expose(pages)
	def pwndepot(self, search=None, **params):
		tools = ["adze","allen wrench","wrench","anvil","axe","bellows","bevel","block","tackle","block","plane","bolt","bolt","cutter","brad","brush","calipers","carpenter","chalk","line","chisel","circular","saw","clamp","clippers","coping","countersink","crowbar","cutters","drill","drill","bit","drill","press","edger","electric","drill","fastener","glass","cutter","glue","glue","gun","grinder","hacksaw","hammer","handsaw","hex","wrench","hoe","hone","jig","jigsaw","knife","ladder","lathe","level","lever","machete","mallet","measuring","tape","miter","box","monkey","wrench","nail","nail","set","needle-nose","pliers","nut","Phillips","screwdriver","pickaxe","pin","pincer","pinch","pitchfork","plane","pliers","plow","plumb","bob","poker","pruning","shears","pry","bar","pulley","putty","knife","rasp","ratchet","razor","reamer","rivet","roller","rope","router","ruler","safety","glasses","sand","paper","sander","saw","sawhorse","scalpel","scissors","scraper","screw","screwdriver","scythe","sharpener","shovel","sickle","snips","spade","spear","sponge","square","squeegee","staple","stapler","tack","tiller","tongs","toolbox","toolmaker","torch","trowel","utility","knife","vise","wedge","wheel","woodworker","workbench","wrench","DIY DIRTY BOMB KIT"]
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
				PRICE TEXT NOT NULL,
				QUANTITY TEXT NOT NULL);''')
			primarykey = 0
			print("\n\n\nFilling table: TOOLS\n\n\n")
			for tool in tools:
				price = random.randint(1,301)
				qty = random.randint(0,1001)
				if tool == "DIY DIRTY BOMB KIT":
					print("Adding flag! " + str(primarykey))
					price = "YouFoundTheFlag."
					qty = "Congrats!"
				statement = "INSERT INTO TOOLS (ID,TOOL,PRICE,QUANTITY) VALUES (" + str(primarykey) + ",'" + tool + "','" + str(price) + "','" + str(qty) + "')"
				cursor.execute(statement)
				print("Added tool with primarykey " + str(primarykey))
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

		sqlPreamble1 = """-->
		    <form action="/pwndepot" method="get">
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

		#Search function
		if search != None:
			print("Search is populated...")
			response = ""
			statement = "SELECT * FROM TOOLS WHERE TOOL LIKE '%" + search + "%' LIMIT 5;"
			cursor.execute(statement)
			#print("Entries retrieved... " + str(len(cursor.fetchall())))
			for i in cursor.fetchall():
				response += "<tr align='left'>\n\t<td id='tool'>" + str(i[1]) + "</td>\n\t<td id='price'>$" + str(i[3]) + "</td>\n\t<td id='quantity'>" + str(i[2]) + "</td>\n</tr>"
			response += "</table></body></html>"
			#print(response)
		else:
			response = ""

			#Output the page
		goal = " Goal: dump the contents of the tools table to find the secret tools."
		return sqlPreamble + goal + sqlPreamble2 + response

#DEMO - SQL Injection 2
#Level2 - Using a UNION attack, read the contents of another table.
	#Aliases for same path
	pages = ['sql2','sqli2','store2']
	@cherrypy.expose(pages)
	def pwndepot2(self, search=None, **params):
		tools = ["adze","Allen","wrench","anvil","axe","bellows","bevel","block","and","tackle","block","plane","bolt","bolt","cutter","brad","brush","calipers","carpenter","chalk","line","chisel","circular","saw","clamp","clippers","coping","countersink","crowbar","cutters","drill","drill","bit","drill","press","edger","electric","drill","fastener","glass","cutter","glue","glue","gun","grinder","hacksaw","hammer","handsaw","hex","wrench","hoe","hone","jig","jigsaw","knife","ladder","lathe","level","lever","machete","mallet","measuring","tape","miter","box","monkey","wrench","nail","nail","set","needle-nose","pliers","nut","Phillips","screwdriver","pickaxe","pin","pincer","pinch","pitchfork","plane","pliers","plow","plumb","bob","poker","pruning","shears","pry","bar","pulley","putty","knife","rasp","ratchet","razor","reamer","rivet","roller","rope","router","ruler","safety","glasses","sand","paper","sander","saw","sawhorse","scalpel","scissors","scraper","screw","screwdriver","scythe","sharpener","shovel","sickle","snips","spade","spear","sponge","square","squeegee","staple","stapler","tack","tiller","tongs","toolbox","toolmaker","torch","trowel","utility","knife","vise","wedge","wheel","woodworker","workbench","wrench"]
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

		sqlPreamble2 = """-->
		    <form action="/pwndepot2" method="get">
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

		#Search function
		if search != None:
			print("Search is populated...")
			response = ""
			statement = "SELECT * FROM TOOLS WHERE TOOL LIKE '%" + search + "%' LIMIT 5;"
			cursor.execute(statement)
			#print("Entries retrieved... " + str(len(cursor.fetchall())))
			for i in cursor.fetchall():
				response += "<tr align='left'>\n\t<td id='tool'>" + str(i[1]) + "</td>\n\t<td id='price'>$" + str(i[3]) + "</td>\n\t<td id='quantity'>" + str(i[2]) + "</td>\n</tr>"
			response += "</table></body></html>"
			#print(response)
		else:
			response = ""

			#Output the page
		goal = " Goal: find the administrator password."
		return sqlPreamble + goal + sqlPreamble2 + response


#DEMO - SQL Injection 3
#Level3 - Using a UNION attack, bypass SQLi filters to read the contents of another table.
	pages = ['sql3','sqli3','store3']
	@cherrypy.expose(pages)
	def pwndepot3(self, search=None, **params):
		tools = ["adze","Allen","wrench","anvil","axe","bellows","bevel","block","and","tackle","block","plane","bolt","bolt","cutter","brad","brush","calipers","carpenter","chalk","line","chisel","circular","saw","clamp","clippers","coping","countersink","crowbar","cutters","drill","drill","bit","drill","press","edger","electric","drill","fastener","glass","cutter","glue","glue","gun","grinder","hacksaw","hammer","handsaw","hex","wrench","hoe","hone","jig","jigsaw","knife","ladder","lathe","level","lever","machete","mallet","measuring","tape","miter","box","monkey","wrench","nail","nail","set","needle-nose","pliers","nut","Phillips","screwdriver","pickaxe","pin","pincer","pinch","pitchfork","plane","pliers","plow","plumb","bob","poker","pruning","shears","pry","bar","pulley","putty","knife","rasp","ratchet","razor","reamer","rivet","roller","rope","router","ruler","safety","glasses","sand","paper","sander","saw","sawhorse","scalpel","scissors","scraper","screw","screwdriver","scythe","sharpener","shovel","sickle","snips","spade","spear","sponge","square","squeegee","staple","stapler","tack","tiller","tongs","toolbox","toolmaker","torch","trowel","utility","knife","vise","wedge","wheel","woodworker","workbench","wrench"]
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

		sqlPreamble3 = """-->
		    <form action="/pwndepot3" method="get">
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
			    </tr>"""

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
				print("Search is populated...")

				statement = "SELECT * FROM TOOLS WHERE TOOL LIKE '%" + search + "%' LIMIT 5;"
				cursor.execute(statement)
				for i in cursor.fetchall():
					response += "<tr align='left'>\n\t<td id='tool'>" + str(i[1]) + "</td>\n\t<td id='price'>$" + str(i[3]) + "</td>\n\t<td id='quantity'>" + str(i[2]) + "</td>\n</tr>"
				response += "</table></body></html>"

			#Output the page
		goal = " Goal: bypass filters and find the administrator password."
		return sqlPreamble + goal + sqlPreamble3 + response

#DEMO - SQL Injection 4
#Level4 - Using a UNION attack, bypass SQLi filters to read the contents of another table.
	pages = ['sql4','sqli4','store4']
	@cherrypy.expose(pages)
	def pwndepot4(self, search=None, **params):
		tools = ["adze","Allen","wrench","anvil","axe","bellows","bevel","block","and","tackle","block","plane","bolt","bolt","cutter","brad","brush","calipers","carpenter","chalk","line","chisel","circular","saw","clamp","clippers","coping","countersink","crowbar","cutters","drill","drill","bit","drill","press","edger","electric","drill","fastener","glass","cutter","glue","glue","gun","grinder","hacksaw","hammer","handsaw","hex","wrench","hoe","hone","jig","jigsaw","knife","ladder","lathe","level","lever","machete","mallet","measuring","tape","miter","box","monkey","wrench","nail","nail","set","needle-nose","pliers","nut","Phillips","screwdriver","pickaxe","pin","pincer","pinch","pitchfork","plane","pliers","plow","plumb","bob","poker","pruning","shears","pry","bar","pulley","putty","knife","rasp","ratchet","razor","reamer","rivet","roller","rope","router","ruler","safety","glasses","sand","paper","sander","saw","sawhorse","scalpel","scissors","scraper","screw","screwdriver","scythe","sharpener","shovel","sickle","snips","spade","spear","sponge","square","squeegee","staple","stapler","tack","tiller","tongs","toolbox","toolmaker","torch","trowel","utility","knife","vise","wedge","wheel","woodworker","workbench","wrench"]
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

		sqlPreamble4 = """-->
		<form action="/pwndepot4" method="get">
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

		#Search function
		evilflag = 0
		evilwords = ["select","from","where","union"]
		response = ""
		if search != None:
			for evilword in evilwords:
				if evilword in search.lower():
					evilflag = 1
					response = "Mischief detected! Illegal word."
				if " " in search.lower():
					evilflag = 1
					response = "Mischief detected! Illegal character."

			if evilflag == 0:
				print("Search is populated...")

				statement = "SELECT * FROM TOOLS WHERE TOOL LIKE '%" + search + "%' LIMIT 5;"
				cursor.execute(statement)
				for i in cursor.fetchall():
					response += "<tr align='left'>\n\t<td id='tool'>" + str(i[1]) + "</td>\n\t<td id='price'>$" + str(i[3]) + "</td>\n\t<td id='quantity'>" + str(i[2]) + "</td>\n</tr>"
				response += "</table></body></html>"

			#Output the page
		goal = " Goal: bypass filters and find the administrator password."
		return sqlPreamble + goal + sqlPreamble4 + response

	@cherrypy.expose('shutdown')
	def shutdown(self):  
	    cherrypy.engine.exit()

cherrypy.tree.mount(PwnDepot(),'/', config=configval)

cherrypy.engine.start()
cherrypy.engine.block()