from flask import Flask, g, redirect, render_template, request, url_for

from create_db import connect_db, init_db

from contextlib import closing
import random
import sqlite3
from urllib2 import Request, urlopen, URLError
from urlparse import urlparse

# TODO: move config to separate file
app = Flask(__name__)
app.debug = True
app.reload = True
app.config.from_object(__name__)

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def retrieve_url(new_url, db):
    query = 'SELECT orig_url FROM urlmap WHERE short_url=:url'
    c = db.cursor()
    c.execute(query, {'url': new_url})
    result = c.fetchone()[0]
    # print("RESULT:", result)
    queryall = 'SELECT * FROM urlmap'
    c.execute(queryall)
    data = c.fetchall()
    print("DATA:", data)
    return result

def store_url(orig_url, short_url, db):
    db.cursor().execute("INSERT INTO urlmap VALUES (?, ?)",
                        (short_url, orig_url))
    db.commit()

def transform(length=10):
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyz')
        for _ in range(length))

def validate(url):
    error = None
    try:
        urlopen(url)
    except URLError, e:
        if hasattr(e, 'reason'):
            error = "Error: Failed to reach a server:"
        elif hasattr(e, 'code'):
            error = " ".join(("Error code:", e.code))

    return error

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/<short_url>')  #Dynamic URL
def retrieve(short_url):
    orig_url = retrieve_url(short_url, g.db)
    return redirect(orig_url)

@app.route('/forms', methods=['POST'])
def process_form():
    orig_url = request.form['url']
    # Make sure URL has header
    header = urlparse(orig_url).scheme
    if not header:
        orig_url = ''.join(('http://', orig_url))

    error = validate(orig_url)
    if error:
        return render_template('index.html', error=error)
    else:
        new_url = transform()
        store_url(orig_url, new_url, g.db)
        return new_url

if __name__ == '__main__':
    init_db()
    app.run('localhost', 5000)
