import json
import random
import string
from functools import wraps

import httplib2
import requests
from flask import Flask, render_template, session as flask_session, flash
from flask import request, url_for, redirect, make_response, jsonify, abort
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError

import application_vm
import catalog_repository

app = Flask(__name__, template_folder='parts')
app.secret_key = 'somesecretkey'

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web'][
    'client_id']
APPLICATION_NAME = "Catalog App"


def is_authorized(func):
    """"""
    @wraps(func)
    def authorization(*args, **kwargs):
        if 'access_token' not in flask_session:
            return redirect(url_for('login'))

        r_json = request.get_json()
        r_json_category = r_json['category'] \
            if r_json is not None and 'category' is r_json \
            else None

        category = kwargs.get('category') or request.args.get('category') \
                   or r_json_category

        if category is not None:
            flask_session[
                'authorized'] = catalog_repository.validate_category_user(
                category=category, user_id=flask_session['user_id'])

        response = func(*args, **kwargs)
        if 'authorized' in flask_session:
            del flask_session['authorized']
        return response

    return authorization


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != flask_session['state']:
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

    stored_access_token = flask_session.get('access_token')
    stored_gplus_id = flask_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        dumps = json.dumps('Current user is already connected.')
        response = make_response(dumps, 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    flask_session['access_token'] = credentials.access_token
    flask_session['gplus_id'] = gplus_id
    flask_session['user_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    flask_session['username'] = data['name']
    flask_session['picture'] = data['picture']
    flask_session['email'] = data['email']

    catalog_repository.update_user(flask_session['user_id'])

    output = ''
    output += '<h1>Welcome, '
    output += flask_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += flask_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;' \
              '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % flask_session['username'])
    print "done!"
    return output

    # DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/api/catalog/gdisconnect', methods=['POST'])
def gdisconnect():
    access_token = flask_session['access_token']
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print flask_session['username']
    if access_token is None:
        print 'Access Token is None'
        dumps = json.dumps('Current user not connected.')
        response = make_response(dumps, 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % flask_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del flask_session['access_token']
        del flask_session['gplus_id']
        del flask_session['user_id']
        del flask_session['username']
        del flask_session['email']
        del flask_session['picture']
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
    flask_session['state'] = state
    return render_template('login.html', STATE=state, CLIENT_ID=CLIENT_ID)


@app.route("/")
@app.route("/catalog")
def catalog_view():
    return render_template('catalog_home.html',
                           categories=application_vm.categories(),
                           items=application_vm.category_list('Latest Items'),
                           category='Latest Items',
                           session=flask_session)


@app.route("/catalog/<string:category>/Items")
@is_authorized
def category_list_view(category):
    return render_template('catalog_home.html',
                           categories=application_vm.categories(),
                           items=application_vm.category_list(category),
                           category=category,
                           session=flask_session)


@app.route("/catalog/<string:category>/<string:item_name>")
@is_authorized
def category_item_view(category, item_name):
    return render_template('category_item.html',
                           item=application_vm.category_item(category,
                                                             item_name),
                           category=category,
                           session=flask_session)


@app.route("/catalog/add/<string:category>")
@is_authorized
def category_item_add_view(category):
    return render_template('category_item_add.html',
                           category=category,
                           session=flask_session)


@app.route("/catalog/add")
@is_authorized
def category_category_add_view():
    return render_template('category_add.html', session=flask_session)


@app.route("/catalog/edit/<string:category>/<string:item>")
@is_authorized
def category_category_edit_view(category, item):
    return render_template('category_item_edit.html',
                           item=application_vm.category_item(category, item),
                           session=flask_session)


@app.route("/api/catalog")
def categories():
    return jsonify(application_vm.categories())


@app.route("/api/catalog/<string:category>")
def category_list(category):
    return jsonify(application_vm.category_list(category))


@app.route("/api/catalog/add", methods=["POST"])
@is_authorized
def category_add():
    r_json = request.get_json()
    application_vm.category_add(category_name=r_json['category_name'],
                                session=flask_session)

    return jsonify("Success")


@app.route("/api/catalog/add/<string:category>", methods=["POST"])
@is_authorized
def category_add_item(category):
    r_json = request.get_json()
    if r_json['category'] != category:
        abort(400)

    if not flask_session['authorized']:
        abort(403)

    application_vm.category_add_item(category=r_json['category'],
                                     name=r_json['name'],
                                     description=r_json['description'])

    return jsonify("Success")


@app.route("/api/catalog/delete/<string:category>/<string:item>",
           methods=["DELETE"])
@is_authorized
def category_delete_item(category, item):
    if not flask_session['authorized']:
        abort(403)

    application_vm.category_delete_item(category=category, item=item)

    return jsonify("Success")


@app.route("/api/catalog/edit/<string:category>",
           methods=["POST"])
@is_authorized
def category_edit_item(category):
    r_json = request.get_json()
    if r_json['category'] != category:
        abort(400)

    if not flask_session['authorized']:
        abort(403)

    application_vm.category_edit_item(category=category,
                                      item=r_json['name'],
                                      description=r_json['description'])

    return jsonify("Success")


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug="true")
    # app.run(port=8888, debug="true")
