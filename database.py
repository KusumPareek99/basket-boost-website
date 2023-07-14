from sqlalchemy import create_engine, text
import os

connection_string = os.environ['DB_CONNECTION_STRING']

engine = create_engine(connection_string,
                       connect_args={"ssl": {
                         "ssl_ca": "/etc/ssl/cert.pem"
                       }})


def load_user_details():
  with engine.connect() as conn:
    result = conn.execute(text("select * from user_details"))

    result_all = result.all()

    user_details = []
    for row in result_all:
      user_details.append(row._asdict())
    return user_details


def authenticate_user(username, password):
  role = ''
  with engine.connect() as conn:
    query = text(
      "SELECT * FROM user_details WHERE username = :username AND password = :password"
    )
    result = conn.execute(query, {'username': username, 'password': password})
    result_all = result.all()

    user_details = []
    for row in result_all:
      user_details.append(row._asdict())

    if result.rowcount > 0:
      user_id = user_details[0]['user_id']
      role = user_details[0]['role']
      org_id = user_details[0]['org_id']
      return ("Login successful", user_id, role, org_id)
    else:
      return "Invalid username or password"


def load_user_byname_byemail(username, email):
  with engine.connect() as conn:
    query = text(
      "SELECT * FROM user_details WHERE username = :username OR email = :email"
    )
    result = conn.execute(query, {'username': username, 'email': email})
    return result


def load_all_users_byorg(org_id):
  with engine.connect() as conn:

    query = text("SELECT * FROM user_details WHERE org_id = :org_id")
    result = conn.execute(query, {'org_id': org_id})

    users = []

    for row in result.all():
      users.append(row._asdict())

  return users


def load_user(user_id):
  with engine.connect() as conn:

    query = text("SELECT * FROM user_details WHERE user_id = :user_id")
    result = conn.execute(query, {'user_id': user_id})

    rows = result.all()

  if len(rows) == 0:
    return None
  else:
    row = rows[0]
    print(row._asdict())
    return row._asdict()
  return row



def delete_user_byid(user_id):
  with engine.connect() as conn:
    query = text("DELETE FROM user_details WHERE user_id = :user_id")
    result = conn.execute(query, {'user_id': user_id})

    if result:
      return (f"{user_id} user id deleted successfully")
    else:
      return None


def edit_user_byid(user_id, username, password, email, role):
  with engine.connect() as conn:
    query = text(
      "UPDATE user_details SET username = :username, email = :email,password = :password,role = :role WHERE user_id = :user_id "
    )
    result = conn.execute(
      query, {
        'user_id': user_id,
        'username': username,
        'email': email,
        'password': password,
        'role': role
      })
    if result:
      return (f"{user_id} updated successfully")
    else:
      return None


def upload_dbfile(filename, filedata, userid):
  with engine.connect() as conn:
    query = text(
      "INSERT INTO db_files(file_name, file_data,user_id) VALUES (:filename, :filedata, :userid)"
    )
    result = conn.execute(query, {
      'filename': filename,
      'filedata': filedata,
      'userid': userid,
    })
    if result:
      print("FILE UPLOADED!!")
      return (f"Your file {filename} is saved!")
    else:
      return "Could not save the file. Try Again."


def show_userdb(user_id):
  with engine.connect() as conn:
    query = text(
      "SELECT file_id,file_name FROM db_files WHERE user_id = :user_id ORDER BY file_id DESC"
    )
    result = conn.execute(query, {'user_id': user_id})

    result_all = result.all()

    files = []
    for row in result_all:
      files.append(row._asdict())

    print("File Names : ", files)
  return files


def load_file(file_id):
  with engine.connect() as conn:
    query = text(
      "SELECT file_name,file_data FROM db_files WHERE file_id = :file_id LIMIT 1"
    )
    result = conn.execute(query, {'file_id': file_id})
    rows = result.all()
    if result is None:
      return 'No such file'
    row = rows[0]
    return row._asdict()


def delete_file_byid(file_id):
  with engine.connect() as conn:
    query = text("DELETE FROM db_files WHERE file_id = :file_id")
    result = conn.execute(query, {'file_id': file_id})
    print("QUERY", query)

    if result:
      print(f"{file_id} file id deleted successfully")
      return (f"{file_id} file id deleted successfully")
    else:
      return None


def search_dbfiles(user_id, file_name):
  with engine.connect() as conn:
    query = text(
      "SELECT file_id, file_name FROM `basket-boost-website`.db_files  where user_id=:user_id and file_name LIKE :file_name"
    )
     # Check if file_name is None, and assign an empty string if so
    file_name = '%' + file_name + '%' if file_name is not None else ''

    result = conn.execute(query, {
      'user_id': user_id,
      'file_name': '%' + file_name + '%'
    })
    print("QUERY", query)

    result_all = result.all()

    files = []
    for row in result_all:
      files.append(row._asdict())

    print("File Names : ", files)
  return files


def search_user(username, email):
  with engine.connect() as conn:
    query = text(
      "SELECT username, email, password, role FROM `basket-boost-website`.user_details  where username LIKE :username or email LIKE :email;"
    )
    # Check if username and email are None, and assign empty strings if so then None
    username = '%' + username + '%' if username is not None else ''
    email = '%' + email + '%' if email is not None else ''
    result = conn.execute(query, {
      'username': '%' + username + '%',
      'email': '%' + email + '%'
    })

    print("QUERY", query)

    result_all = result.all()

    users = []
    for row in result_all:
      users.append(row._asdict())

    print("User Names : ", users)
  return users