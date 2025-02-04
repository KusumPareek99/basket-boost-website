from flask import Flask, render_template, session, request, redirect, url_for, jsonify
from database import engine, authenticate_user, load_user_byname_byemail, load_all_users_byorg, load_user, delete_user_byid, edit_user_byid, upload_dbfile, show_userdb, load_file, delete_file_byid, search_dbfiles, search_user
import re
import os
import json
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
import plotly.graph_objs as go

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Set the temporary upload folder
UPLOAD_FOLDER = 'static/mydb'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
@app.route('/login', methods=["GET", "POST"])
def login():
    message = ''
    role = 'U'
    if request.method == 'POST' and "username" in request.form and "password" in request.form:
        username = request.form["username"]
        password = request.form["password"]
        result = authenticate_user(username, password)
        if "Login successful" in result:
            session['user_id'] = result[1]
            session['username'] = username
            session['role'] = result[2]
            session['org_id'] = result[3]
            return redirect(url_for('index', message='Login Success', role=role))
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
    if request.method == "POST" and "username" in request.form and "email" in request.form and "password" in request.form and "role" in request.form:
        username = request.form["username"]
        email = request.form["email"]
        password = request.form['password']
        role = request.form.get('role')
        value = 'P' if role == 'Poweruser' else 'U'
        org_id = session['org_id']
        check_exist = load_user_byname_byemail(username, email)
        if check_exist.rowcount > 0:
            message = "email or username already exist"
        elif not username or not email or not password or not role:
            message = "Please fill out the form!"
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            message = "Invalid email address!"
        elif not re.match(r"^[a-zA-Z0-9]+$", username):
            message = "Username must contain only characters and numbers!"
        else:
            with engine.connect() as conn:
                query = text(
                    "INSERT INTO user_details(username, password, email, role, org_id) VALUES (:username, :password, :email, :role, :org_id)"
                )
                conn.execute(query, {
                    'username': username,
                    'password': password,
                    'email': email,
                    'role': value,
                    'org_id': org_id
                })
            message = "User added successfully"
    return render_template('add_users.html', message=message)

@app.route("/allusers")
def all_users():
    org_id = session['org_id']
    users = load_all_users_byorg(org_id)
    return render_template('view_all_users.html', users=users)

@app.route('/delete/<int:user_id>')
def delete_user(user_id):
    userdetails = delete_user_byid(user_id)
    return userdetails

@app.route('/edit/<int:user_id>')
def edit_user(user_id):
    user = load_user(user_id)
    return render_template('edit_user.html', user=user)

@app.route('/update/<int:user_id>', methods=['GET', 'POST'])
def update_user(user_id):
    if request.method == 'POST':
        username = request.form['username']
        email = request.form["email"]
        password = request.form['password']
        role = request.form.get('role')
        value = 'P' if role == 'Poweruser' else 'U'
        update_details = edit_user_byid(user_id, username, password, email, role)
        if session['user_id'] == user_id:
            session['role'] = role
        return redirect(url_for('index', message=update_details))
    org_id = session['org_id']
    users = load_all_users_byorg(org_id)
    return render_template('view_all_users.html', user=users)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return render_template('get_started.html', error='No file selected.')

    file = request.files['file']
    if file.filename == '':
        return render_template('get_started.html', error='No file selected.')

    filename = file.filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    user_id = session['user_id']
    print("FILE path : ",file_path)

    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
        message = upload_dbfile(filename, file_content, user_id)
        datasets = show_userdb(user_id)
        return redirect(url_for('alldatasets', message=message, datasets=datasets))
    except Exception as error:
        return render_template('get_started.html', error=f'Failed to upload file. Error: {error}')
    finally:
        print("Removing file")
        os.remove(file_path)

@app.route('/deletefile/<int:file_id>')
def delete_file(file_id):
    user_id = session['user_id']
    datasets = show_userdb(user_id)
    filedetails = delete_file_byid(file_id)
    return redirect(url_for('alldatasets', datasets=datasets, message=filedetails))

@app.route('/alldatasets', methods=['GET', 'POST'])
def alldatasets():
    user_id = session['user_id']
    datasets = show_userdb(user_id)
    column = {dataset['file_name']: getColumns(dataset['file_id']) for dataset in datasets}
    return render_template('all_datasets.html', datasets=datasets, column=column, current_file=None)

@app.route('/getColumns/<int:file_id>', methods=['GET', 'POST'])
def getColumns(file_id):
    file = load_file(file_id)
    file_content = file['file_data']
    temp_file_path = f"static/mydb/{file['file_name']}"
    with open(temp_file_path, 'wb') as temp_file:
        temp_file.write(file_content)
    df = pd.read_csv(temp_file_path)
    columns = df.columns.tolist()
    return jsonify({'file_name': file['file_name'], 'columns': columns})

@app.route('/getRules/<int:file_id>', methods=['GET', 'POST'])
def getRules(file_id):
    transactionID = request.form.get('transactionID')
    itemsColumn = request.form.get('itemsColumn')

    try:
        file = load_file(file_id)
        file_content = file['file_data']
        temp_file_path = f"static/mydb/{file['file_name']}"
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(file_content)
        df = pd.read_csv(temp_file_path)
        df.drop_duplicates(inplace=True)
        df.fillna('NA', inplace=True)
        df = df.astype(str)
        transaction_data = df.groupby(transactionID)[itemsColumn].apply(list).reset_index(name='items')
        one_hot_encoded = transaction_data['items'].str.join('|').str.get_dummies()
        frequent_itemsets = apriori(one_hot_encoded, min_support=0.1, use_colnames=True)
        rules = association_rules(frequent_itemsets, metric='confidence', min_threshold=0.5)
        sorted_rules = rules.sort_values(by='confidence', ascending=False)
        top_rules = sorted_rules.head(10)
        myrule = [{'antecedents': ', '.join(rule['antecedents']), 'consequents': ', '.join(rule['consequents']),
                   'confidence': round(rule['confidence'], 3), 'support': round(rule['support'], 3)} for _, rule in top_rules.iterrows()]
        return jsonify({'rules': myrule})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/displayRules')
def displayRules():
    rules = request.args.get('rules')
    rules = json.loads(rules)
    return render_template('display_rules.html', rules=rules)

@app.route('/visualize', methods=['POST'])
def dataVisualization():
    rules = request.form['allrules']
    rules = rules.replace("'", '"')
    rules = json.loads(rules)
    itemsets = [rule['consequents'] + ', ' + rule['antecedents'] for rule in rules]
    support = [rule['support'] for rule in rules]
    data = [go.Bar(x=support, y=itemsets, orientation='h')]
    layout = go.Layout(title='Insights Visualization', xaxis=dict(title='Support'), yaxis=dict(title='Frequent Itemsets'), barmode='group')
    fig = go.Figure(data=data, layout=layout)
    chart_json = fig.to_json()
    return render_template('visualize_insights.html', chart_json=chart_json)

@app.route('/search', methods=['GET', 'POST'])
def search():
    user_id = session['user_id']
    searchedtext = request.form.get('searchtext')
    if session['role'] == 'P':
        users = search_user(searchedtext, searchedtext)
        files = search_dbfiles(user_id, searchedtext)
        return render_template('search.html', users=users, files=files, searchedtext=searchedtext)
    else:
        files = search_dbfiles(user_id, searchedtext)
        return render_template('search.html', files=files, searchedtext=searchedtext)

@app.route("/logout")
def logout():
    session.pop("loggedin", None)
    session.pop("user_id", None)
    session.pop("username", None)
    session.pop("role", None)
    session.pop("org_id", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
