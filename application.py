import json
import random
import string

import httplib2
import requests
from flask import Flask, render_template, session as login_session, request
from flask import abort, flash, redirect, jsonify, make_response
from oauth2client.client import FlowExchangeError
from oauth2client.client import flow_from_clientsecrets

import catalog_repository

app = Flask(__name__, template_folder="parts")
app.secret_key = 'somesecret'

CLIENT_ID = json.loads(open('client_secrets.json', 'r')
                       .read())['web']['client_id']
APPLICATION_NAME = "Catalog App"


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        dumps = json.dumps('Current user is already connected.')
        response = make_response(dumps, 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;' \
              '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

    # DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/api/catalog/gdisconnect', methods=['POST'])
def gdisconnect():
    access_token = login_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    if access_token is None:
        print 'Access Token is None'
        dumps = json.dumps('Current user not connected.')
        response = make_response(dumps, 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        json_dumps = json.dumps('Failed to revoke token for given user.', 400)
        response = make_response(json_dumps)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route("/catalog/login")
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route("/")
@app.route("/catalog")
def catalog_view():
    return render_template('catalog_home.html',
                           categories=categories(),
                           items=category_list('Latest Items'),
                           category='Latest Items',
                           session=login_session)


@app.route("/catalog/<string:category>/Items")
def category_list_view(category):
    return render_template('catalog_home.html',
                           categories=categories(),
                           items=category_list(category),
                           category=category,
                           session=login_session)


@app.route("/catalog/<string:category>/<string:item>")
def category_item_view(category, item):
    return render_template('catalog_item.html',
                           item=category_item(category, item),
                           category=category,
                           session=login_session)


@app.route("/catalog/add")
def category_item_add_view():
    if 'username' not in login_session:
        return redirect('/catalog/login')

    return render_template('catalog_item_add.html',
                           categories=categories(),
                           session=login_session)


@app.route("/catalog/edit")
def category_item_edit_view():
    if 'username' not in login_session:
        return redirect('/catalog/login')

    category = request.args.get('category')
    name = request.args.get('name')
    return render_template('catalog_item_edit.html',
                           item=category_item(category, name),
                           categories=categories(),
                           session=login_session)


@app.route("/catalog/delete")
def category_item_delete_view():
    if 'username' not in login_session:
        return redirect('/catalog/login')

    category = request.args.get('category')
    name = request.args.get('name')
    return render_template('catalog_item_delete.html',
                           item=category_item(category, name),
                           session=login_session)


@app.route("/api/catalog/add", methods=['POST'])
def category_item_add():
    if 'username' not in login_session:
        abort(401)

    title = request.form['title']
    description = request.form['description']
    category = request.form['category']
    catalog_repository.add_item(name=title,
                                description=description,
                                category=category)
    return redirect('/catalog/%s/Items' % category)


@app.route("/api/catalog/edit", methods=['POST'])
def category_item_edit():
    if 'username' not in login_session:
        abort(401)

    r_json = request.get_json()
    catalog_repository.update_item(name=r_json.get('title'),
                                   description=r_json.get('description'),
                                   category=r_json.get('category'))
    return jsonify('Success')


@app.route("/api/catalog/delete", methods=['DELETE'])
def category_item_delete():
    if 'username' not in login_session:
        abort(401)

    title = request.args.get('title')
    category = request.args.get('category')
    catalog_repository.delete_item(name=title, category=category)
    return jsonify('Success')


@app.route("/api/catalog")
def categories():
    return catalog_repository.get_all_categories()


@app.route("/api/catalog/<string:category>")
def category_list(category):
    return catalog_repository.get_all_category_items() \
        if category == 'Latest Items' \
        else catalog_repository.get_category_items(category)


@app.route("/api/catalog/<string:category>/<string:item_name>")
def category_item(category, item_name):
    return catalog_repository.get_category_item(category, item_name)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug="true")
