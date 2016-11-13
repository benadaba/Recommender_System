# -*- coding: utf-8 -*-
"""
Created on Sat Nov 12 17:09:35 2016

@author: bernard
"""


from flask import Flask, jsonify, request
from scikits.crab import datasets
from sklearn.datasets.base import Bunch
import numpy as np


app = Flask(__name__)   


    
##connecting to the database    
import sqlalchemy
import pyodbc

#to hold the data from our database
movies_data = []
engine = ''
try:
 
    import urllib
    params = urllib.quote_plus("DRIVER={SQL Server Native Client 11.0};SERVER=.\MSSQLSERVER_ENT;DATABASE=Antrak;Trusted_Connection=yes;")
 
    engine = sqlalchemy.create_engine('mssql+pyodbc:///?odbc_connect=%s"' % params)
    
    engine.execute("insert into antrak.dbo.recommender_customers_tb values ('John','UK'), ('John','UK'),('Elvis','UK'), ('John','US')")
 
    #results.to_sql("clusterSegments", engine, if_exists = 'replace')#
    result = engine.execute("select * from antrak.dbo.recommender_rankings")
    #dat = np.loadtxt(result,dtype=str)
    for row in result:
        movies_data.append(row[0:3])
        
except (RuntimeError, TypeError, NameError):
    print('Error in Conneccting')
    print(RuntimeError, TypeError, NameError)
    
#lets convert the list of tuples to array as the recommender needs
data_m = np.asarray(movies_data)    

#let define a function to load the data from the array

import pandas as pd
def load_sample_data():

    #base_dir = join(dirname(__file__), 'data/')

    #Read data
    #data_m = np.loadtxt(csvcontent,
    #data_m = np.loadtxt(movies_data,
    #data_m = np.loadtxt(base_dir + 'sample_movies.csv',
            #delimiter=';', dtype=str)
    #for line in csvcontent.splitlines():
        #data_m = str.parseLine(line)
    #data_ini = csvcontent.split(";")
    #data_m= np.loadtxt(data_ini, dtype = str)
    #print(data_m)
    #data_

    item_ids = []
    user_ids = []
    data_songs = {}
    for user_id, item_id, rating in data_m:
        if user_id not in user_ids:
            user_ids.append(user_id)
        if item_id not in item_ids:
            item_ids.append(item_id)
        u_ix = user_ids.index(user_id) + 1
        i_ix = item_ids.index(item_id) + 1
        data_songs.setdefault(u_ix, {})
        data_songs[u_ix][i_ix] = float(rating)

    data_t = []
    for no, item_id in enumerate(item_ids):
        data_t.append((no + 1, item_id))
    data_titles = dict(data_t)

    data_u = []
    for no, user_id in enumerate(user_ids):
        data_u.append((no + 1, user_id))
    data_users = dict(data_u)

    #fdescr = open(dirname(__file__) + '/descr/sample_movies.rst')

    return Bunch(data=data_songs, item_ids=data_titles,
                 #user_ids=data_users, DESCR=fdescr.read())
                 user_ids=data_users)
                 
                 
#let's call the function and view sample data
movies = load_sample_data()

#get sample user
movies.user_ids.get(148)

from scikits.crab.models import MatrixPreferenceDataModel

#Build the model
model = MatrixPreferenceDataModel(movies.data)

from scikits.crab.metrics import pearson_correlation

from scikits.crab.similarities import UserSimilarity

#Build the similarity
similarity = UserSimilarity(model, pearson_correlation)

from sklearn.base import BaseEstimator

from scikits.crab.recommenders.knn import UserBasedRecommender
#build the user Based recommender
recommender = UserBasedRecommender(model, similarity, with_preference=True)

# get top N recommended countries
# @user_id : id of the customer to be recommended a product
# @n: Number of recommendations to make , with the highest rated recommended products in top
recdit = {}
def topNRecsUser(user_id, n):
    
    #lets ingore the warnings
    import warnings
    warnings.filterwarnings('ignore')
    
    #recdit = {}
    rec_items = recommender.recommend(user_id)
    
    #get top n ids
    topN = rec_items[:n]
    
    #get the ids of all recommmended countries
    rec_count_id = [item[0] for item in topN]
    
    #lets get the names of the top 5 recommended countries
    rec_countries = [movies.item_ids[x] for x in rec_count_id]
    recdit[movies.user_ids.get(user_id)] = rec_countries
    
    return recdit
    
    
userrec = topNRecsUser(102,5)

@app.route("/dbf2", methods=["GET"])
def testDB():
    #Connect to databse#
    #Perform query and return JSON data
    query = engine.execute("select top 3 Country from antrak.dbo.recommender_rankings")
    return jsonify({'country': [i[0] for i in query.cursor.fetchall()]})

languages = [{'name':'Javascript'}, {'name':'Python'}, {'name':'Ruby'}]

@app.route("/", methods=["GET"])
def test():
    return jsonify({'message':'It Works!'})
    

@app.route("/lang", methods=["GET"])
def getAll():
    return jsonify({"languages":languages})

@app.route("/lang/<string:name>", methods=['GET'])
def returnOne(name):
    langs = [language for language in languages if language['name'] == name]
    return jsonify({'language':langs[0]})
    
@app.route("/dbf", methods=["GET"])
def getDB():    
    return jsonify({"languages":languages})
    
    
##POST REQUEST API to posting request to the API
@app.route("/lang", methods=["POST"])
def addOne():
    language = {'name':request.json['name']}
    languages.append(language)
    return jsonify({'languages':languages})
   
   
##Using PUT request to edit data
@app.route("/lang/<string:name>", methods = ['PUT'])   
# define a function and pass in the name argument user sends
def editOne(name):
    #lets find the name in the languages which matches the one the person ssends
    lang = [language for language in languages if language['name'] == name]
    
    #lets update the name which was returned from the previus line to the name passed
    # in the json object
    lang[0]['name'] =  request.json['name']
    
    #lets return the jasonify version of the name wwhich was updated
    return jsonify({'language':lang[0]})
    

#lets work on DELETING an item 
@app.route("/lang/<string:name>",  methods=['DELETE'])  

#lets define a function to delete
def deleteOne(name):
    
    # for a language name that matches the name passed in the parameter
    lang = [language for language in languages if language['name'] == name]
    
    #remove the language returned from the previous step from the languages list
    languages.remove(lang[0])
    
    #return the jsonify version
    return jsonify({'languages_DELETE':languages})


#lets send recommended item to a GET RESPONSE
@app.route("/recommender", methods = ['GET'])
def recommend():
    return jsonify({'recommended':recdit})
    

#lets retrieve the recommended destinations to our customer by the customer's name
    
   
if __name__ == '__main__':
    app.run(debug=True, port=8080)  # run on port 8080 in debug mode
