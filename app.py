import os, sqlite3
from pathlib import Path
from functools import wraps
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'local-demo-key-change-me')
DB = Path(__file__).with_name('inventory.db')

def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with connect() as db:
        db.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, name TEXT NOT NULL, sku TEXT UNIQUE NOT NULL, category TEXT NOT NULL, price REAL NOT NULL CHECK(price>=0), quantity INTEGER NOT NULL CHECK(quantity>=0), reorder_level INTEGER NOT NULL DEFAULT 5 CHECK(reorder_level>=0), supplier TEXT DEFAULT '', created_at TEXT NOT NULL);''')
        if not db.execute('SELECT 1 FROM users LIMIT 1').fetchone():
            db.execute('INSERT INTO users(username,password_hash) VALUES(?,?)', ('admin', generate_password_hash('admin123')))
        if not db.execute('SELECT 1 FROM products LIMIT 1').fetchone():
            data=[('Wireless Mouse','ACC-1001','Accessories',799,24,8,'TechSource'),('Mechanical Keyboard','ACC-1002','Accessories',2499,7,5,'KeyWorks'),('USB-C Hub','ACC-1003','Accessories',1599,3,6,'TechSource'),('27-inch Monitor','DIS-2001','Displays',18499,12,4,'PixelSupply'),('Laptop Stand','OFF-3001','Office',1199,0,5,'DeskGoods'),('Webcam HD','ACC-1004','Accessories',3299,9,4,'VisionWare')]
            db.executemany('INSERT INTO products(name,sku,category,price,quantity,reorder_level,supplier,created_at) VALUES(?,?,?,?,?,?,?,?)', [(*x,date.today().isoformat()) for x in data])

def signed_in(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):
        if not session.get('user_id'):
            flash('Please sign in first.','warning'); return redirect(url_for('login'))
        return fn(*args,**kwargs)
    return wrapper

def form_values():
    name=request.form.get('name','').strip(); sku=request.form.get('sku','').strip().upper(); category=request.form.get('category','').strip(); supplier=request.form.get('supplier','').strip()
    try: price=float(request.form.get('price','')); qty=int(request.form.get('quantity','')); reorder=int(request.form.get('reorder_level','5'))
    except ValueError: raise ValueError('Price must be a number; quantities must be whole numbers.')
    if not name or not sku or not category: raise ValueError('Name, SKU and category are required.')
    if price<0 or qty<0 or reorder<0: raise ValueError('Price and stock values cannot be negative.')
    if len(name)>100 or len(sku)>30 or len(category)>60 or len(supplier)>100: raise ValueError('A text field is too long.')
    return name,sku,category,price,qty,reorder,supplier

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        with connect() as db: user=db.execute('SELECT * FROM users WHERE username=?',(request.form.get('username','').strip(),)).fetchone()
        if user and check_password_hash(user['password_hash'],request.form.get('password','')):
            session.clear(); session['user_id']=user['id']; session['username']=user['username']; return redirect(url_for('dashboard'))
        flash('Username or password is incorrect.','danger')
    return render_template('login.html')

@app.get('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

@app.get('/')
@signed_in
def dashboard():
    q=request.args.get('q','').strip(); cat=request.args.get('category',''); low=request.args.get('low','')
    sql='SELECT * FROM products WHERE 1=1'; args=[]
    if q: sql+=' AND (name LIKE ? OR sku LIKE ? OR supplier LIKE ?)'; args += [f'%{q}%']*3
    if cat: sql+=' AND category=?'; args.append(cat)
    if low=='1': sql+=' AND quantity<=reorder_level'
    sql+=' ORDER BY name COLLATE NOCASE'
    with connect() as db:
        products=db.execute(sql,args).fetchall()
        stats=db.execute('SELECT COUNT(*) products,COALESCE(SUM(quantity),0) units,COALESCE(SUM(price*quantity),0) value,COALESCE(SUM(quantity<=reorder_level),0) low FROM products').fetchone()
        categories=[r[0] for r in db.execute('SELECT DISTINCT category FROM products ORDER BY category')]
        alerts=db.execute('SELECT * FROM products WHERE quantity<=reorder_level ORDER BY quantity LIMIT 5').fetchall()
    return render_template('dashboard.html',products=products,stats=stats,categories=categories,alerts=alerts,q=q,cat=cat,low=low)

@app.route('/products/new',methods=['GET','POST'])
@app.route('/products/<int:pid>/edit',methods=['GET','POST'])
@signed_in
def product_form(pid=None):
    with connect() as db: product=db.execute('SELECT * FROM products WHERE id=?',(pid,)).fetchone() if pid else None
    if pid and not product: flash('Product not found.','warning'); return redirect(url_for('dashboard'))
    if request.method=='POST':
        try:
            values=form_values()
            with connect() as db:
                if pid: db.execute('UPDATE products SET name=?,sku=?,category=?,price=?,quantity=?,reorder_level=?,supplier=? WHERE id=?',(*values,pid))
                else: db.execute('INSERT INTO products(name,sku,category,price,quantity,reorder_level,supplier,created_at) VALUES(?,?,?,?,?,?,?,?)',(*values,date.today().isoformat()))
            flash('Product saved successfully.','success'); return redirect(url_for('dashboard'))
        except ValueError as e: flash(str(e),'danger')
        except sqlite3.IntegrityError: flash('SKU already exists; use a unique SKU.','danger')
    return render_template('product_form.html',product=product)

@app.post('/products/<int:pid>/delete')
@signed_in
def delete(pid):
    with connect() as db: db.execute('DELETE FROM products WHERE id=?',(pid,))
    flash('Product deleted.','info'); return redirect(url_for('dashboard'))

@app.post('/products/<int:pid>/stock')
@signed_in
def stock(pid):
    try:
        change=int(request.form.get('change',''))
        if change==0: raise ValueError
        with connect() as db:
            row=db.execute('SELECT quantity FROM products WHERE id=?',(pid,)).fetchone()
            if not row: flash('Product not found.','warning')
            elif row['quantity']+change<0: flash('Stock cannot go below zero.','danger')
            else: db.execute('UPDATE products SET quantity=quantity+? WHERE id=?',(change,pid)); flash('Stock updated.','success')
    except ValueError: flash('Enter a non-zero whole number.','danger')
    return redirect(url_for('dashboard'))

if __name__=='__main__':
    init_db(); app.run(debug=False)
