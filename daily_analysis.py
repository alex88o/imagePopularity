# -*- coding: utf-8 -*-
"""
Created on Mon Oct  2 11:13:27 2017

@author: alessandro
"""

from image_crawler import daily_monitoring
import pickle
from sys import argv



# Credenziali iplabsocial (alessandro.ortis)
#api_key= u'394b14cc54cd9cba5aa0d68b1d5f7eb9'
#api_secret = u'9bda221d1de625a9'

# Le seguenti due righe sono state eseguite una volta sola per generare il token di autorizzazione    
#flickr = flickrapi.FlickrAPI(api_key, api_secret)
#flickr.authenticate_via_browser(perms='read')
oauth_token=u'72157675663685032-6052b3ccbdc594e8'
oauth_verifier=u'1103dab7cc7d9c5e'
pickle_image_list = 'known_images.pickle'




with open(pickle_image_list,'r') as f:
    images_list = pickle.load(f)


print "Check for duplicates..."
dup = len(images_list) - len(list(set(images_list)))
print "duplicates:\t"+str(dup)

seqday = int(argv[1])
err_list = []
for photo_id in images_list:
    res = daily_monitoring(photo_id, seqday) 
    if res:
        print "Image\t"+photo_id+"\tanalyzed for day\t"+str(seqday)
    else:
        print "Image\t"+photo_id+"\terror occurred during day\t"+str(seqday)
        err_list.append(photo_id)
        
print "Images with errors:"
print err_list