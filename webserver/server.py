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
    print "uh oh, problem connecting to database"
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

#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """
  if app.debug: print request.args
  #
  # example of a database query
  #
  cursor = g.conn.execute("""SELECT * FROM Film INNER JOIN Filmmaker ON Film.filmmaker_imdblink = Filmmaker.imdblink
    INNER JOIN FilmingLocations ON Film.imdblink = FilmingLocations.film_imdblink
    INNER JOIN NYCLocation ON (FilmingLocations.latitude = NYCLocation.latitude
            AND FilmingLocations.longitude = NYCLocation.longitude) LIMIT 10;""")
  films = []
  for result in cursor:
    films.append(Film(result)) 
  cursor.close()
  cache['films'] = films
  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **cache)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/film')
def film():
  return render_template("film.html")

# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  if app.debug: print name
  cmd = 'INSERT INTO test(name) VALUES (:name1)';
  g.conn.execute(text(cmd), name1 = name);
  return redirect('/')

@app.route('/filter_by_film', methods=['GET'])
def add():
  filmname = request.form['film']
  if app.debug: print filmname
  qry = """SELECT """
  cmd = 'INSERT INTO test(name) VALUES (:name1)';
  g.conn.execute(text(cmd), name1 = name);
  return render_template("index.html", **cache)

@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()

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
  
  user = args.user
  pwd = args.pwd
  # The Database URI should be in the format of: 
  #     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
  DB_URI = 'postgresql://%s:%s@%s/w4111' % (user, pwd, DB_SERVER)
  # Create a database engine that connects to the database of the given URI. 
  engine = create_engine(DB_URI)
  cache['engine'] = engine
  if args.debug: print 'engine created'

  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None
  
  cursor = g.conn.execute("""SELECT DISTINCT borough from NYCLocation;""")
  boroughs = []
  for result in cursor: boroughs.append(result[0])
  cursor.close()
  cache['boroughs'] = boroughs

  cursor = g.conn.execute("""SELECT DISTINCT neighborhood from NYCLocation;""")
  neighborhoods = []
  for result in cursor: neighborhoods.append(result[0])
  cursor.close()
  cache['neighborhoods'] = neighborhoods

  try:
    g.conn.close()
  except Exception as e:
    pass

  HOST, PORT = args.host, args.port
  print 'running on %s:%d' % (HOST, PORT)
  app.run(host=HOST, port=PORT, debug=args.debug, threaded=args.threaded)
