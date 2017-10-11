
# -*- coding: utf-8 -*-
#!/usr/bin/env python
#title:		image_crawler.py
#description:	Download the last public images from Flickr with associated information
#author:		Alessandro Ortis
#date:		20170928
#version:		0.1
#usage:		python image_crawler.py <seqday>
#notes:         if there are images in the DB, update daily information
#==============================================================================


import flickrapi
import json
import pickle
import urllib, urllib2
import sqlite3 as lite
import csv
import sys, os, os.path
reload(sys)
sys.setdefaultencoding('utf8')
import time
#from skimage.measure import structural_similarity as ssim
from skimage.measure import compare_ssim as ssim
import cv2
import numpy as np
#import matplotlib.pyplot as plt
from sys import argv
from shutil import copyfile
import sqlite3 as lite
import time, datetime, calendar
import ftfy

def create_db(db_name, tab_name, query, drop_existing = False):
    con = lite.connect(db_name)
    cur = con.cursor()
    if(drop_existing):
        q = "DROP TABLE IF EXISTS " + tab_name
        cur.execute(q)
    # Create empty table
    try:
        cur.execute(query)
        print "Creating a new DB/table\t" + tab_name + "\n" 
    except Exception, e:
        if not str(e) == 'table ' + tab_name + ' already exists':
            print "Error:\t" + str(e)
        else:
            print str(e) #If the table exists, just go ahead.
    con.close()
 
 
def find_by_size(size,path):
    result = []
    for root, dirs, files in os.walk(path):
        for f in files:
            path_name = os.path.join(root,f)
            if os.stat(path_name).st_size > size:
                result.append(f)
    return result

def downloadImage(url, file_name):
    
    u = urllib2.urlopen(url)
    f = open(file_name, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "\nDownloading: %s Bytes: %s" % (file_name, file_size)
    
    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break
    
        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print "\n"+status,
    
    f.close()
    
def createRecord(csvrow):
    record = {'ImageID':'', 'Num_of_Positive':0, 'Num_of_Neutral':0, 'Num_of_Negative':0}
    
    record['ImageID'] = csvrow[0]
    record['Num_of_Positive'] = int(csvrow[1])
    record['Num_of_Neutral'] = int(csvrow[2])
    record['Num_of_Negative'] = int(csvrow[3])

    return record    


def mse(A,B):
    err = np.sum((A.astype("float") - B.astype("float")) ** 2)
    err /= float((A.shape[0]) * (A.shape[1]))
    return err
    
def isMissing(imagePath):
    for referenceImage in nullImages:
        refImgPath = "data/" + referenceImage
        refImg = cv2.imread(refImgPath)
        curImg = cv2.imread(imagePath)
        
            
        refImg = cv2.cvtColor(refImg, cv2.COLOR_BGR2GRAY)
        curImg = cv2.cvtColor(curImg, cv2.COLOR_BGR2GRAY)
        
        curImg = cv2.resize(curImg,(refImg.shape[1], refImg.shape[0]))
        
        
        s = ssim(refImg,curImg)
        print "SSIM with null picture:\t"+str(s)
        if s>0.99:
            return True
    return False
    

def sanitize_text(s):
    s = unicode(s)
    s = s.replace("&#39;"," ")
    s = s.replace("'"," ")
    s = s.replace("’"," ")
    s = s.replace("\""," ")
    s = s.replace("\n"," ")
    s = ftfy.fix_text(s)
    return s
        
def daily_monitoring(photo_id, seqday):
    
    try:
     #   photo_id = "23557782078"
      #  photo_id = "37418539912"
    #            [u'23600802928', u'36782732473', u'36782743333'] these Flickr IDs don't exist
    #           [u'36783353383', u'23601757988', u'36783729883', u'36783687273']
        #   [u'23602491078', u'37406825706']
        #photo_id = '37406825706'
	check = False
        print "\nProcessing photo with FlickrId:\t" +photo_id
        print "Getting photo info..."
        response = flickr.photos.getInfo(api_key = api_key, photo_id=photo_id)            
        print "request result:\t"+response['stat']
        photo_info = response['photo']
        ext = 'jpg'
        photo_url = 'https://farm'+str(photo_info['farm'])+'.staticflickr.com/'+str(photo_info['server'])+'/'+photo_id+'_'+str(photo_info['secret'])+'_b.'+ext
        user_id = photo_info['owner']['nsid']
        dt = datetime.datetime.utcnow()
        date_download = calendar.timegm(dt.utctimetuple())
             
        # seqday == 0 only the first time and after three days (early period)
        if seqday == 0:
            date_posted = photo_info['dates']['posted']
            date_taken = photo_info['dates']['posted']
            photo_title = ''
            photo_title = photo_info['title']['_content']
  #          print "Original Title: " + photo_title
            photo_title = photo_title.replace("&#39;"," ")
            photo_title = photo_title.replace("'"," ")
            photo_title = photo_title.replace("’"," ")
            photo_title = photo_title.replace("\""," ")
            photo_title = photo_title.replace("\n"," ")
            photo_title = ftfy.fix_text(unicode(photo_title))
   #         print "Title: " + photo_title

            #TODO: use the function sanitize_text
            photo_description = ''
            photo_description = photo_info['description']['_content']
            photo_description = photo_description.replace("&#39;"," ")
            photo_description = photo_description.replace("'"," ")
            photo_description = photo_description.replace("’"," ")
            photo_description = photo_description.replace("\""," ")
            photo_description = photo_description.replace("\n"," ")
            photo_description = ftfy.fix_text(unicode(photo_description))
    #        print "Description: " + photo_description
            
            photo_tags_num = len(photo_info['tags']['tag'])
            photo_tags = [sanitize_text(str(t['_content'])) for t in photo_info['tags']['tag']]
    #        print "# of tags:\t" + str(photo_tags_num)
 #           print photo_tags
            
            lat = ""
            lon = ""
            country = ""
            if 'location' in photo_info:
                lat = photo_info['location']['latitude']
                lon = photo_info['location']['longitude']
                if 'country' in photo_info['location']:
                    country = photo_info['location']['country']['_content']


            print "Getting photo sizes..."
            response = flickr.photos.getSizes(api_key = api_key, photo_id=photo_id)            
            print "request result:\t"+response['stat']
            photo_size = 0
            for sz in response['sizes']['size']:
                if sz['label'] == 'Original':
                    photo_size = int(sz['width']) * int(sz['height'])
                    print "Original size:\t\t"+str(photo_size)+"\t("+ sz['height'] +" X " + sz['width'] +")"
                    break
      
          # Download the photo and check if still available
            img_path = "images/"+photo_id#+".jpg"   
            httpRes = urllib.urlretrieve(photo_url, img_path)
            # Questa funzione usa urllib2     
            #downloadImage(photo_url,img_path)    
            abs_path = os.path.abspath(img_path)
                        
            check = isMissing(img_path)
            print "Is missing:\t" + str(check)
            if check:
                copyfile(abs_path, "missing/"+photo_id)
                os.remove(abs_path)
                abs_path = os.path.abspath("missing/"+photo_id)            
            elif os.stat(abs_path).st_size < 10000:
		# Discard images with size lower than 10Mb
                copyfile(abs_path, "missing/"+photo_id)
                os.remove(abs_path)
                abs_path = os.path.abspath("missing/"+photo_id)            
		check = True
		print "Photo discarded due to image file size"
		if DEMO:
			time.sleep(5)

            print "Getting photo contexts..." 
            response = flickr.photos.getAllContexts(api_key = api_key, photo_id=photo_id)            
            print "request result:\t"+response['stat']
            photo_sets = 0
            photo_groups = 0
            avg_group_memb =0
            avg_group_photos = 0
            photo_groups_ids =[]
            groups_members =[]
            groups_photos = []
            if 'set' in response:
                photo_sets = len(response['set'])
            if 'pool' in response:
                photo_groups = len(response['pool'])
                photo_groups_ids = [g['id'] for g in response['pool']]
                groups_members = [int(g['members']) for g in response['pool']]
                groups_photos = [int(g['pool_count']) for g in response['pool']]
                avg_group_memb = 0 if len(groups_members)==0 else np.mean(groups_members)
                avg_group_photos = 0 if len(groups_photos)==0 else np.mean(groups_photos)
            #    if photo_groups > 0:
                #    print json.dumps(photo_groups_ids)
            print "The photo is shared through\t" +str(photo_sets)+"\talbums and\t"+str(photo_groups)+"\tgroups."
 
 
            con = lite.connect('user_info.db')
            cur = con.cursor()
            cur.execute("SELECT * FROM user_info WHERE UserId = '"+str(user_id)+"'")
            if len(cur.fetchall()) > 0 and seqday!=2:
                print "User\t"+str(user_id)+"\talready registered."
            else:
                con.close()
                print "Getting user info..."
                response = flickr.people.getInfo(api_key = api_key, user_id=user_id)            
                print "request result:\t"+response['stat']
                ispro = int(response['person']['ispro'])
                has_stats = int(response['person']['has_stats']) 
                username = response['person']['username']['_content']
                username = sanitize_text(username)
    #            if 'location' in response['person']:
     #               location = response['person']['location']['_content']        
    
                user_photos = int(response['person']['photos']['count']['_content'])        
    
                print "Getting user contacts..."
                response = flickr.contacts.getPublicList(api_key = api_key, user_id=user_id)            
                print "request result:\t"+response['stat']
                contacts = int(response['contacts']['total'])
     
     
                 
                # Notes: the API allows only 500 photos per call. If the user has 
                # a huge amount of pictures, consider only the views of the 10.000 oldest photos (i.e., 20 pages).
                print "Getting photos stats..."
                user_photo_views = []
                page_n = 1
                while len(user_photo_views)< user_photos:
                    if page_n == 10:
                        print "Waiting 1 sec..."
                        time.sleep(1)
                        
                    response = flickr.people.getPublicPhotos(api_key = api_key, user_id=user_id, extras='views', page=page_n, per_page=500)            
                    print "request result:\t"+response['stat']
                    page_elements = [int(p['views']) for p in response['photos']['photo']]
                    user_photo_views.extend(page_elements)
                    page_n += 1
                    #Integrity check and upper bound                
                    if len(page_elements)<500 or page_n >20:
                        break
		
                user_mean_views = 0 if len(user_photo_views)==0 else np.mean(user_photo_views)
                print "The user's photos have a mean view rate of\t"+str(user_mean_views)+"\tcomputed on\t"+str(len(user_photo_views))+"\tphotos."
                
                print "Getting user groups info..."
                response = flickr.people.getPublicGroups(api_key = api_key, user_id=user_id)            
                print "request result:\t"+response['stat']
                user_groups_membs = [int(g['members']) for g in response['groups']['group']]
                user_groups_photos = [int(g['pool_count']) for g in response['groups']['group']]
                user_groups = len(user_groups_photos)
                avg_user_gmemb = 0 if len(user_groups_membs)==0 else np.mean(user_groups_membs)
                avg_user_gphotos = 0 if len(user_groups_photos)==0 else np.mean(user_groups_photos)
                print "The user has\t"+str(contacts)+"\tcontacts and is enrolled in\t" +str(user_groups)+"\tgroups with\t"+str(avg_user_gmemb)+"\tmean members and\t"+str(avg_user_gphotos)+"\tmean photos."
    
    
    
                # DB interaction
         #       print username
                try:
                    con = lite.connect('user_info.db')
                    cur = con.cursor()
                    q = "INSERT INTO user_info(UserId, \
                                                        Day, \
                                                        Username, \
                                                        Ispro, \
                                                        HasStats, \
                                                        Contacts, \
                                                        PhotoCount, \
                                                        MeanViews, \
                                                        GroupsCount, \
                                                        GroupsAvgMembers, \
                                                        GroupsAvgPictures) VALUES('"+\
                                user_id+"', "+str(seqday)+", '"+username + \
                                "', "+str(ispro)+", "+str(has_stats) +  \
                                ", "+str(contacts)+", "+str(user_photos) + \
                                ", "+str(user_mean_views)+", "+str(user_groups) + \
                                ", "+str(avg_user_gmemb)+", "+str(avg_user_gphotos) + \
                                ")"
                                #  ", "+str(json.dumps(photo_groups_ids))+")")

                    if not DEMO:
	            	cur.execute(q)
		        con.commit()
                    else:
		    	print "DEMO MODE: not writing the DB."
                    con.close()
                except Exception, e:
                     print "ERROR with Photo\t"+photo_id+":"
                     print str(e)
                     print "Query:"
                     print q
                     return False
                print "User record added." 
     
            #----------- user info ----
            con.close()  # closes the connection with user_info.db
            
            con = lite.connect('headers.db')
            cur = con.cursor()
            if not DEMO:

	    	cur.execute("INSERT INTO headers(FlickrId, \
        	                                        Day, \
                	                                URL, \
                        	                        Path, \
                                	                DatePosted, \
                                        	        DateTaken, \
                                                	DateCrawl, \
                                                	UserId) VALUES('"+\
   	                     photo_id+"',"+str(seqday)+", '"+photo_url+"', '"+abs_path + \
        	                "', '"+str(date_posted)+"', '"+str(date_taken) +  \
                	        "', '"+str(date_download)+"', '"+str(user_id)+"')")
                      	#  ", "+str(json.dumps(photo_groups_ids))+")")
            	con.commit()
            else:
            	print "DEMO MODE: not writing the DB."
            con.close()
            print "Header record added."
            
            # Single quote escape
            tags = json.dumps(photo_tags).replace("'","''")
           # print tags
            con = lite.connect('image_info.db')
            cur = con.cursor()
            q = "INSERT INTO image_info(FlickrId, \
                                                Day, \
                                                Size, \
                                                Title, \
                                                Description, \
                                                NumSets, \
                                                NumGroups, \
                                                AvgGroupsMemb, \
                                                AvgGroupPhotos, \
                                                Tags, \
                                                Latitude, \
                                                Longitude, \
                                                Country) VALUES('"+\
                        photo_id+"', "+str(seqday)+", "+str(photo_size)+", '"+photo_title + \
                        "', '"+photo_description+"', "+str(photo_sets) +  \
                        ", "+str(photo_groups)+", "+str(avg_group_memb)+ \
                        ", "+str(avg_group_photos) +", '"+ tags +"', '"+lat +"', '"+lon + \
                        "', '"+country+"')"
            if not DEMO:
	    	cur.execute(q)
            	con.commit()
            else:
            	print "DEMO MODE, not writing the DB."
            con.close()
            print "Image info record added."
       
        #Getting daily information
	if check:
            return False	#The image data have been recorded in DBs but the image is not available

        photo_views = int(photo_info['views'])
        photo_comments = int(photo_info['comments']['_content'])        

        print "Getting photo favorites..."
        response = flickr.photos.getFavorites(api_key = api_key, photo_id=photo_id)            
        print "request result:\t"+response['stat']
        photo_favorites = int(response['photo']['total'])
     
        print photo_url,'\n','views:\t',photo_views,'\tcomments:\t',photo_comments
        con = lite.connect('image_daily.db')
        cur = con.cursor()
        if not DEMO:
	        cur.execute("INSERT INTO image_daily(FlickrId, \
        	                                    Day, \
                	                            Comments, \
                        	                    Views, \
                                	            Favorites, \
                                        	    DateQuery) VALUES('"+\
           	         photo_id+"',"+str(seqday)+", "+str(photo_comments) + \
               	     ", "+str(photo_views)+", "+str(photo_favorites)+", '"+str(date_download)+"')")
        	con.commit()
        else:
        	print "DEMO MODE, not writing the DB."
        con.close()
        print "Image daily record added."
        print "Image:\t"+photo_id+"\tday:\t"+str(seqday)+"\n"

        return True	# The only one "True" return value
        
    except Exception, e:
        print "ERROR with Photo\t"+photo_id+":"
        print str(e)
        return False
       # print q
#        sys.exit(0)
    

def do_work():

	## Load list of known images, or create a new one
	##

	# Keeps the list of known images
	known_images = []

	if not os.path.isfile(pickle_image_list):
	    print('Creating (empty) image list file (pickle)')
	    data = []
	    with open(pickle_image_list,'wb') as f:
		pickle.dump(data,f)
	else:
	    print('Loading image list from pickle')
	    with open(pickle_image_list,'r') as f:
		known_images = pickle.load(f)

	##-----------------------------------------------------------------
	    
	##
	## Create DBs
	##
	headers_db      = 'headers.db'      #mage id, user id, groups ids
	image_info_db   = 'image_info.db'   #image meta-data
	image_daily_db  = 'image_daily.db'  #daily information
	user_info_db    = 'user_info.db'    #user information
	groups_info_db  = 'groups_info.db'  #groups information

	t_name = 'headers'
	query = "CREATE TABLE headers(Id INTEGER PRIMARY KEY, \
								FlickrId TEXT, \
					Day INT, \
								UserId TEXT, \
					URL TEXT, \
					Path TEXT, \
								DatePosted TEXT, \
								DateTaken, \
								DateCrawl TEXT)"

	create_db(headers_db, t_name, query, drop_existing = True)


	# Information that shouldn't change. If they do, a new record is added.
	t_name = 'image_info'
	query = "CREATE TABLE image_info(Id INTEGER PRIMARY KEY, \
								FlickrId TEXT, \
								Day INT, \
					Camera TEXT, \
					Size INT, \
								Title TEXT, \
								Description TEXT, \
					NumSets INT, \
					NumGroups INT, \
					AvgGroupsMemb REAL, \
					AvgGroupPhotos REAL, \
								Tags TEXT, \
								Latitude TEXT, \
								Longitude TEXT, \
					Country TEXT)"

	create_db(image_info_db, t_name, query, drop_existing = True)

	# Information collected daily
	t_name = 'image_daily'
	query = "CREATE TABLE image_daily(Id INTEGER PRIMARY KEY, \
								FlickrId TEXT, \
								Day INT, \
								Comments INT, \
					Views INT, \
					Favorites INT, \
					DateQuery TEXT)"

	create_db(image_daily_db, t_name, query, drop_existing = True)


	t_name = 'user_info'
	query = "CREATE TABLE user_info(Id INTEGER PRIMARY KEY, \
								UserId TEXT, \
								Day INT, \
								Username TEXT, \
					Ispro INT, \
					HasStats INT, \
					Contacts INT, \
					PhotoCount INT, \
					MeanViews REAL, \
					GroupsCount INT, \
					GroupsAvgMembers REAL, \
					GroupsAvgPictures REAL)"

#	create_db(user_info_db, t_name, query, drop_existing = False)


	t_name = 'groups_info'
	query = "CREATE TABLE "+t_name+"(Id INTEGER PRIMARY KEY, \
								GroupId TEXT, \
								Day INT, \
								Members INT, \
								Photos INT)"

	create_db(groups_info_db, t_name, query, drop_existing = True)
	##-----------------------------------------------------------------


	##
	## Image and meta-data crawling
	##

	tt = time.time()
	count = 0        
	sleep_time = 10
	print "Number of images to download:\t"+str(new_images_count)    

	#extra_info = 'date_taken, date_upload, geo, tags, description, title, views, owner_name'
	extra_info = '' 


	# Get the list of images to download
	#   photo_set ==>> all pictures crawled in this call
	#   known_images ==>> all pictures crawled at all
	#   new_photo_ids ==>> pictures added at each iteration
	photo_set = []
	not_available_photos = []
#	while len(photo_set) < new_images_count:
	while len(known_images) < new_images_count:

	    print "Photo Set:\t"+ str(len(photo_set))    
	    print "Known images:\t"+ str(len(known_images))
	    f = open('status.log','w')
	    f.write("\nPhoto Set:\t"+str(len(photo_set)))
	    f.write("\n\nKnown images:\t"+str(len(known_images))+"\n")
	    f.close()

	    attempts = 0
	    try :
		# Request the first 2 pages of the most recent public photos on Flickr
		print "\n\nGetting recent photos..."
		recent_photos_p1 = flickr.photos.getRecent(api_key= api_key, per_page = 500, page= 1, extras = extra_info)
		page_1 = [photo['id'] for photo in recent_photos_p1['photos']['photo']]
		print "First page request:\t"+recent_photos_p1['stat']
		recent_photos_p2 = flickr.photos.getRecent(api_key= api_key, per_page = 500, page= 2, extras = extra_info)
		page_2 = [photo['id'] for photo in recent_photos_p2['photos']['photo']]
		print "Second page request:\t"+recent_photos_p2['stat']

		#Some photos may shift to the second page between the two calls            
		new_photo_ids = set(page_1+page_2) - set(photo_set)
		new_photo_ids = list(new_photo_ids)
		photo_set = list(set(photo_set+page_1+page_2))
	     #   photo_data.extend(recent_photos_p1['photos']['photo'])
	      #  photo_data.extend(recent_photos_p2['photos']['photo'])
		
		print "Unique photos:\t" + str(len(photo_set)) + "/" + str(new_images_count)
		print "Adding\t" + str(len(new_photo_ids))+ "\tnew photos"
		

	#        for photo_id in photo_set:
	 #           if photo_id not in new_photo_ids:
	#                print "Skipping (existing)\t"+photo_id
	#                continue
		for photo_id in new_photo_ids:
		    print "Known images:\t"+ str(len(known_images))
		    res = daily_monitoring(photo_id, 0)            
		    #Remove the processed photo id from the list(???)
		    if not res:
			not_available_photos.append(photo_id)
		    else:
			known_images.append(photo_id)
				
			if len(known_images) % 1000 == 0:
				print "Saving data pickle backup..."
				with open(pickle_image_list,'wb') as f:
					pickle.dump(list(known_images),f)
		    if len(known_images)>new_images_count:
			break
			
		print "Sleeping (new attempt after "+str(4)+" seconds)..."
		time.sleep(4)
		
	    except Exception, e:
		print "ERROR:"
		print str(e)
		if attempts >= 5:
		    print "Too many failed attempts. Exit."
		    break
		attempts += 1
		print "Sleeping (new attempt after "+str(3)+" seconds)..."
		time.sleep(3)
		print "Awake .. "


	with open(pickle_image_list,'wb') as f:
	    pickle.dump(list(known_images),f)      # known_images: only pictures successfully crawled without errors
	print "\n\n-------------\tCrawling Report\t-------------"
	print "Elapsed time (sec):\t"+ str(time.time()-tt)
	print "Not available photos:"
	print "total:\t"+ str(len(not_available_photos))
	for id in not_available_photos:
	    print id

	print "List of Flickr Photos (photo_set):"
	print "total:\t"+ str(len(photo_set))    
	print "Known images:"
	print "total:\t"+ str(len(known_images))

	con = lite.connect('image_daily.db')
	cur = con.cursor()
	rows = cur.execute("SELECT FlickrId, Views FROM image_daily WHERE Day = 0")
	print "Total in DB:\t"+str(len(cur.fetchall()))
	for r in rows:
	    print r
	con.close()


def daily_analysis(seqday):
#	with open(pickle_image_list,'r') as f:
	# List of good photos, ordered by CrawlDate

#	with open('final_photo_list.pickle','r') as f:
	with open('day'+str(seqday-1)+'_images.pickle','r') as f:
	    images_list = pickle.load(f)


	print "Check for duplicates..."
	dup = len(images_list) - len(list(set(images_list)))
	print "duplicates:\t"+str(dup)

	err_list = []

	print "\n\nSTART\n************\tUTC\t"+str(datetime.datetime.utcnow())+"\t************"
	print "Updating engagement state of\t"+str(len(images_list))+"\t photos"
	print "Day:\t"+str(seqday)
#	print images_list[0]
#	sys.exit(0)
	for photo_id in images_list:
	   try:
	       res = daily_monitoring(photo_id, seqday) 
	       if res:
		    print "Image\t"+photo_id+"\tanalyzed for day\t"+str(seqday)
	       else:
		    print "Image\t"+photo_id+"\terror occurred during day\t"+str(seqday)
		    err_list.append(photo_id)
	   except Exception, e:
		print "ERROR (external loop):"
		print "FlickrId:\t"+str(photo_id)
		err_list.append(photo_id)
		print str(e)
		
	print "Error images list:"
	print err_list
	print "Images with errors:"
	print len(err_list)
	con = lite.connect('image_daily.db')
	cur = con.cursor()
	#Select the pictures successfully added today
	res = cur.execute("SELECT FlickrId FROM image_daily WHERE Day = "+str(seqday))
	rows = cur.fetchall()
	print "Total in DB:\t"+str(len(rows))

	new_list = [x[0] for x in rows]
	with open('day'+str(seqday)+'_images.pickle','wb') as f:
		pickle.dump(new_list,f)
	print "Images list updated"

	print "\n\nEND\n************\tUTC\t"+str(datetime.datetime.utcnow())+"\t************"



"""
    Settings:
	
	-   Flickr API Settings
	-   Number of images to crawl

"""
# Null image name
nullImages= ["flickrMissing", "flickrNotFound"]

# Credenziali The Social Picture
api_key = u'c3388aa658417c77dcc98d5f9dc3ac91'
api_secret = u'9f3693a3ab57bfc1'

# Credenziali iplabsocial (alessandro.ortis)
api_key= u'394b14cc54cd9cba5aa0d68b1d5f7eb9'
api_secret = u'9bda221d1de625a9'

# Le seguenti due righe sono state eseguite una volta sola per generare il token di autorizzazione    
#flickr = flickrapi.FlickrAPI(api_key, api_secret)
#flickr.authenticate_via_browser(perms='read')
oauth_token=u'72157675663685032-6052b3ccbdc594e8'
oauth_verifier=u'1103dab7cc7d9c5e'
flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')
pickle_image_list = 'known_images.pickle'
new_images_count = 10200
""" END SETTINGS """	##

DEMO = False
if len(argv)==1:
	print "seqday missing!!!"
	sys.exit(0)
#	do_work()
else:

	day = int(argv[1])
	daily_analysis(day)

