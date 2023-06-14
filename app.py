from flask import Flask, render_template, session, request, redirect, url_for
from database import engine
from sqlalchemy import text
import re
from database import load_user_details, authenticate_user, load_user_byname_byemail, load_all_users_byorg, load_user, delete_user_byid, edit_user_byid
#from flask_fontawesome import FontAwesome

app = Flask(__name__)
#fa = FontAwesome(app)

app.secret_key = "your secret key"


@app.route('/')
@app.route('/login', methods=["GET", "POST"])
def login():
  message = ''
  role = 'U'
  if (request.method == 'POST' and "username" in request.form
      and "password" in request.form):
    username = request.form["username"]
    password = request.form["password"]
    result = authenticate_user(username, password)
    if "Login successful" in result:
      session['user_id'] = result[1]
      session['username'] = username
      session['role'] = result[2]
      session['org_id'] = result[3]
      # role = result[1]
      return render_template('index.html', message='Login Success', role=role)
    else:
      message = 'Incorrect details were entered'
  return render_template('login.html', message=message)


@app.route("/index")
def index():
  return render_template("index.html")


@app.route("/getstarted")
def getStarted():
  return render_template("get_started.html")


@app.route("/addusers", methods=["GET", "POST"])
def add_users():
  message = ""
  if (request.method == "POST" and "username" in request.form
      and "email" in request.form and "password" in request.form
      and "role" in request.form):
    print("In add user if")
    username = request.form["username"]
    email = request.form["email"]
    password = request.form['password']
    role = request.form.get('role')
    if role == 'Poweruser':
      value = 'P'
    else:
      value = 'U'
    org_id = session['org_id']
    check_exist = load_user_byname_byemail(username, email)
    print(check_exist.all())
    if check_exist.rowcount > 0:
      message = "email or username already exist"
      print("MESSAGE ", message)
    elif not username or not email or not password or not role:
      message = "Please fill out the form!"
      print("MESSAGE ", message)
    elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
      message = "Invalid email address!"
      print("MESSAGE ", message)
    elif not re.match(r"^[a-zA-Z0-9]+$", username):
      message = "Username must contain only characters and numbers!"
      print("MESSAGE ", message)
    else:
      with engine.connect() as conn:
        query = text(
          "INSERT INTO user_details(username, password, email, role, org_id) VALUES (:username, :password, :email, :role, :org_id)"
        )
        result = conn.execute(
          query, {
            'username': username,
            'password': password,
            'email': email,
            'role': value,
            'org_id': org_id
          })
      message = "User added successfully"
      print("MESSAGE ", message)
  else:
    message = ""
    print("MESSAGE ", message)
  return render_template('add_users.html', message=message)


@app.route("/allusers")
def all_users():
  org_id = session['org_id']
  users = load_all_users_byorg(org_id)
  print(users)
  return render_template('view_all_users.html', users=users, i=0)


# @app.route("/allusers/<id>")
# def show_user(id):
#   user = load_user(id)
#   return render_template('')


@app.route('/delete/<int:user_id>')
def delete_user(user_id):
  # Delete the user with the given user_id from the userdetails list
  userdetails = delete_user_byid(user_id)
  # userdetails = [user for user in userdetails if user['user_id'] != user_id]
  return userdetails


@app.route('/edit/<int:user_id>')
def edit_user(user_id):
  user = load_user(user_id)
  print("USER ------- ", user)
  # Redirect to the edit user page for the given user_id
  return render_template('edit_user.html', user=user)


@app.route('/update/<int:user_id>', methods=['GET', 'POST'])
def update_user(user_id):

  if request.method == 'POST':

    username = request.form['username']
    email = request.form["email"]
    password = request.form['password']
    role = request.form.get('role')
    if role == 'Poweruser':
      value = 'P'
    else:
      value = 'U'

    update_details = edit_user_byid(user_id, username, password, email, role)
    print(update_details)
    if (session['user_id'] == user_id):
      print("-----------IN SESSION USER ID --------")
      session['role'] = role
    return redirect(url_for('index', message=update_details))
  org_id = session['org_id']
  users = load_all_users_byorg(org_id)
  return render_template('view_all_users.html', user=users, i=0)


@app.route("/logout")
def logout():
  session.pop("loggedin", None)
  session.pop("id", None)
  session.pop("username", None)
  session.pop("role", None)
  session.pop("org_id", None)

  return redirect(url_for("login"))  # change this to logout success page.


if __name__ == "__main__":
  app.run(host="0.0.0.0", debug=True)
