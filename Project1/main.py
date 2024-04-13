from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3

app = Flask(__name__)

# Route for the index page
@app.route('/')
def index():
    return render_template('index.html')

# Routes for different user roles
@app.route('/customer')
def customer():
    return render_template('customer.html', role='3')

@app.route('/register')
def register() :
    return render_template('customerRegister.html', role='3')

@app.route('/registerUser', methods=['POST'])
def registerUser() :
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    address = request.form['address']
    role = request.form['role']
    # Connect to the SQLite database
    conn = sqlite3.connect('Store.db')
    cursor = conn.cursor()

    # Check if the email already exists in the Customers table
    cursor.execute("SELECT * FROM Customers WHERE email = ?", (email,))
    existing_customer = cursor.fetchone()

    if existing_customer:
        # Email already exists, return an error message
        return "Email already exists. Please choose a different email."
    else:
        # Insert the new customer into the Customers table
        cursor.execute("INSERT INTO Customers (name, email, address, password, role_id) VALUES (?, ?, ?, ?, ?)",
                       (name, email, address, password, role))
        conn.commit()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        return "Customer registered successfully!"

@app.route('/employee')
def employee():
    return render_template('employee.html', role='2')

@app.route('/admin')
def admin():
    return render_template('admin.html', role='1')

@app.route('/login', methods=['POST'])
def login():
    # Get form data
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']

    #print(email)
    #print(password)
    #print(role)
    # Connect to the SQLite database
    conn = sqlite3.connect('Store.db')
    cursor = conn.cursor()

    # Determine the table based on the role
    if role == '3':
        table_name = 'Customers'
    elif role == '2':
        table_name = 'Employees'
    elif role == '1':
        table_name = 'Employees'
    else :
        return "Invalid role."

    # Query the table based on email and password
    cursor.execute(f"SELECT name FROM {table_name} WHERE email=? AND password=?", (email, password))
    result = cursor.fetchone()

    # Close the cursor and connection
    cursor.close()
    conn.close()

    # If a match is found, output a greeting message with the name
    if result:
        name = result[0]
        if role == '3':
            return render_template('Control/custCtrl.html', name=name, info=result)
        elif role == '2':
            return render_template('Control/empCtrl.html', name=name)
        elif role == '1':
            return render_template('Control/adminCtrl.html', name=name)
    else:
        return "Invalid email, password, or role."


# Route to render the admin control page
@app.route('/adminAdd', methods=['GET', 'POST'])
def adminAdd():
    if request.method == 'POST':
        if 'add_product' in request.form:
            name = request.form['name']
            description = request.form['description']
            stock = request.form['stock']
            price = request.form['price']

            conn = sqlite3.connect('Store.db')
            conn.execute('INSERT INTO Products (name, description, stock, price) VALUES (?, ?, ?, ?)', (name, description, stock, price))
            conn.commit()
            conn.close()
            return render_template('Control/adminCtrl.html', P_message="Added Product!")
        elif 'add_employee' in request.form:
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            role_id = request.form['role_id']

            conn = sqlite3.connect('Store.db')
            conn.execute('INSERT INTO Employees (name, email, password, role_id) VALUES (?, ?, ?, ?)', (name, email, password, role_id))
            conn.commit()
            conn.close()
            return render_template('Control/adminCtrl.html', E_message="Added Employee!")

    return "Invalid"

# Route to view transactions
@app.route('/transactions', methods=['POST'])
def transactions():
    cust_id = request.form['cust_id']

    conn = sqlite3.connect('Store.db')
    if cust_id:
        transactions = conn.execute('SELECT * FROM Transactions WHERE cust_id = ?', (cust_id,)).fetchall()
    else:
        transactions = conn.execute('SELECT * FROM Transactions').fetchall()
    conn.close()

    return render_template('Control/adminCtrl.html', transactions=transactions)


# Route to handle the form submission and charge the user
@app.route('/charge_user', methods=['POST'])
def charge_user():
    customer_id = request.form['customer_id']
    product_id = request.form['product_id']
    quantity = request.form['quantity']

    # Fetch product details from the database
    conn = sqlite3.connect('Store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, stock FROM Products WHERE id=?", (product_id,))
    product = cursor.fetchone()

    cursor.execute("SELECT id FROM Customers WHERE id=?", (customer_id,))
    customer = cursor.fetchone()
    if product and customer:
        product_name, price, stock = product
        if stock >= int(quantity):
            # Calculate total price
            total_price = price * int(quantity)

            # Perform transaction
            cursor.execute(
                "INSERT INTO Transactions (cust_id, prod_id, quantity, price, date) VALUES (?, ?, ?, ?, date('now'))",
                (customer_id, product_id, quantity, total_price))
            conn.commit()

            # Update stock
            new_stock = stock - int(quantity)
            cursor.execute("UPDATE Products SET stock=? WHERE id=?", (new_stock, product_id))
            conn.commit()

            return render_template('Control/empCtrl.html', C_message="Transaction Complete.")
        else:
            return render_template('Control/empCtrl.html', C_message="Out of Stock")
    else:
        return render_template('Control/empCtrl.html', C_message="No Product Found.")

# Route to view all stock
@app.route('/view_stock')
def view_stock():
    conn = sqlite3.connect('Store.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, stock FROM Products")
    stock = cursor.fetchall()
    stock_data = [{'id':row[0], 'name': row[1], 'stock': row[2]} for row in stock]
    return jsonify(stock_data)

@app.route('/update_customer', methods=['POST'])
def update_customer():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        address = request.form['address']
        password = request.form['password']

        # Update the customer information in the database
        conn = sqlite3.connect('Store.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE Customers SET name=?, address=? WHERE email = ? and password = ?', (name, address, email, password))
        conn.commit()
        conn.close()

        return render_template('Control/custCtrl.html', name=name)

if __name__ == '__main__':
    app.run(debug=True)
