
from flask import *
import os
import json

# Create Application Object
app = Flask(__name__)
app.secret_key = 'dhwbiud7238eygf7843gf7r584e'


def invalid_request(**kwargs):
    """
    Function to return response object if request is invalid
    :param kwargs: Data to return with response
    :return: Response with data and response status code 501
    """
    return json.dumps(kwargs), 501, {'ContentType': 'application/json'}


def success(**kwargs):
    """
    Function to return response object if request is successfully completed
    :param kwargs: Data to return with response
    :return: Response with data and response status code 200
    """
    return json.dumps(kwargs), 200, {'ContentType': 'application/json'}


def update_movie_data(movie_data):
    """
    Function to update Movies data
    :param movie_data: New data of movies to override previous
    :return: None
    """
    with open(os.path.join('database', 'MovieScreens.JSON'), 'w+') as database:
        database.write(json.dumps(movie_data))


def read_movie_data():
    """
    Function to read Movie data
    :return: Movies data in the form of JSON object
    """
    with open(os.path.join('database', 'MovieScreens.JSON'), 'r') as database:
        return json.loads(database.read())


def read_user_data():
    """
    Function to read User's data
    :return: User's data in the form of JSON object
    """
    with open(os.path.join('database', 'users.JSON'), 'r') as database:
        return json.loads(database.read())


def update_user_data(user_data):
    """
    Function to update User's data
    :param user_data: New data of Users as JSON object to override previous
    :return: None
    """
    with open(os.path.join('database', 'users.JSON'), 'w+') as database:
        database.write(json.dumps(user_data))


@app.route('/')
def show_homepage():
    """
    Function to Render Homepage
    :return: Render's the index.html template
    """
    if 'name' in session:
        return render_template('index.html', session=True), 200
    return render_template('index.html', session=False), 200


@app.route('/privacy_policy')
def show_privacy():
    """
    Function to Render Privacy Policies Page
    :return: Render's the template privacy_policy.html
    """
    return render_template('privacy_policy.html'), 200


@app.route('/login', methods=['POST'])
def login():
    """
    Accepts the data of the user coming from post method
    Login's the user if exist in the database or else Creates new user in the database
    :return: Function success
    """
    user_data = request.get_json()
    try:
        users = read_user_data()
    except Exception as e:
        print(e)
        users = list()
        users.append(user_data)
        update_user_data(users)
        session['name'] = user_data['name']
        session['email'] = user_data['email']
        return success(success=True)
    for user in users:
        if user['name'] == user_data['name'] and user['email'] == user_data['email']:
            break
    else:
        users.append(user_data)
        update_user_data(users)

    session['name'] = user_data['name']
    session['email'] = user_data['email']
    return success(success=True)


@app.route('/logout')
def logout():
    """
    Logs out the user if exist in the session
    :return: Response object to redirect to homepage
    """
    session.pop('name', None)
    session.pop('email', None)
    return redirect(url_for('show_homepage'))


@app.route('/getmovieslist')
def getmovieslist():
    """
    Returns the Response object with movies data
    """
    return success(success=True, movies=read_movie_data())


@app.route('/screens', methods=['POST'])
def add_movie_screen():
    try:
        movie_data = read_movie_data()
    except Exception as e:
        print(e)
        movie_data = list()

    data = request.get_json()

    for movie in movie_data:
        if movie['name'] == data['name']:
            for seat in data['seatInfo']:
                movie['seatInfo'][seat] = data['seatInfo'][seat]
            break
    else:
        movie_data.append(data)

    update_movie_data(movie_data)
    return success(success=True)


@app.route('/screens/<screen_name>/reserve', methods=['POST'])
def reserve_tickets(screen_name):
    try:
        movie_data = read_movie_data()
    except Exception as e:
        print(e)
        return invalid_request(success=False)

    to_reserve = request.get_json()

    for movie in movie_data:
        if movie['name'] == screen_name:
            if not set(to_reserve["seats"].keys()).issubset(set(movie['seatInfo'].keys())):
                return invalid_request(success=False)
            for seat in to_reserve['seats']:
                if set(to_reserve['seats'][seat]).intersection(set(movie['seatInfo'][seat]['aisleSeats'])) \
                        or not set(to_reserve['seats'][seat]) \
                        .issubset(set(list(range(movie['seatInfo'][seat]['numberOfSeats'])))):
                    return invalid_request(success=False)
                movie['seatInfo'][seat]['aisleSeats'] += to_reserve['seats'][seat]
            update_movie_data(movie_data)
            return success(success=True)
    else:
        return invalid_request(success=False)


@app.route('/screens/<screen_name>/seats', methods=['GET'])
def available_seats(screen_name):
    try:
        movie_data = read_movie_data()
        for movie in movie_data:
            if movie['name'] == screen_name:
                seat_info = movie['seatInfo']
                break
        else:
            return invalid_request(success=False, seats=dict())
    except Exception as e:
        print(e)
        return invalid_request(success=False, seats=dict())

    seats = dict()

    try:
        status = request.args['status']
        if status == 'unreserved':
            for seat in seat_info:
                seats[seat] = [i for i in range(seat_info[seat]['numberOfSeats']) if
                               i not in seat_info[seat]['aisleSeats']]
            return success(seats=seats)
        else:
            return invalid_request(success=False, seats=dict())
    except KeyError:
        try:
            num_seats, choice_row, choice_seat = int(request.args['numSeats']), request.args['choice'][:1], \
                                                 int(request.args['choice'][1:])
            try:
                aisle_seats = set(seat_info[choice_row]['aisleSeats'])
            except KeyError:
                return invalid_request(success=False, availableSeats={choice_row: []})

            for i in range(choice_seat - num_seats + 1, choice_seat + 1):
                for j in range(i, i + num_seats):
                    if j in aisle_seats or j not in range(seat_info[choice_row]['numberOfSeats']):
                        break
                else:
                    return success(availableSeats={choice_row: list(range(i, i + num_seats))})
            return invalid_request(success=False, availableSeats={choice_row: []})
        except KeyError:
            return render_template('404.html'), 404
        except ValueError:
            return invalid_request(success=False, seats=dict())


@app.errorhandler(404)
def page_not_found(e):
    """
    Returns the Response object with http status code 404 and renders the 404.html template
    """
    print(e)
    return render_template('404.html'), 404


if __name__ == '__main__':

    # Run application on port 9090 with providing access on remote machines
    app.run(host='0.0.0.0', port=9090, debug=True)
