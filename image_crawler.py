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
import time
from skimage.measure import structural_similarity as ssim
import cv2
import numpy as np
#import matplotlib.pyplot as plt
from sys import argv
import sqlite3 as lite


"""
    Settings:
        
        -   Flickr API Settings
        -   Number of images to crawl

"""
# Null image name
referenceImage="flickrMissing"

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

new_images_count = 0      # Set it to zero to update the existing pictures  

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
    refImgPath = project_root_dir + referenceImage
    refImg = cv2.imread(refImgPath)
    curImg = cv2.imread(imagePath)
    
        
    refImg = cv2.cvtColor(refImg, cv2.COLOR_BGR2GRAY)
    curImg = cv2.cvtColor(curImg, cv2.COLOR_BGR2GRAY)
    
    curImg = cv2.resize(curImg,(refImg.shape[1], refImg.shape[0]))
    
    
    s = ssim(refImg,curImg)
    print "SSIM:\t"+str(s)
    return s>0.99
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

if len(argv)>1:
    seqday = int(argv[1])
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
query = "CREATE TABLE "+t_name+"(Id INTEGER PRIMARY KEY, \
							FlickrId TEXT, \
							UserId TEXT, \
							GroupsIds TEXT, \
							DateCrawl TEXT)"

create_db(headers_db, t_name, query, drop_existing = False)


# Information that shouldn't change. If they do, a new record is added.
t_name = 'image_info'
query = "CREATE TABLE "+t_name+"(Id INTEGER PRIMARY KEY, \
							FlickrId TEXT, \
							Day TEXT, \
                                Camera TEXT, \
                                Size INT, \
							Title TEXT, \
							Description TEXT, \
                                NumSets INT, \
                                NumGroups INT, \
							Tags TEXT, \
							DatePosted TEXT, \
							DateTaken, \
							URL TEXT, \
							Latitude DOUBLE, \
							Longitude DOUBLE, \
                                Country TEXT)"

create_db(image_info_db, t_name, query, drop_existing = False)

# Information collected daily
t_name = 'image_daily'
query = "CREATE TABLE "+t_name+"(Id INTEGER PRIMARY KEY, \
							FlickrId TEXT, \
							Day TEXT, \
							Comments INT, \
                                Views INT, \
                                Favorites INT)"

create_db(image_daily_db, t_name, query, drop_existing = False)


t_name = 'user_info'
query = "CREATE TABLE "+t_name+"(Id INTEGER PRIMARY KEY, \
							UserId TEXT, \
							Day TEXT, \
							Username TEXT, \
                                Ispro INT, \
                                Contacts INT, \
							Location TEXT, \
                                PhotoCount INT, \
                                MeanViews REAL, \
                                GroupsCount INT, \
                                GroupsAvgMembers REAL, \
                                GroupsAvgPictures REAL)"

create_db(user_info_db, t_name, query, drop_existing = False)


t_name = 'groups_info'
query = "CREATE TABLE "+t_name+"(Id INTEGER PRIMARY KEY, \
							GroupId TEXT, \
							Day TEXT, \
							Members INT, \
							Photos INT)"

create_db(groups_info_db, t_name, query, drop_existing = False)
##-----------------------------------------------------------------


##
## Image and meta-data crawling
##


count = 0        
sleep_time = 10
print "Number of images to download:\t"+str(new_images_count)    

extra_info = 'date_taken, date_upload, geo, tags, description, title, views, owner_name'
flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')


# Get the list of images to download
new_images_count = 1000
photo_data = []
photo_ids = []
while len(photo_ids) <= new_images_count:

    attempts = 0
    try :
        """            
        recent_photos['photos']['photo'][0].keys()
        [u'isfamily', u'dateupload', u'ispublic', u'description', 
        u'datetakengranularity', u'farm', u'datetakenunknown', u'views',
        u'longitude', u'server', u'datetaken', u'isfriend', u'secret', u'ownername', 
        u'context', u'owner', u'title', u'latitude', u'id', u'tags', u'accuracy']
        """            
        # Request the first 2 pages of the most recent public photos on Flickr
        print "\n\nGetting recent photos..."
        recent_photos_p1 = flickr.photos.getRecent(api_key= api_key, per_page = 500, page= 1, extras = extra_info)
        page_1 = [photo['id'] for photo in recent_photos_p1['photos']['photo']]
        print "First page request:\t"+recent_photos_p1['stat']
        recent_photos_p2 = flickr.photos.getRecent(api_key= api_key, per_page = 500, page= 2, extras = extra_info)
        page_2 = [photo['id'] for photo in recent_photos_p2['photos']['photo']]
        print "Second page request:\t"+recent_photos_p2['stat']
        #Some photos may shift to the second page between the two calls            
        photo_set = list(set(page_1+page_2))
        photo_ids.extend(photo_set)
        photo_data.extend(recent_photos_p1['photos']['photo'])
        photo_data.extend(recent_photos_p2['photos']['photo'])
        

        print "Unique photos:\t" + str(len(photo_set)) + "/" + str(len(page_1)+len(page_2))
 
#            print json.dumps(recent_photos)
        
 #            response = flickr.photos.getInfo(api_key = api_key, photo_id=photo_id)            
 #           print "request result:\t"+response['stat']
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
        print str(e)
        if attempts >= 5:
            break
        attempts += 1
        print "Sleeping (new attempt after "+str(sleep_time)+" seconds)..."
        time.sleep(sleep_time)
        print "Awake .. "
            
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




