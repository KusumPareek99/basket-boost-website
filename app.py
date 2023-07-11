from flask import Flask, render_template, session, request, redirect, url_for
from database import engine
from sqlalchemy import text
import re
import os
from database import authenticate_user, load_user_byname_byemail, load_all_users_byorg, load_user, delete_user_byid, edit_user_byid, upload_dbfile, show_userdb, load_file, delete_file_byid
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
from matplotlib import pyplot as plt
#from flask_fontawesome import FontAwesome

app = Flask(__name__)
#fa = FontAwesome(app)

app.secret_key = "your secret key"

# Set the temporary upload folder
UPLOAD_FOLDER = 'static/mydb'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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
  return render_template('view_all_users.html', users=users)


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
  return render_template('view_all_users.html', user=users)


# Handle the file upload request
@app.route('/upload', methods=['POST'])
def upload_file():
  # Check if a file was uploaded
  if 'file' not in request.files:
    return render_template('get_started.html', error='No file selected.')

  file = request.files['file']

  # Check if the file is empty
  if file.filename == '':
    return render_template('get_started.html', error='No file selected.')

  # Save the uploaded file to a temporary location
  filename = file.filename
  file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
  file.save(file_path)

  user_id = session['user_id']

  # Save the file to the MySQL database
  try:

    # Read the file content
    with open(file_path, 'r') as f:
      file_content = f.read()

    # Insert the file content into the database table
    message = upload_dbfile(filename, file_content, user_id)

    datasets = show_userdb(user_id)
    return render_template('all_datasets.html',
                           message=message,
                           datasets=datasets)

  except Exception as error:
    return render_template(
      'get_started.html',
      error='Failed to upload file. Error: {}'.format(error))

  finally:
    # Remove the temporary file
    os.remove(file_path)


@app.route('/deletefile/<int:file_id>')
def delete_file(file_id):
  # Delete the file with the given file_id from the filedetails list
  print("IN DELETE FILES")
  user_id = session['user_id']
  datasets = show_userdb(user_id)
  filedetails = delete_file_byid(file_id)

  # return render_template('all_datasets.html', message = filedetails,datasets = datasets)
  return redirect(
    url_for('alldatasets', datasets=datasets, message=filedetails))


@app.route('/alldatasets', methods=['GET', 'POST'])
def alldatasets():
  user_id = session['user_id']
  datasets = show_userdb(user_id)
  return render_template('all_datasets.html', datasets=datasets)


@app.route('/preprocess/<int:file_id>', methods=['GET', 'POST'])
def preprocess(file_id):
  file = load_file(file_id)
  # print('file: ', file['file_name'] )
  # Get the file content from the database
  file_content = file['file_data']
  # Create a temporary file path to save the content
  temp_file_path = f"static/mydb/{file['file_name']}"
  with open(temp_file_path, 'wb') as temp_file:
    temp_file.write(file_content)
  # Read the temporary file into a DataFrame
  df = pd.read_csv(
    temp_file_path)  # todo: Adjust this line if using Excel file
  # Perform data cleaning
  # Remove duplicates
  df.drop_duplicates(inplace=True)

  # Handle missing values
  df.fillna('NA', inplace=True)

  # Change column data types to string
  df = df.astype(str)

  # Group items by transaction and create a new DataFrame with binary encoding
  # to do: change Member_number and itemDescription to dynamic column name
  transaction_data = df.groupby('Member_number')['itemDescription'].apply(
    list).reset_index(name='items')

  # Perform one-hot encoding to create a binary matrix of items
  one_hot_encoded = transaction_data['items'].str.join('|').str.get_dummies()

  frequent_itemsets = apriori(one_hot_encoded,
                              min_support=0.1,
                              use_colnames=True)
  rules = association_rules(frequent_itemsets,
                            metric='confidence',
                            min_threshold=0.5)

  sorted_rules = rules.sort_values(by='confidence', ascending=False)
  top_rules = sorted_rules.head(5)
  myrule = []
  for idx, rule in top_rules.iterrows():
    antecedents = ', '.join(rule['antecedents'])
    consequents = ', '.join(rule['consequents'])
    confidence = rule['confidence']
    support = rule['support']
    myrule.append(
      f"Antecedents: {antecedents}  Consequents: {consequents} Confidence: {confidence:.2f}  Support: {support:.2f}"
    )
    print(f"Rule #{idx+1}:")
    print(f"Antecedents: {antecedents}")
    print(f"Consequents: {consequents}")
    print(f"Confidence: {confidence:.2f}")
    print(f"Support: {support:.2f}")
    print("---")

  return render_template('preprocess_data.html', file=file, myrules=myrule)



# function to get the column names of uploaded csv file
def getColumns(df):
  columns = df.columns.tolist()
  return columns


# function to remove spaces in the specified column of the dataframe
def removeSpaces(df, column):
  df[column] = df[column].str.strip()
  return df


# function to remove duplicates in the specified column of the dataframe
def removeDuplicates(df, column):
  df[column] = df[column].drop_duplicates()
  return df


# function to remove null values in the specified column of the dataframe
def removeNull(df, column):
  df[column] = df[column].dropna()
  return df


# function to remove special characters in the specified column of the dataframe
def removeSpecialCharacters(df, column):
  df[column] = df[column].str.replace('[^\w\s]', '')
  return df


# function to convert the specified column to string type
def convertToString(df, column):
  df[column] = df[column].astype(str)
  return df


# function to perform data cleaning
def dataCleaning(df, column):
  df = convertToString(df, column)
  df = removeSpaces(df, column)
  # df = removeDuplicates(df, column)
  # df = removeNull(df, column)
  # df = removeSpecialCharacters(df, column)
  return df


# function to perform one hot encoding
def oneHotEncoding(df):
  te = TransactionEncoder()
  te_ary = te.fit(df).transform(df)
  df = pd.DataFrame(te_ary, columns=te.columns_)
  return df


# function to perform apriori algorithm
def aprioriAlgorithm(df):
  frequent_itemsets = apriori(df, min_support=0.01, use_colnames=True)
  return frequent_itemsets


# function to perform association rules
def associationRules(frequent_itemsets):
  rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1)
  return rules


# function to perform data analysis
def dataAnalysis(df):
  #df = dataCleaning(df) ---- do data cleaning separately
  df = oneHotEncoding(df)
  frequent_itemsets = aprioriAlgorithm(df)
  rules = associationRules(frequent_itemsets)
  return rules


# function to display the results
def displayResults(rules):
  rules = rules.sort_values(['confidence', 'lift'], ascending=[False, False])
  print(rules.head(10))
  return rules.head(10)


# function to perform data visualization
def dataVisualization(rules):
  fig = plt.figure(figsize=(10, 10))
  ax = fig.add_subplot(111)
  scatter = ax.scatter(rules['support'],
                       rules['confidence'],
                       c=rules['lift'],
                       cmap='gray')
  plt.colorbar(scatter)
  plt.xlabel('support')
  plt.ylabel('confidence')
  plt.show()


# function to perform data analysis and visualization
def dataAnalysisAndVisualization(df):
  rules = dataAnalysis(df)
  displayResults(rules)
  dataVisualization(rules)


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
