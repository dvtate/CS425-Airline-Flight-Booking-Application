from app import app
from app.auth import hashPassword, generateToken, loginUser
from app.flightBookerDB import db_interface
from flask import request
import re


@app.route('/customer/login', methods=['POST'])
def login():
    data = request.json
    email = data['email']
    password = data['password']
    token = loginUser(email,password)

    if not token:
        return {
            'message' : 'Invalid credentials'
        }, 401
    else:
        return {
            'token' : token
        }


@app.route('/customer/create', methods=['POST'])
def createCustomer():
    #try:
    data = request.json
    print('data:', data)
    name = data['name']
    email = data['email']
    password = data['password']

    print('new user: ', name,',', email,',', password)
    def isValidEmail(email):
        return re.match("[^@]+@[^@]+\.[^@]+", email) != None
    
    if not isValidEmail(email):
        print('invalid email...')
        return {
            'result' : False,
            'message' : 'Invalid email'
        }, 400

    c = db_interface.conn.cursor()

    if not db_interface.checkEmail(email):
        print('email in use')
        return {
            'result' : False,
            'message' : 'email already in use'
        }, 400

    c.execute("""
        INSERT INTO customers (name, email, password, authToken)
        VALUES (%s, %s, %s, %s)
        RETURNING customerId""", (name, email, password, generateToken(-1)))
    customer_id = c.fetchone()
    customer_id = customer_id[0]
    print("customerId: ", customer_id)

    authToken = generateToken(customer_id)
    c.execute("UPDATE customers SET password=%s, authToken=%s WHERE customerId=%s;", (
        hashPassword(customer_id, password), authToken, customer_id))

    c.close()

    print('created user!')
    return {
        'result': True,
        'authToken' : authToken,
        'message': 'Customer has been created.'
    }


@app.route('/customer/address/add', methods=['POST'])
def addCustomerAddress():
    # Getting customer ID from header
    customerId = request.headers.get('customerId')
    # Extracting rest of form data
    data = request.json
    line1 = data['line1']
    line2 = data['line2']
    postalCode = data['postalCode']
    city = data['city']
    state = data['state']
    country = data['country']

    db_interface.addCustomerAddress(customerId, line1, line2, postalCode, city, state, country)

    return {
        'result': True,
        'message': 'Customer address added.'
    }

@app.route('/customer/address/get', methods=['POST'])
def getCustomerAddress():
    customerId = request.headers.get('customerId')
    customerAddresses = db_interface.getCustomerAddresses(customerId)
    if customerAddresses:
        return {
            'result': True,
            'addresses': customerAddresses
        }
    return {
        'result': False
    }

@app.route('/customer/address/delete', methods=['POST'])
def deleteCustomerAddress():
    customerId = request.headers.get('customerId')
    data = request.json
    addressId = data['addressId']
    if deleteCustomerAddress(addressId, customerId):
        return {
            'result': True
        }
    return {
        'result': False
    }
