from flask import Flask, render_template, request, redirect, \
    url_for, jsonify, flash, make_response
from flask import session as login_session
from sqlalchemy import create_engine, asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, Book, User
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import os
import random
import string
import logging


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "My Library Application"

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)


@app.route('/login')
def show_login():
    """
    Endpoint for the login page.
    """
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, client_id=CLIENT_ID)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Endpoint for connecting with a Google Plus account, and adding the user
    to the database (if it doesn't exist).
    """
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

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        logging.warning("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    logging.info("Result is:")
    logging.info(data)

    login_session['username'] = data['name']
    login_session['email'] = data['email']

    # See if user exists, if it doesn't make a new one
    user_id = get_user_id(data["email"])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h4>Welcome, '
    output += login_session['username']
    output += '!</h4>'
    flash("You are now logged in as %s" % login_session['username'], "success")
    logging.info("done!")
    return output


@app.route('/gdisconnect')
def gdisconnect():
    """
    Endpoint for disconnecting from the Google Plus session.
    """
    access_token = login_session.get('access_token')
    if access_token is None:
        logging.info('Access Token is None')
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    logging.info('In gdisconnect, access token: %s', access_token)
    logging.info('User name: %s', login_session['username'])
    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
           % login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    logging.info('Result is: ')
    logging.info(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        flash('You successfully logged out', "success")
    else:
        flash('Failed to revoke token for given user', "danger")
    return redirect(url_for('show_all_categories_and_books'))


@app.route('/')
@app.route('/category/')
def show_all_categories_and_books():
    """
    Endpoint for rendering the main page which shows all
    categories and books.
    """
    session = DBSession()
    categories = session.query(Category).order_by(asc(Category.name))
    books = session.query(Book, Category, User).join(
        Book.category, Book.user).all()
    session.close()
    logged_in = ('username' in login_session)
    user_id = login_session['user_id'] if logged_in else None
    return render_template('main.html', categories=categories,
                           selected_category=None, books=books,
                           logged_in=logged_in, current_user_id=user_id)


@app.route('/category/<int:category_id>/')
def show_books_by_category(category_id):
    """
    Endpoint for rendering the main page with the books
    filtered by category.

    Parameter:
    category_id: ID of the category
    """
    session = DBSession()
    categories = session.query(Category).all()
    try:
        category = session.query(Category).filter_by(id=category_id).one()
        books = session.query(Book, Category, User).join(
            Book.category, Book.user).filter(
            Book.category_id == category_id).all()
    except SQLAlchemyError:
        return redirect(url_for('show_all_categories_and_books'))
    session.close()
    logged_in = ('username' in login_session)
    user_id = login_session['user_id'] if logged_in else None
    return render_template('main.html', categories=categories,
                           selected_category=category, books=books,
                           logged_in=logged_in, current_user_id=user_id)


@app.route('/book/<int:book_id>/edit', methods=['POST'])
def edit_book(book_id):
    """
    Endpoint for editing a book.

    Parameter:
    book_id: ID of the book
    """
    if 'username' not in login_session:
        return redirect('/login')
    session = DBSession()
    book_to_edit = session.query(Book).filter_by(id=book_id).one()
    if book_to_edit.user_id != login_session['user_id']:
        flash("You are not authorized to edit this book", "warning")
        return redirect(url_for('show_all_categories_and_books'))
    if request.form['title']:
        book_to_edit.title = request.form['title']
    if request.form['author']:
        book_to_edit.author = request.form['author']
    if request.form['category']:
        book_to_edit.category_id = int(request.form['category'])
    if request.form['description']:
        book_to_edit.description = request.form['description']
    session.add(book_to_edit)
    session.commit()
    session.close()
    flash("Book successfully updated", "success")
    return redirect(url_for('show_all_categories_and_books'))


@app.route('/book/new', methods=['POST'])
def add_book():
    """
    Endpoint for adding a book.
    """
    if 'username' not in login_session:
        return redirect('/login')
    book_to_add = Book(title=request.form['title'],
                       description=request.form['description'],
                       author=request.form['author'],
                       category_id=request.form['category'],
                       user_id=login_session['user_id'])
    session = DBSession()
    session.add(book_to_add)
    session.commit()
    session.close()
    flash("Book successfully added", "success")
    return redirect(url_for('show_all_categories_and_books'))


@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    """
    Endpoint for deleting a book.

    Parameter:
    book_id: ID of the book
    """
    if 'username' not in login_session:
        return redirect('/login')
    session = DBSession()
    book_to_delete = session.query(Book).filter_by(id=book_id).one()
    if book_to_delete.user_id != login_session['user_id']:
        flash("You are not authorized to delete this book", "warning")
        return redirect(url_for('show_all_categories_and_books'))
    session.delete(book_to_delete)
    session.commit()
    session.close()
    flash("Book successfully removed", "success")
    return redirect(url_for('show_all_categories_and_books'))


@app.route('/categories/JSON')
def get_categories_json():
    """
    Endpoint for retrieving the category names and IDs in json format.
    """
    session = DBSession()
    categories = session.query(Category).all()
    session.close()
    return jsonify(Categories=[c.serialize for c in categories])


@app.route('/category/<int:category_id>/JSON')
def get_books_by_category_json(category_id):
    """
    Endpoint for retrieving information on books
    in a category in json format.

    Parameter:
    category_id: ID of the category
    """
    session = DBSession()
    books = session.query(Book).filter_by(category_id=category_id)
    session.close()
    return jsonify(Books=[b.serialize for b in books])


@app.route('/book/<int:book_id>/JSON')
def get_book_json(book_id):
    """
    Endpoint for retrieving information on a book in json format.

    Parameter:
    book_id: ID of the book
    """
    session = DBSession()
    book = session.query(Book).filter_by(id=book_id).one()
    return jsonify(Book=book.serialize)


def get_user_id(email):
    """
    Function for retrieving the user ID from the database.

    Parameter:
    email: email address of the user
    """
    try:
        session = DBSession()
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except SQLAlchemyError:
        return None


def get_user_info(user_id):
    """
    Function for retrieving a user's information from the database.

    Parameter:
    user_id: ID of the user in the database
    """
    session = DBSession()
    user = session.query(User).filter_by(id=user_id).one()
    return user


def create_user(login_session):
    """
    Function for adding a user to the database.

    Parameter:
    login_session: login session for the user
    """
    newUser = User(name=login_session['username'],
                   email=login_session['email'])
    session = DBSession()
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
