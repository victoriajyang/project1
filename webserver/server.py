#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
COMS W4111 Introduction to Databases Fall 2018 (Prof. Wu).
Webserver for project 1. 
Team: Victoria Yang (vjy2102), Yuxuan Mei (ym2552).
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from film import Film
from Actor import Actor
from Company import Company

# Need to create app that is needed for all operations afterwards. 
tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
# Have to use this global cache to make this global engine work.
cache = {'engine' : None}

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible for one request.
  """
  engine = cache['engine']
  try:
    g.conn = engine.connect()
  except:
    print "error creating temporary connection to the db"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass

# Homepage route.
@app.route('/')
def index():
  if app.debug: print request.args
  if 'films' in cache and len(cache['films']) > 0: 
    return render_template("index.html", **cache)
  # Default to list 30 films.
  cursor = g.conn.execute("""SELECT * FROM Film 
    INNER JOIN Filmmaker ON Film.filmmaker_imdblink = Filmmaker.imdblink
    INNER JOIN FilmingLocations ON Film.imdblink = FilmingLocations.film_imdblink
    INNER JOIN NYCLocation ON (FilmingLocations.latitude = NYCLocation.latitude
            AND FilmingLocations.longitude = NYCLocation.longitude) LIMIT 30;""")
  films = []
  for result in cursor: films.append(Film(result)) 
  cursor.close()
  cache['films'] = films
  return render_template("index.html", **cache)

# Film actor details page route.
@app.route('/actor_details/<url_encoded_name>/<int:year>', methods=['GET'])
def actor_details(url_encoded_name, year):
  if app.debug: print request.args
  qry = """SELECT * FROM Film 
    INNER JOIN Appearances ON Film.imdblink = Appearances.film_imdblink
    INNER JOIN Actor ON (Appearances.actor_imdblink = Actor.imdblink)
    INNER JOIN Character ON (Appearances.cid = Character.cid)  
    WHERE Film.url_encoded_name = :film AND Film.year = :y;"""
  cursor = g.conn.execute(text(qry), film = url_encoded_name, y = year)
  actors = []
  for result in cursor: actors.append(Actor(result)) 
  cursor.close()
  cache['actors'] = actors
  cache['current_film'] = actors[0].film_name
  cache['current_film_imdblink'] = actors[0].film_imdblink
  return render_template("actor-details.html", **cache)

# Film company details page route.
@app.route('/company_details/<url_encoded_name>/<int:year>', methods=['GET'])
def company_details(url_encoded_name, year):
  if app.debug: print request.args
  qry = """SELECT * FROM Film 
    INNER JOIN CompanyCredits ON (CompanyCredits.film_imdblink = Film.imdblink) 
    INNER JOIN Company ON (CompanyCredits.company_imdblink = Company.imdblink) 
    WHERE Film.url_encoded_name = :film AND Film.year = :y;"""
  cursor = g.conn.execute(text(qry), film = url_encoded_name, y = year)
  companies = []
  for result in cursor: companies.append(Company(result))
  cursor.close()
  cache['companies'] = companies
  cache['current_film'] = companies[0].film_name
  cache['current_film_imdblink'] = companies[0].film_imdblink
  return render_template("company-details.html", **cache)

# Film search results route.
@app.route('/filter_by_film', methods=['POST'])
def filter_by_film():
  if len(request.form['film']) < 1: 
    return render_template("index.html", **cache)
  if app.debug: print request.args
  filmname = '%' + request.form['film'].lower() + '%'
  if app.debug: print filmname
  qry = """SELECT * FROM Film 
    INNER JOIN Filmmaker ON Film.filmmaker_imdblink = Filmmaker.imdblink
    INNER JOIN FilmingLocations ON Film.imdblink = FilmingLocations.film_imdblink
    INNER JOIN NYCLocation ON (FilmingLocations.latitude = NYCLocation.latitude
            AND FilmingLocations.longitude = NYCLocation.longitude)
    WHERE LOWER(Film.title) LIKE :film_searchstring;"""
  cursor = g.conn.execute(text(qry), film_searchstring = filmname)
  films = []
  for result in cursor: films.append(Film(result)) 
  cursor.close()
  cache['films'] = films
  return render_template("index.html", **cache)

# Location search results route.
@app.route('/filter_by_location', methods=['POST'])
def filter_by_location():
  if len(request.form['location']) < 1:
    return render_template("index.html", **cache)
  if app.debug: print request.args
  location = '%' + request.form['location'].lower() + '%'
  if app.debug: print location
  qry = """SELECT * FROM Film 
    INNER JOIN Filmmaker ON Film.filmmaker_imdblink = Filmmaker.imdblink
    INNER JOIN FilmingLocations ON Film.imdblink = FilmingLocations.film_imdblink
    INNER JOIN NYCLocation ON (FilmingLocations.latitude = NYCLocation.latitude
            AND FilmingLocations.longitude = NYCLocation.longitude)
    WHERE LOWER(NYCLocation.address) LIKE :location_searchstring;"""
  cursor = g.conn.execute(text(qry), location_searchstring = location)
  films = []
  for result in cursor: films.append(Film(result)) 
  cursor.close()
  cache['films'] = films
  return render_template("index.html", **cache)

# Neighborbood dropdown results route.
@app.route('/filter_by_neighborhood/<neighborhood>', methods=['GET'])
def filter_by_neighborhood(neighborhood):
  if app.debug: print request.args
  qry = """SELECT * FROM Film 
    INNER JOIN Filmmaker ON Film.filmmaker_imdblink = Filmmaker.imdblink
    INNER JOIN FilmingLocations ON Film.imdblink = FilmingLocations.film_imdblink
    INNER JOIN NYCLocation ON (FilmingLocations.latitude = NYCLocation.latitude
            AND FilmingLocations.longitude = NYCLocation.longitude)
    WHERE NYCLocation.neighborhood = :neighborhood_str;"""
  cursor = g.conn.execute(text(qry), neighborhood_str = neighborhood)
  films = []
  for result in cursor: films.append(Film(result)) 
  cursor.close()
  cache['films'] = films
  return render_template("index.html", **cache)

# Borough dropdown results route.
@app.route('/filter_by_borough/<borough>', methods=['GET'])
def filter_by_borough(borough):
  if app.debug: print request.args
  qry = """SELECT * FROM Film 
    INNER JOIN Filmmaker ON Film.filmmaker_imdblink = Filmmaker.imdblink
    INNER JOIN FilmingLocations ON Film.imdblink = FilmingLocations.film_imdblink
    INNER JOIN NYCLocation ON (FilmingLocations.latitude = NYCLocation.latitude
            AND FilmingLocations.longitude = NYCLocation.longitude)
    WHERE NYCLocation.borough = :borough_str;"""
  cursor = g.conn.execute(text(qry), borough_str = borough)
  films = []
  for result in cursor: films.append(Film(result)) 
  cursor.close()
  cache['films'] = films
  return render_template("index.html", **cache)

if __name__ == "__main__":
  import argparse
  DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
  parser = argparse.ArgumentParser()
  parser.add_argument('--host', default='0.0.0.0', help='host ip address')
  parser.add_argument('--port', default=8111, help='port number', type=int)
  parser.add_argument('--user', default='ym2552', help='username for connecting to the db')
  parser.add_argument('--pwd', required=True, help='password for connecting to the db')
  parser.add_argument('--debug', action='store_true', help='whether to run in debug mode')
  parser.add_argument('--threaded', action='store_true', help='whether to run in multi threads')
  args = parser.parse_args()
  
  # The Database URI should be in the format of: 
  #     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
  user = args.user
  pwd = args.pwd
  DB_URI = 'postgresql://%s:%s@%s/w4111' % (user, pwd, DB_SERVER)
  # Create a database engine that connects to the database of the given URI. 
  engine = create_engine(DB_URI)
  cache['engine'] = engine
  if args.debug: print 'engine created'

  # Below is the first batch of queries to prepare the dropdown items.
  try:
    tconn = engine.connect()
  except:
    print "error creating temporary connection to the db"
    import traceback; traceback.print_exc()
    tconn = None
  
  cursor = tconn.execute("""SELECT DISTINCT borough from NYCLocation;""")
  boroughs = []
  for result in cursor: boroughs.append(result[0])
  cursor.close()
  cache['boroughs'] = boroughs

  cursor = tconn.execute("""SELECT DISTINCT neighborhood from NYCLocation;""")
  neighborhoods = []
  for result in cursor: neighborhoods.append(result[0])
  cursor.close()
  cache['neighborhoods'] = neighborhoods

  try:
    tconn.close()
  except Exception as e:
    pass

  # Now ready to serve the page.
  HOST, PORT = args.host, args.port
  print 'running on %s:%d' % (HOST, PORT)
  app.run(host=HOST, port=PORT, debug=args.debug, threaded=args.threaded)
