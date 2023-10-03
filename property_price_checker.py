#Script which uses MySQL and BeautifulSoup to store, scrape and eventually view plans for saving up for homes.
#The average house price for the user specified postcode has been taken from RightMove.
from bs4 import BeautifulSoup
from urllib import request
import mysql.connector
import requests
from datetime import date
import sys

#Database information.
mydb = mysql.connector.connect(
    host="sql8.freemysqlhosting.net",
    user="sql8519618",
    password="8ajPVxBZ2K",
    database="sql8519618")

cursor = mydb.cursor(buffered=True)

def create_tables():
    cursor.execute("CREATE TABLE users (username VARCHAR(255), password VARCHAR(255))")
    mydb.commit()
    cursor.execute("CREATE TABLE checks (username VARCHAR(255), post_code VARCHAR(255), month_1 VARCHAR(255), month_6 VARCHAR(255), date_check VARCHAR(255))")
    mydb.commit()

def login():
    global username
    user_allowed = False
    while user_allowed == False:
        username=input("Please enter your username\n").lower()
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        if cursor.rowcount==0:
            print("user doesn't exist, try again")
            user_allowed = False
        else:
            user_allowed = True

    pswd_tries_left = 3
    while pswd_tries_left != 0:
        password_log=input("Please enter your password:\n")

        query = "SELECT * FROM users WHERE username=%s AND password = %s"
        values = (username, password_log)
        cursor.execute(query, values)

        if cursor.rowcount==0:
            pswd_tries_left=pswd_tries_left-1
            if pswd_tries_left==1:
                print("Incorrect, please try again. %i try remaining." %(pswd_tries_left))
            else:
                print("Incorrect, please try again. %i tries remaining." %(pswd_tries_left))
        else:
            check_existing()
                
    print("Please contact the admin for assistance with your password.")
    sys.exit()

def check_existing():
    cursor.execute("SELECT post_code, date_check FROM checks WHERE username=%s", (username,))
    if cursor.rowcount==0:
        avg_check()
    else:
        print("you have existing checks, any new checks will replace old checks. ")
        for x in cursor.fetchall():
            print("You checked " + x[0] + " on " + x[1] + ".")

        avg_check()
    
def register():
    user_allowed = False
    while user_allowed == False:
        username=input("Please enter your desired username\n").lower()
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        if cursor.rowcount==0:
            print("great, name isn't taken")
            user_allowed = True
        else:
            print("username is taken")
            user_allowed = False

    password=input("Please enter a password\n")
    usr_pass=(username, password)
    
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", usr_pass)
    mydb.commit()

def avg_check():
    valid_post_code = False
    while valid_post_code == False:
        post_code=input("Enter the post code where your potential home is going to be located:\n").strip().replace(" ", "").upper()
        url="https://www.rightmove.co.uk/house-prices/"+ post_code +".html?country=england&searchLocation="+ post_code
        check_valid_url = requests.get(url)
        if check_valid_url.status_code == 400:
            print("enter a valid post code")
            valid_post_code = False
        elif check_valid_url.status_code == 200:
            print("valid post code entered")
            valid_post_code = True
            new_url="https://www.rightmove.co.uk/house-prices-in-my-area/marketTrendsTotalPropertiesSoldAndAveragePrice.html?searchLocation="+ post_code +"&sellersPriceGuide=Start+Search"

    cursor.execute("DELETE FROM checks WHERE username=%s AND post_code=%s", (username, post_code))
    mydb.commit()

    html=request.urlopen(new_url).read().decode('utf8', 'ignore')
    soup=BeautifulSoup(html, "html.parser")

    price_table = []
    for row in soup.find( "tr", {"class":"total"}):
        row_text = row.get_text().strip()
        if (row_text.isalpha()==False):
    
            price_table.append(row_text)
            
    price_table = list(filter(None, price_table))

    cleaned_price_table=[]
    for x in price_table:
        cleaned_price_table.append((x.partition(" (")[0]).replace(",", "").replace("£", ""))

    month_1_avg=cleaned_price_table[0] #Current price
    month_6_avg=cleaned_price_table[1] #Price 6 months ago
    
    print("The average property price in your desired area is £"+ month_6_avg + " currently.")
    print("Six months ago it was £"+ month_1_avg + ".")
    
    current_date = date.today()
    formatted_date = current_date.strftime("%d/%m/%Y")

    cursor.execute("INSERT INTO checks (post_code, username, date_check) VALUES (%s, %s, %s)", (post_code, username, formatted_date))
    mydb.commit()

    cursor.execute("UPDATE checks SET month_1 = %s WHERE username = %s AND post_code =%s", (month_1_avg, username, post_code))
    mydb.commit()

    cursor.execute("UPDATE checks SET month_6 = %s WHERE username = %s AND post_code =%s", (month_6_avg, username, post_code))
    mydb.commit()

    sys.exit()


#Checking if there are tables already in the database
#On the first run of the script, the tables will be created
cursor=mydb.cursor(buffered=True)
cursor.execute("SHOW tables")
initial_tables=0
for x in cursor:
  initial_tables=initial_tables+1
if initial_tables==0:
    create_tables()

#Logging in and registering
log_or_reg=input("Would you like to login or register?\n").lower()
if log_or_reg=="login":
    login()
elif log_or_reg=="register":
    register()
    login()
