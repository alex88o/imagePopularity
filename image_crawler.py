# -*- coding: utf-8 -*-
"""
Created on Tue Nov 29 10:53:14 2016

@author: alessandro
"""

import flickrapi
import json
import urllib, urllib2
import sqlite3 as lite
import csv
import sys, os
import time
from skimage.measure import structural_similarity as ssim
import cv2
import numpy as np
import matplotlib.pyplot as plt
"""
    Settings:
        
        -   Flickr API Settings
        -   Dataset Settings

"""
# Credenziali The Social Picture
api_key = u'c3388aa658417c77dcc98d5f9dc3ac91'
api_secret = u'9f3693a3ab57bfc1'

# Credenziali iplabsocial (alessandro.ortis)
api_key= u'394b14cc54cd9cba5aa0d68b1d5f7eb9'
api_secret = u'9bda221d1de625a9'

# create Flickr image pool from data
dataset_dir = "/home/alessandro/CrossSentiment/FlickrDatasetKatsurai/"
project_root_dir = "/home/alessandro/flickrCrawling/"
image_pool = []



""" END SETTINGS """

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

referenceImage="flickrMissing"

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
# Le seguenti due righe sono state eseguite una volta sola per generare il token di autorizzazione    
#flickr = flickrapi.FlickrAPI(api_key, api_secret)
#flickr.authenticate_via_browser(perms='read')
oauth_token=u'72157675663685032-6052b3ccbdc594e8'
oauth_verifier=u'1103dab7cc7d9c5e'

# Crea il pool di immagini del dataset di Katsurai

for i in range(3):
    filename = "flickr" + str(i+1) + "_icassp2016_dataset.csv"
    filepath = dataset_dir + filename
    
    try:
        csvfile = open(filepath,'rb')
        csvreader = csv.reader(csvfile, delimiter=',')
    except:
        print('Error reading file ',filename)
        print sys.exc_info()[0]       
        raise
    
    #skip the first row (header)
    header = csvreader.next()
    print header
    for row in csvreader:
        #print row
        rc = createRecord(row)
        image_pool.append(rc)


count = 0        
sleep_time = 10
picts_with_stats = 0
print "Dataset dims:\t"+str(len(image_pool))    
#photo_id = image_pool[0]['ImageID']
for i in range(len(image_pool)):

    count = count +1
  #  if count>12:
   #     break

    photo_id = image_pool[i]['ImageID']        
    flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')
    tryflag = True
    while tryflag :
        try :
            print "\n\nPhoto ID:\t"+photo_id+"\t-\tgetting photo info..."
            response = flickr.photos.getInfo(api_key = api_key, photo_id=photo_id)            
            print "request result:\t"+response['stat']
            photo_info = response['photo']
           #   response = flickr.photos.getSizes(api_key = api_key, photo_id=photo_id)
            print "Photo ID:\t"+photo_id+"\t-\tgetting photo stats..."
            stats = flickr.stats.getPhotoStats(date=photo_info['dates']['posted'], photo_id = photo_id)            
            print "request result:\t"+stats['stat']
            picts_with_stats = picts_with_stats +1
            
            tryflag = False
        except Exception, e:
            print str(e)
            break
            print "Sleeping (new attempt after "+str(sleep_time)+" seconds)..."
            time.sleep(sleep_time)
            print "Awake .. "
            
            
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
    """
    The <date> element's lastupdate attribute is a Unix timestamp indicating the last time the photo, or any of its metadata (tags, comments, etc.) was modified.
    """
#    photo_pop = 10**5 * float(photo_views)/(int(time.time()) - int(post_date))
    photo_pop = 10**5 * float(photo_views)/(int(last_update) - int(post_date))
    print photo_url,'\n','views:\t',photo_views,'\tcomments:\t',photo_comments,'\tpopularity:\t',photo_pop,' (x10^-5)'

    img_path = "images2/"+photo_id#+".jpg"   
#    httpRes = urllib.urlretrieve("https://farm5.staticflickr.com/4054/4287743529_4d1bccb6d7_b.jpg", "ciao")
    httpRes = urllib.urlretrieve(photo_url, img_path)
    # Questa funzione usa urllib2    
    #downloadImage(photo_url,img_path)    
    abs_path = os.path.abspath(img_path)
    
    check = isMissing(img_path)
    print "Is missing:\t" + str(check)
    continue

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
