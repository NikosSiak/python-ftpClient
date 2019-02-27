from ftplib import FTP
import sys
import readline
import os
from tqdm import tqdm

#BLUE='\033[1;34m'
#RED='\033[0;31m'
#DEFAULT='\033[0m'

ftp = FTP('')
ip = '192.168.1.50' #change it with yours
port = 2000 	    #change it with yours

if len(sys.argv) == 3:
	try:
		ftp.connect(ip,port)
		ftp.login(sys.argv[1],sys.argv[2])
		ftp.encoding = 'utf-8'
	except:
		print ("\033[0;31m" + "Error Connecting to server \033[0m")
		exit()
else:
	try:
		ftp.connect(ip,port)
		ftp.login()
		ftp.encoding = 'utf-8'
	except:
		print ("\033[0;31m" + "Error Connecting to server \033[0m")
		exit()

def isFolder(foldername):
	try:
		ftp.cwd(foldername)
		ftp.cwd('..')
		return True
	except:
		return False

def getSizeServer(path):
	size = 0
	ftp.cwd(path)
	for file in ftp.nlst():
		if isFolder(file):
			size+=getSizeServer(file)
		else:
			ftp.voidcmd('TYPE i')
			size+=ftp.size(file)
	ftp.cwd('..')
	return size

def getSizeClient(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def uploadFile(filename,pbar):
	filename2 = filename
	counter = 0
	while filename in ftp.nlst():
		if counter!=0:
			for i in range(len(filename)-1,-1,-1):
				if filename[i]=='(':
					opens = i
					break
				elif filename[i]==')':
					closes = i
			ext = filename[closes+1:]
			name = filename[:opens]
			filename = name + ext
		counter+=1
		for i in range(len(filename)-1,-1,-1):
			if filename[i] == '.':
				ind = i
				break
		ext = filename[ind:]
		filename = filename[:ind]
		filename = filename + '(' + str(counter) + ')' + ext
	file = open(filename2, 'rb')
	filesize = os.path.getsize(filename2)
	ftp.storbinary('STOR '+filename, file, port,callback = lambda sent: pbar.update(len(sent)))
	file.close()

def downloadFile(filename,pbar):
	filename2 = filename
	counter = 0
	while os.path.exists(filename):
		if counter!=0:
			for i in range(len(filename)-1,-1,-1):
				if filename[i]=='(':
					opens = i
					break
				elif filename[i]==')':
					closes = i
			ext = filename[closes+1:]
			name = filename[:opens]
			filename = name + ext
		counter+=1
		ind = 0
		for i in range(len(filename)-1,-1,-1):
			if filename[i] == '.':
				ind = i
				break
		ext = filename[ind:]
		filename = filename[:ind]
		filename = filename + '(' + str(counter) + ')' + ext
	with open(filename, 'wb') as fd:
		def cb(data):
			pbar.update(len(data))
			fd.write(data)
		ftp.retrbinary('RETR {}'.format(filename2), cb)

def downloadFolder(foldername,pbar):
	counter = 0
	foldername2 = foldername
	while os.path.exists(foldername):
		if counter!=0:
			for i in range(len(foldername)-1,-1,-1):
				if foldername[i]=='(':
					ind = i
					break
			foldername = foldername[:ind]
		counter+=1
		foldername = foldername + '(' + str(counter) + ')'
	os.mkdir(foldername)
	os.chdir(foldername)
	ftp.cwd(foldername2)
	for file in ftp.nlst():
		if isFolder(file):
			downloadFolder(file,pbar)
		else:
			try:
				downloadFile(file,pbar)
			except:
				print("\033[0;31m" + "error \033[0m")
	os.chdir('..')
	ftp.cwd('..')

def uploadFolder(foldername,pbar):
	counter = 0
	foldername2 = foldername
	while foldername in ftp.nlst():
		if counter!=0:
			for i in range(len(foldername)-1,-1,-1):
				if foldername[i]=='(':
					ind = i
					break
			foldername = foldername[:ind]
		counter+=1
		foldername = foldername + '(' + str(counter) + ')'
	ftp.mkd(foldername)
	ftp.cwd(foldername)
	os.chdir(foldername2)
	for file in os.listdir():
		if os.path.isdir(file):
			uploadFolder(file,pbar)
		else:
			try:
				uploadFile(file,pbar)
			except:
				print("\033[0;31m" + "error \033[0m")
	os.chdir('..')
	ftp.cwd('..')

def completer(text, state):
	options = [i for i in ftp.nlst() if i.startswith(text)]
	for i in ['ls','pwd','cd','download','upload','size','exit','help']:
		if i.startswith(text):
			options.append(i)
	for i in os.listdir():
		if i.startswith(text):
			options.append(i)
	if state < len(options):
	        return options[state]
	else:
	        return None


readline.parse_and_bind("tab: complete")
readline.set_completer(completer)

while True:
	temp = input(">>>")
	ind = temp.find(" ")
	param = ""
	if ind != -1:
		command = temp[:ind]
		param = temp[ind+1:]
	else:
		command = temp
	if command == "help":
		print ("List of commands:")
		print ("download filename")
		print ("upload filename")
		print ("cd directory")
		print ("ls")
		print ("pwd")
		print ("size filename/directory")
		print ("exit")
	elif command == "download":
		if isFolder(param):
			try:
				filesize = getSizeServer(param)
				with tqdm(unit = 'blocks', unit_scale = True, leave = True, miniters = 1, desc = 'Downloading......', total = filesize) as pbar:
					downloadFolder(param,pbar)
			except:
				print ("\033[0;31m" + "Wrong folder \033[0m")
		else:
			try:
				ftp.voidcmd('TYPE i')
				filesize = ftp.size(param)
				with tqdm(unit = 'blocks', unit_scale = True, leave = True, miniters = 1, desc = 'Downloading......', total = filesize) as pbar:
					downloadFile(param,pbar)
			except:
				print ("\033[0;31m" + "Wrong filename \033[0m")
	elif command == "upload":
		if os.path.isdir(param):
			try:
				filesize = getSizeClient(param)
				with tqdm(unit = 'blocks', unit_scale = True, leave = True, miniters = 1, desc = 'Uploading......', total = filesize) as pbar:
					uploadFolder(param,pbar)
			except:
				print ("\033[0;31m" + "Wrong folder \033[0m")	
		else:
			try:
				filesize = os.path.getsize(param)
				with tqdm(unit = 'blocks', unit_scale = True, leave = True, miniters = 1, desc = 'Uploading......', total = filesize) as pbar:
					uploadFile(param,pbar)
			except:
				print ("\033[0;31m" + "Wrong filename \033[0m")
	elif command == "cd":
		try:
			ftp.cwd(param)
		except:
			print ("\033[0;31m" + "Wrong directory \033[0m")
	elif command == "ls":
		for file in ftp.nlst():
			if isFolder(file):
				print('\033[1;34m' + file + '\033[0m')
			else:
				print(file)
	elif command == "pwd":
		print (ftp.pwd())
	elif command == "size":
		if isFolder(param):
			print("Size of " + param + ": " + str(getSizeServer(param)) + " bytes")
		else:
			ftp.voidcmd('TYPE i')
			print("Size of " + param + ": " + str(ftp.size(param)) + " bytes")
	elif command == "exit":
		ftp.quit()
		break
	else:
		print ("Invalid command")
