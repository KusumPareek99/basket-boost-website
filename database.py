from sqlalchemy import create_engine, text, select
import re
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

    # print("USER DETAILS : ", user_details)
    return user_details

def authenticate_user(username, password):
  role=''
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
      return ("Login successful",user_id,role,org_id)
    else:
      return "Invalid username or password"

def load_user_byname_byemail(username,email):
  with engine.connect() as conn:
    query = text(
      "SELECT * FROM user_details WHERE username = :username OR email = :email"
    )
    result = conn.execute(query, {'username': username, 'email': email})
    return result

def load_all_users_byorg(org_id):
  with engine.connect() as conn:

    
    query = text(
      "SELECT * FROM user_details WHERE org_id = :org_id"
    )
    result = conn.execute(query, {'org_id': org_id})
  
    users = []
    
    for row in result.all():
      users.append(row._asdict())

  return users

def load_user(user_id):
  with engine.connect() as conn:

    # user_id= 2
    query = text(
      "SELECT * FROM user_details WHERE user_id = :user_id"
    )
    result = conn.execute(query, {'user_id': user_id})
  
    rows = result.all()

  if len(rows) == 0:
    return None
  else :
    row = rows[0]
    print(row._asdict())
    return row._asdict()

    # print("user", users)

  return users
# load_user(2) 

def delete_user_byid(user_id):
  with engine.connect() as conn:
    query = text("DELETE FROM user_details WHERE user_id = :user_id")
    result = conn.execute(query,{'user_id': user_id})
    
    if result:
     return (f"{user_id} deleted successfully")
    else :
      return None 

def edit_user_byid(user_id,username,password,email,role):
  with engine.connect() as conn:
    query = text("UPDATE user_details SET username = :username, email = :email,password = :password,role = :role WHERE user_id = :user_id ")
    result = conn.execute(query,{'user_id': user_id, 'username': username, 'email': email, 'password': password, 'role': role})
    if result:
     return (f"{user_id} updated successfully")
    else :
      return None 

# print(edit_user_byid('2','paku','123456','paku@gmail.com','P')) 
# with engine.connect() as conn:

#   org_id= 1
#   query = text(
#     "SELECT * FROM user_details WHERE org_id = :org_id"
#   )
#   result = conn.execute(query, {'org_id': org_id})

#   users = []
  
#   for row in result.all():
#     users.append(row._asdict())

#   print(users[1]['username'])

#   for user in users:
#     for ele in user:
#       print(f"{ele}:{user[ele]}")
    