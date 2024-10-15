# Rename to database_config.py for clarity
# import the connector
import mysql.connector

# establish a connection to MySQL database
connection = mysql.connector.connect(
  host="localhost",
  user="educative",
  password="secret",
  database="flight"
)

# create a cusrsor object to perform quries
mycursor = connection.cursor()

# query for a table named users
# mycursor.execute("SELECT * from users")
mycursor.execute("SELECT user, host FROM mysql.user WHERE user = 'educative';")

# fetch all retrieved rows
myresult = mycursor.fetchall()

# display all rows onto the console
for x in myresult:
  print(x)


mycursor.close()
connection.close()


def get_db_connection():
    connection = mysql.connector.connect(
      host="localhost",
      user="educative",
      password="secret",
      database="flight"
    )
    return connection