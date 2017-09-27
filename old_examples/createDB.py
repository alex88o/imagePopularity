# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 18:45:15 2016

@author: alessandro
"""

import sqlite3 as lite
import sys

con = lite.connect('flickrCrossSentiment.db')

with con:
    
    cur = con.cursor()    
    cur.execute("DROP TABLE IF EXISTS Image")
    cur.execute("CREATE TABLE Image(Id INTEGER PRIMARY KEY, FlickrId TEXT, URL TEXT, Path TEXT, PostDate INT, LastUpdate INT, Comments INT, Views INT)")