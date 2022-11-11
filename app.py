from flask import Flask, render_template, request, redirect, flash, session
import pymongo
import os
from passlib.hash import pbkdf2_sha256
app = Flask(__name__)
if os.environ.get('MONGO_URI')== None: #tells you if code is running on my computer to safe guard connectionstring
    file = open('connectionstring.txt','r')
    connectionstring = file.read()
    file.close()
else:
    connectionstring = os.environ.get('MONGO_URI') #if you run on heruko

if os.environ.get('SECRET_KEY')== None: #tells you if code is running on my computer to safe guard connectionstring
    file = open('secretkey.txt','r')
    secretkey = file.read()
    file.close()
else:
    secretkey = os.environ.get('SECRET_KEY') 
app.config["SECRET_KEY"] = secretkey
cluster = pymongo.MongoClient(connectionstring)
database = cluster['onestopshop']
collection = database['useraccounts']
product_cards = database['items']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods =['GET', "POST"])
def login():
    if request.method == "GET":
        if 'username' in session:
            return redirect('/home')
        return render_template('login.html')
    else:
        username = request.form['username']
        password = request.form['password']
        userinfo = collection.find_one({'username':username})
        if userinfo is None:
            flash("username or password does not exist","danger")
            return redirect('/login')
        if pbkdf2_sha256.verify(password, userinfo['password']):
            session['username'] = username
            return redirect('/home')
        else:
            flash("username of password does not exist","danger")
            return redirect('/login')
        

@app.route('/signup', methods = ["GET", "POST"])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    else:
        username= request.form['username']
        password = request.form['password']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        hashpass = pbkdf2_sha256.hash(password)
        record = {'firstname': firstname, 'lastname': lastname,'username':username, 'password':hashpass}
        collection.insert_one(record)
        return redirect('/login')
    
@app.route('/home', methods = ["GET", "POST"])
def home():
    if 'username' in session:
        userinfo = collection.find_one({'username': session['username']}) 
        firstname = userinfo['firstname']
        return render_template('home.html', firstname= firstname)
    
    else:
        flash("please login again","primary")
        return redirect('/login')

@app.route('/shop', methods=['GET'])
def shop():
    items=[]
    all_items = product_cards.find()
    for loop in all_items:
        items.append(loop)
    return render_template('shop.html', items=items)

@app.route('/addcartitems', methods=['GET','POST'])
def addcartitems():
    if request.method=='GET':
        return render_template('addcartitems.html')
    else:
        itemname = request.form['itemname']
        price = request.form['price']
        image = request.form['image']
        item_info = {'itemname': itemname, 'price': price,'image':image}
        product_cards.insert_one(item_info)
        return redirect('/addcartitems')

@app.route('/add_to_cart')
def add_to_cart():
    if 'username' not in session:
        flash('Please login to add to cart','danger')
        return redirect('/login')
    else:
        itemname = request.args.get('itemname') #getting the itemname from the url 
        cart ={} #make the cart 
        userinfo = collection.find_one({"username":session['username']}) #get details of currently logged in user
        if 'cart' in userinfo: #if cart dictionary is in the userinfo then theres an item in cart already
            cart = userinfo['cart'] #updates cart with current details
        #Item counter
        if itemname in cart:
            cart[itemname] +=1
        else:
            cart[itemname] = 1
        #updates userinfo with cart information
        collection.update_one({"username":session['username']}, {"$set":{"cart":cart}})
        return redirect('/shop')

@app.route('/checkout')
def checkout():
    if 'username' in session:
        userinfo = collection.find_one({"username":session['username']})
        cart = userinfo['cart']
        prices = {}
        totalprice = {}
        total_counter = 0
        for i in cart:
            item_details = product_cards.find_one({'itemname':i})
            price = item_details['price']
            prices[i] = price
            x= cart[i]
            totalprice[i] = int(price)*x
            total_counter = total_counter + totalprice[i]
        return render_template('checkout.html', cart = cart, prices = prices, totalprice = totalprice, tc= total_counter)
    else:
        flash('Please login to checkout','danger')
        return redirect('/login')


@app.route('/logout')
def logout():
    del(session['username'])
    flash('you have succesfully logged out','success')
    return redirect('/login')

if __name__ == '__main__':
    app.run()