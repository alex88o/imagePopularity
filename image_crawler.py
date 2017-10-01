
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
#sys.setdefaultencoding('utf8')
import time
from skimage.measure import structural_similarity as ssim
import cv2
import numpy as np
#import matplotlib.pyplot as plt
from sys import argv
from shutil import copyfile
import sqlite3 as lite
import time, datetime, calendar
import ftfy

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

new_images_count = 2000      # Set it to zero to update the existing pictures  
#TODO: scaricare 2000 foto al giorno per 7 giorni in 2 orari diversi, tot 20k
# Es ore 12 e 24... giornamlemnte si possono variare gli orari
""" END SETTINGS """

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
        print "SSIM:\t"+str(s)
        if s>0.99:
            return True
    return False
    
    """
    fig = plt.figure("Image comparison")
    plt.suptitle("MSE: "+str(m))

    ax = fig.add_subplot(1,2,1)
    plt.imshow(refImg, cmap= plt.cm.gray)
    plt.axis("off")

    ax = fig.add_subplot(1,2,2)
    plt.imshow(refImg, cmap= plt.cm.gray)
    plt.axis("off")

    plt.show()    
    """

def sanitize_text(s):
    s = unicode(s)
    s = s.replace("'"," ")
    s = s.replace("’"," ")
    s = s.replace("\""," ")
    s = s.replace("\n"," ")
    s = ftfy.fix_text(s)
    return s
        
def daily_monitoring(photo_id, seqday):
    
    try:
     #   photo_id = "23557782078"
     #   photo_id = "36717094514"
        print "\nProcessing photo with FlickrId:\t" +photo_id
        print "Getting photo info..."
        response = flickr.photos.getInfo(api_key = api_key, photo_id=photo_id)            
        print "request result:\t"+response['stat']
        photo_info = response['photo']
        ext = 'jpg'
        photo_url = 'https://farm'+str(photo_info['farm'])+'.staticflickr.com/'+str(photo_info['server'])+'/'+photo_id+'_'+str(photo_info['secret'])+'_b.'+ext
        user_id = photo_info['owner']['nsid']
             
        # seqday == 0 only the first time and after three days (early period)
        if seqday == 0 or seqday == 2:
            date_posted = photo_info['dates']['posted']
            date_taken = photo_info['dates']['posted']
            dt = datetime.datetime.utcnow()
            date_download = calendar.timegm(dt.utctimetuple())
            photo_title = ''
            photo_title = photo_info['title']['_content']
            photo_title = photo_title.replace("'"," ")
            photo_title = photo_title.replace("’"," ")
            photo_title = photo_title.replace("\n"," ")
            photo_title = ftfy.fix_text(unicode(photo_title))
            print "Title: " + photo_title

            #TODO: use the function sanitize_text
            photo_description = ''
            photo_description = photo_info['description']['_content']
            photo_description = photo_description.replace("'"," ")
            photo_description = photo_description.replace("’"," ")
            photo_description = photo_description.replace("\""," ")
            photo_description = photo_description.replace("\n"," ")
            photo_description = ftfy.fix_text(unicode(photo_description))
            #print "Description: " + photo_description
            
            photo_tags_num = len(photo_info['tags']['tag'])
            photo_tags = [sanitize_text(str(t['_content'])) for t in photo_info['tags']['tag']]
            print "# of tags:\t" + str(photo_tags_num)
 #           print photo_tags
            
            lat = ""
            lon = ""
            country = ""
            if 'location' in photo_info:
                lat = photo_info['location']['latitude']
                lon = photo_info['location']['longitude']
                country = photo['location']['country']['_content']


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
                avg_group_memb = 0 if len(groups_members)==0 else mean(groups_members)
                avg_group_photos = 0 if len(groups_photos)==0 else mean(groups_photos)
            #    if photo_groups > 0:
                #    print json.dumps(photo_groups_ids)
            print "The photo is shared through\t" +str(photo_sets)+"\talbums and\t"+str(photo_groups)+"\tgroups."
 
 
            print "Getting user info..."
            response = flickr.people.getInfo(api_key = api_key, user_id=user_id)            
            print "request result:\t"+response['stat']
            ispro = int(response['person']['ispro'])
            has_stats = int(response['person']['has_stats']) 
            username = response['person']['username']['_content']
#            if 'location' in response['person']:
 #               location = response['person']['location']['_content']        

            user_photos = int(response['person']['photos']['count']['_content'])        

            print "Getting user contacts..."
            response = flickr.contacts.getPublicList(api_key = api_key, user_id=user_id)            
            print "request result:\t"+response['stat']
            contacts = int(response['contacts']['total'])
 
 
             
            #Notes: the mean of the views takes into account the oldest 500 photos of the user (or fewer)
            print "Getting photos stats..."
            user_photo_views = []
            page_n = 1
            while len(user_photo_views)< user_photos:
                response = flickr.people.getPublicPhotos(api_key = api_key, user_id=user_id, extras='views', page=page_n, per_page=500)            
                print "request result:\t"+response['stat']
                page_elements = [int(p['views']) for p in response['photos']['photo']]
                user_photo_views.extend(page_elements)
                page_n += 1
                #Integrity check                
                if len(page_elements)<500:
                    break
            user_mean_views = mean(user_photo_views)
            print "The user's photos have a mean view rate of\t"+str(user_mean_views)+"\tcomputed on\t"+str(len(user_photo_views))+"\tphotos."
            
            print "Getting user groups info..."
            response = flickr.people.getGroups(api_key = api_key, user_id=user_id)            
            print "request result:\t"+response['stat']
            user_groups_membs = [int(g['members']) for g in response['groups']['group']]
            user_groups_photos = [int(g['pool_count']) for g in response['groups']['group']]
            user_groups = len(user_groups_photos)
            avg_user_gmemb = 0 if len(user_groups_membs)==0 else mean(user_groups_membs)
            avg_user_gphotos = 0 if len(user_groups_photos)==0 else mean(user_groups_photos)
            print "The user has\t"+str(contacts)+"\tcontacts and is enrolled in\t" +str(user_groups)+"\tgroups with\t"+str(avg_user_gmemb)+"\tmean members and\t"+str(avg_user_gphotos)+"\tmean photos."

            # DB interaction

            con = lite.connect('user_info.db')
            cur = con.cursor()
            cur.execute("INSERT INTO user_info(UserId, \
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
                        ")")
                      #  ", "+str(json.dumps(photo_groups_ids))+")")
            con.commit()
            con.close()
            print "User record added." 
 
            con = lite.connect('headers.db')
            cur = con.cursor()
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
            con.close()
            print "Header record added."
            
            
            tags = json.dumps(photo_tags).replace("'","''")
       #     print tags
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
            cur.execute(q)
            con.commit()
            con.close()
            print "Image info record added."
       
        """
        con = lite.connect('headers.db')
        cur = con.cursor()
        rows = cur.execute("SELECT * FROM headers")
        for r in rows:
            print r
        con.close()
        con = lite.connect('image_info.db')
        cur = con.cursor()
        rows = cur.execute("SELECT * FROM image_info")
        for r in rows:
            print r
        
        """
        #Getting daily information
        photo_views = int(photo_info['views'])
        photo_comments = int(photo_info['comments']['_content'])        

        print "Getting photo favorites..."
        response = flickr.photos.getFavorites(api_key = api_key, photo_id=photo_id)            
        print "request result:\t"+response['stat']
        photo_favorites = int(response['photo']['total'])
     
        print photo_url,'\n','views:\t',photo_views,'\tcomments:\t',photo_comments
        con = lite.connect('image_daily.db')
        cur = con.cursor()
        cur.execute("INSERT INTO image_daily(FlickrId, \
                                            Day, \
                                            Comments, \
                                            Views, \
                                            Favorites) VALUES('"+\
                    photo_id+"',"+str(seqday)+", "+str(photo_comments) + \
                    ", "+str(photo_views)+", "+str(photo_favorites)+")")
        con.commit()
        con.close()
        print "Image daily record added."
        print "Image:\t"+photo_id+"\tday:\t"+str(seqday)+"\n"
        return True
            
     #   last_update = photo_info['dates']['lastupdate']
       # The <date> element's lastupdate attribute is a Unix timestamp indicating the last time the photo, or any of its metadata (tags, comments, etc.) was modified.
        
        if check:
            return False
    except Exception, e:
        print "ERROR with Photo\t"+photo_id+":"
        print str(e)
       # print q
        sys.exit(0)
    

##
## Load list of known images, or create a new one
##

# Keeps the list of known images
known_images = []
pickle_image_list = 'known_images.pickle'

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
                                Favorites INT)"

create_db(image_daily_db, t_name, query, drop_existing = True)


t_name = 'user_info'
query = "CREATE TABLE user_info(Id INTEGER PRIMARY KEY, \
							UserId TEXT, \
							Day INT, \
							Username TEXT, \
                                Ispro INT, \
                                HasStats INT, \
                                Contacts INT, \
							Location TEXT, \
                                PhotoCount INT, \
                                MeanViews REAL, \
                                GroupsCount INT, \
                                GroupsAvgMembers REAL, \
                                GroupsAvgPictures REAL)"

create_db(user_info_db, t_name, query, drop_existing = True)


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


count = 0        
sleep_time = 10
print "Number of images to download:\t"+str(new_images_count)    

#extra_info = 'date_taken, date_upload, geo, tags, description, title, views, owner_name'
extra_info = '' 
flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')


# Get the list of images to download
#photo_data = []
photo_set = []
not_available_photos = []
while len(photo_set) <= new_images_count:

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
        #TODO: invece di andare in sleep, recupera le info delle nuove immagini
        new_photo_ids = set(page_1+page_2) - set(photo_set)
        new_photo_ids = list(new_photo_ids)
        photo_set = list(set(photo_set+page_1+page_2))
     #   photo_data.extend(recent_photos_p1['photos']['photo'])
      #  photo_data.extend(recent_photos_p2['photos']['photo'])
        
        print "Unique photos:\t" + str(len(photo_set)) + "/" + str(new_images_count)
        print "Adding\t" + str(len(new_photo_ids))+ "\tnew photos"
        

#        for photo in photo_data:
 #           photo_id = photo['id']
        for photo_id in photo_set:
            if photo_id not in new_photo_ids:
                print "Skipping (existing)\t"+photo_id
                continue

            res = daily_monitoring(photo_id, 0)            
            #Remove the processed photo id from the list, handle the photo after
            if not res:
                not_available_photos.append(photo_id)
            
            new_photo_ids.remove(photo_id)
            
  
        print "Sleeping (new attempt after "+str(20)+" seconds)..."
        time.sleep(20)
        
        """
        sys.exit(0)
        photo_info = response['photo']
       #   response = flickr.photos.getSizes(api_key = api_key, photo_id=photo_id)
        print "Photo ID:\t"+photo_id+"\t-\tgetting photo stats..."
        stats = flickr.stats.getPhotoStats(date=photo_info['dates']['posted'], photo_id = photo_id)            
        print "request result:\t"+stats['stat']
        picts_with_stats = picts_with_stats +1
        """     
    except Exception, e:
        print "Error:"
        print str(e)
        if attempts >= 5:
            print "Too many failed attempts. Exit."
            break
        attempts += 1
        print "Sleeping (new attempt after "+str(sleep_time)+" seconds)..."
        time.sleep(sleep_time)
        print "Awake .. "
            
print "Not available photos:"
print "total:\t"+ str(len(not_available_photos))
for id in not_available_photos:
    print id
    
"""
TODO:
    - aggiorno lista data pickle
    - faccio la chiamata per day 0
    - implementare chiamata a parte per daily update
"""
"""            
    #Interrompo qui
    continue
        
    photo_info = response['photo']
     #       photo_url = str(photo_info['urls']['url'][0]['_content'])
    ext = 'jpg'
    photo_url = 'https://farm'+str(photo_info['farm'])+'.staticflickr.com/'+str(photo_info['server'])+'/'+photo_id+'_'+str(photo_info['secret'])+'_b.'+ext
    photo_views = int(photo_info['views'])
    photo_comments = int(photo_info['comments']['_content'])
    post_date = photo_info['dates']['posted']
    last_update = photo_info['dates']['lastupdate']
   # The <date> element's lastupdate attribute is a Unix timestamp indicating the last time the photo, or any of its metadata (tags, comments, etc.) was modified.
 
#    photo_pop = 10**5 * float(photo_views)/(int(time.time()) - int(post_date))
    photo_pop = 10**5 * float(photo_views)/(int(last_update) - int(post_date))
    print photo_url,'\n','views:\t',photo_views,'\tcomments:\t',photo_comments,'\tpopularity:\t',photo_pop,' (x10^-5)'


    # Download the photo and check if still available
    img_path = "images2/"+photo_id#+".jpg"   
#    httpRes = urllib.urlretrieve("https://farm5.staticflickr.com/4054/4287743529_4d1bccb6d7_b.jpg", "ciao")
    httpRes = urllib.urlretrieve(photo_url, img_path)
    # Questa funzione usa urllib2    
    #downloadImage(photo_url,img_path)    
    abs_path = os.path.abspath(img_path)
    
    check = isMissing(img_path)
    print "Is missing:\t" + str(check)
    
    if not check:
            count = count +1    #Only counts the 'good' photos

    # DB interaction   
    con = lite.connect('flickrCrossSentiment.db')
    with con:
        cur = con.cursor()
        cur.execute("INSERT INTO Image(FlickrId, URL, Path, PostDate, LastUpdate, Comments, Views) VALUES('"+\
                photo_id+"', '"+photo_url+"', '"+abs_path + \
                "', "+str(post_date)+", "+str(last_update) +  \
                ", "+str(photo_comments)+", "+str(photo_views)+")")
    
#response = flickr.stats.getPhotoStats(api_key = api_key,photo_id=photo_id)
print "Pictures with stats:\t" + str(picts_with_stats) + "/" + str(len(image_pool))
"""




