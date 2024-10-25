from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import date, datetime, timedelta
import mysql.connector
import connect

####### Required for the reset function to work both locally and in PythonAnywhere
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'COMP636 S2'

start_date = datetime(2024,10,29)
pasture_growth_rate = 65    #kg DM/ha/day
stock_consumption_rate = 14 #kg DM/animal/day

db_connection = None
 
def getCursor():
    """Gets a new dictionary cursor for the database.
    If necessary, a new database connection is created here and used for all
    subsequent to getCursor()."""
    global db_connection
 
    if db_connection is None or not db_connection.is_connected():
        db_connection = mysql.connector.connect(user=connect.dbuser, \
            password=connect.dbpass, host=connect.dbhost,
            database=connect.dbname, autocommit=True)
       
    cursor = db_connection.cursor(buffered=False)   # returns a list
    cursor = db_connection.cursor(dictionary=True, buffered=False)  # use a dictionary cursor if you prefer
    return cursor


def get_date():
    cursor = getCursor()
    qstr = "SELECT curr_date FROM curr_date;"
    cursor.execute(qstr)
    result = cursor.fetchone()
    if result:  # Ensure the result is not None
        return result['curr_date']  # Access by column name since it's a dictionary
    return None  # Return None if no date is found

@app.route("/")
def home():
    # This line:
    curr_date = get_date()
    print(curr_date)
    # Replaces these lines:
    if 'curr_date' not in session:
        session.update({'curr_date': start_date})
    
    return render_template("home.html", curr_date=curr_date)

@app.route("/reset")
def reset():
    """Reset data to original state."""
    THIS_FOLDER = Path(__file__).parent.resolve()
    with open(THIS_FOLDER / 'fms-reset.sql', 'r') as f:
        mqstr = f.read()
        
        # Split by semicolon and filter out empty queries or whitespace
        queries = [qstr.strip() for qstr in mqstr.split(";") if qstr.strip()]
        
        for qstr in queries:
            cursor = getCursor()
            try:
                cursor.execute(qstr)
            except Exception as e:
                print(f"Error executing query: {qstr}\nError: {e}")
                # Handle the error (log, flash message, etc.)
            
    # Reset the session variable for days passed
    session['num_clicks'] = 0
    
    # Ensure the current date is reset properly
    get_date()

    return redirect(url_for('paddocks'))


@app.route("/mobs")
def mobs():
    """List the mob details (including the number of stock)."""
    cursor = getCursor()
    qstr = """
    SELECT m.id, m.name, p.name AS paddock_name, COUNT(s.id) AS num_stock
    FROM mobs m
    INNER JOIN paddocks p ON m.paddock_id = p.id
    LEFT JOIN stock s ON m.id = s.mob_id  -- Count stock in each mob
    GROUP BY m.id, m.name, p.name
    ORDER BY m.name;
    """ 
    cursor.execute(qstr)
    mobs = cursor.fetchall()  # Fetch results as tuples

    return render_template("mobs.html", mobs=mobs)


@app.route("/create_mob", methods=["GET", "POST"])
def create_mob():
    """Create a new mob."""
    cursor = getCursor()

    if request.method == "GET":
        # Fetch all paddocks to display in the form
        qstr = "SELECT id, name FROM paddocks"
        cursor.execute(qstr)
        paddocks = cursor.fetchall()

        return render_template("create_mob.html", paddocks=paddocks)

    if request.method == "POST":
        mob_name = request.form.get("mob_name")
        paddock_id = request.form.get("paddock_id")

        # Validate inputs
        if not mob_name or not paddock_id:
            flash("All fields are required!", "danger")
            return redirect(url_for("create_mob"))

        # Check if the selected paddock already has a mob assigned to it
        qstr = "SELECT COUNT(*) AS mob_count FROM mobs WHERE paddock_id = %s"
        cursor.execute(qstr, (paddock_id,))
        paddock_occupied_result = cursor.fetchone()

        # Debugging log
        # print(f"Query result: {paddock_occupied_result}")

        # Access the count using the dictionary key
        if paddock_occupied_result and paddock_occupied_result['mob_count'] > 0:
            flash("This paddock already has a mob assigned to it!", "danger")
            return redirect(url_for("create_mob"))

        # Insert the new mob into the database
        qstr = "INSERT INTO mobs (name, paddock_id) VALUES (%s, %s)"
        cursor.execute(qstr, (mob_name, paddock_id))
        db_connection.commit()

        flash("Mob created successfully!", "success")
        return redirect(url_for("mobs"))



@app.route("/update_mob/<int:mob_id>", methods=["GET", "POST"])
def update_mob(mob_id):
    """Update an existing mob."""
    cursor = getCursor()

    if request.method == "GET":
        # Fetch mob details to pre-fill the form
        qstr = "SELECT id, name, paddock_id FROM mobs WHERE id = %s"
        cursor.execute(qstr, (mob_id,))
        mob = cursor.fetchone()

        if mob is None:
            flash("Mob not found!", "danger")
            return redirect(url_for("mobs"))

        # Fetch paddocks that don't have a mob assigned or are currently assigned to this mob
        qstr = """
        SELECT id, name 
        FROM paddocks 
        WHERE id NOT IN (SELECT paddock_id FROM mobs WHERE paddock_id IS NOT NULL AND paddock_id != %s)
        OR id = %s
        """
        cursor.execute(qstr, (mob['paddock_id'], mob['paddock_id']))
        paddocks = cursor.fetchall()

        return render_template("update_mob.html", mob=mob, paddocks=paddocks)

    if request.method == "POST":
        mob_name = request.form.get("mob_name")
        paddock_id = request.form.get("paddock_id")

        # Validate inputs
        if not mob_name or not paddock_id:
            flash("All fields are required!", "danger")
            return redirect(url_for("update_mob", mob_id=mob_id))

        # Update mob in the database
        qstr = "UPDATE mobs SET name = %s, paddock_id = %s WHERE id = %s"
        cursor.execute(qstr, (mob_name, paddock_id, mob_id))
        db_connection.commit()

        flash("Mob updated successfully!", "success")
        return redirect(url_for("mobs"))



@app.route("/delete_mob/<int:mob_id>", methods=["POST"])
def delete_mob(mob_id):
    """Delete a mob and any associated stock entries from the database."""
    cursor = getCursor()

    # First, delete stock entries associated with the mob
    qstr = "DELETE FROM stock WHERE mob_id = %s"
    cursor.execute(qstr, (mob_id,))

    # Then, delete the mob itself
    qstr = "DELETE FROM mobs WHERE id = %s"
    cursor.execute(qstr, (mob_id,))
    db_connection.commit()

    # Flash a success message
    flash("Mob and associated stock entries deleted successfully!", "success")

    # Redirect back to the mobs listing page
    return redirect(url_for("mobs"))


@app.route("/paddocks", methods=["GET", "POST"])
def paddocks():
    """List paddock details and update pasture growth and consumption."""
    cursor = getCursor()

    # Set the simulator's start date as a date object
    start_date = datetime(2024, 10, 29).date()

    # Initialize or retrieve the number of days passed (clicks) from the session
    num_clicks = session.get('num_clicks', 0)

    # Calculate the current simulated date
    curr_date = start_date + timedelta(days=num_clicks)

    if request.method == "POST":
        # Increment the number of clicks (days passed)
        num_clicks += 1
        curr_date = start_date + timedelta(days=num_clicks)

        # Update the session for persistent tracking
        session['num_clicks'] = num_clicks

        # Fetch paddocks and their associated mobs and stock
        qstr = """
        SELECT p.id, p.area, p.total_dm, p.dm_per_ha, 
               IFNULL(COUNT(s.id), 0) AS num_stock 
        FROM paddocks p
        LEFT JOIN mobs m ON m.paddock_id = p.id
        LEFT JOIN stock s ON s.mob_id = m.id
        GROUP BY p.id
        """
        cursor.execute(qstr)
        paddocks = cursor.fetchall()

        # Update pasture values for each paddock
        for paddock in paddocks:
            num_stock = paddock['num_stock']  # Number of stock in the paddock
            consumption = num_stock * stock_consumption_rate  # Consumption by stock

            # Ensure total_dm is not None, initialize it to 0 if it's None
            total_dm = paddock['total_dm'] if paddock['total_dm'] is not None else 0

            new_total_dm = total_dm + pasture_growth_rate - consumption  # Update Total DM

            # Print calculation details
            calculation_details = {
                'paddock_name': paddock['id'],
                'starting_dm': total_dm,
                'growth': pasture_growth_rate,
                'consumption': consumption,
                'new_total_dm': new_total_dm
            }
            print(calculation_details)

            # Update the paddock in the database with the new total_dm
            cursor.execute("""
                UPDATE paddocks 
                SET total_dm = %s
                WHERE id = %s
            """, (new_total_dm, paddock['id']))

    # Fetch paddock details after recalculation (or initially if GET)
    qstr = """
    SELECT p.id, p.name AS paddock_name,
           IFNULL(m.name, 'No Mob') AS mob_name,
           COUNT(s.id) AS num_stock,
           p.area, p.dm_per_ha, p.total_dm
    FROM paddocks p
    LEFT JOIN mobs m ON m.paddock_id = p.id
    LEFT JOIN stock s ON s.mob_id = m.id
    GROUP BY p.id
    ORDER BY p.name;
    """
    cursor.execute(qstr)
    paddocks = cursor.fetchall()

    return render_template(
        "paddocks.html", 
        paddocks=paddocks, 
        curr_date=curr_date, 
        num_clicks=num_clicks  # Pass the number of days passed
    )







@app.route("/create_paddock", methods=["GET", "POST"])
def create_paddock():
    """Create a new paddock."""
    cursor = getCursor()

    if request.method == "GET":
        # Fetch paddocks with NULL or 0 values for area and dm_per_ha
        qstr = "SELECT id, name FROM paddocks WHERE area IS NULL OR area = 0 AND dm_per_ha IS NULL OR dm_per_ha = 0"
        cursor.execute(qstr)
        available_paddocks = cursor.fetchall()

        return render_template("create_paddock.html", paddocks=available_paddocks)

    if request.method == "POST":
        paddock_id = request.form.get("paddock_id")
        area = request.form.get("area")
        dm_per_ha = request.form.get("dm_per_ha")

        # Validate inputs
        if not paddock_id or not area or not dm_per_ha:
            flash("All fields are required!", "danger")
            return redirect(url_for("create_paddock"))

        # Calculate total DM
        total_dm = float(area) * float(dm_per_ha)

        # Update paddock in the database
        qstr = "UPDATE paddocks SET area = %s, dm_per_ha = %s, total_dm = %s WHERE id = %s"
        cursor.execute(qstr, (area, dm_per_ha, total_dm, paddock_id))
        db_connection.commit()

        flash("Paddock updated successfully!", "success")
        return redirect(url_for("paddocks"))

    

@app.route("/update_paddock/<int:paddock_id>", methods=["GET", "POST"])
def update_paddock(paddock_id):
    """Update an existing paddock."""
    cursor = getCursor()

    if request.method == "GET":
        # Fetch paddock details to pre-fill the form
        qstr = "SELECT * FROM paddocks WHERE id = %s"
        cursor.execute(qstr, (paddock_id,))
        paddock = cursor.fetchone()

        if paddock:
            return render_template("update_paddock.html", paddock=paddock)
        else:
            flash("Paddock not found!", "danger")
            return redirect(url_for("paddocks"))

    if request.method == "POST":
        paddock_name = request.form.get("paddock_name")
        area = request.form.get("area")
        dm_per_ha = request.form.get("dm_per_ha")

        # Validate inputs
        if not paddock_name or not area or not dm_per_ha:
            flash("All fields are required!", "danger")
            return redirect(url_for("update_paddock", paddock_id=paddock_id))

        # Update paddock in the database
        total_dm = float(area) * float(dm_per_ha)
        qstr = "UPDATE paddocks SET name = %s, area = %s, dm_per_ha = %s, total_dm = %s WHERE id = %s"
        cursor.execute(qstr, (paddock_name, area, dm_per_ha, total_dm, paddock_id))
        db_connection.commit()

        flash("Paddock updated successfully!", "success")
        return redirect(url_for("paddocks"))
    

@app.route("/delete_paddock/<int:paddock_id>", methods=["GET", "POST"])
def delete_paddock(paddock_id):
    """Delete a paddock."""
    cursor = getCursor()

    # Check if the paddock has any associated mobs or stock
    qstr = """
    SELECT COUNT(m.id) AS mob_count
    FROM mobs m
    WHERE m.paddock_id = %s
    """
    cursor.execute(qstr, (paddock_id,))
    result = cursor.fetchone()

    if result and result['mob_count'] > 0:
        flash("Paddock cannot be deleted because it has assigned mobs.", "danger")
        return redirect(url_for("paddocks"))

    # If no mobs are assigned, proceed to delete the paddock
    qstr = "DELETE FROM paddocks WHERE id = %s"
    cursor.execute(qstr, (paddock_id,))
    db_connection.commit()

    flash("Paddock deleted successfully.", "success")
    return redirect(url_for("paddocks"))

@app.route("/stock")
def stock():
    """List the stock entries grouped by mob."""
    cursor = getCursor()

    # Fetch stock details
    qstr = """
    SELECT m.id AS mob_id, m.name AS mob_name, p.name AS paddock_name, 
           s.id AS stock_id, s.dob AS dob, s.weight AS stock_weight
    FROM mobs m
    INNER JOIN paddocks p ON m.paddock_id = p.id
    LEFT JOIN stock s ON m.id = s.mob_id
    ORDER BY m.name;
    """
    cursor.execute(qstr)
    mob_data = cursor.fetchall()

    # Convert curr_date to a date object if it's a datetime
    curr_date = session.get('curr_date', datetime.today())
    if isinstance(curr_date, datetime):
        curr_date = curr_date.date()

    mob_stock = {}
    for mob in mob_data:
        mob_id = mob['mob_id']
        dob = mob['dob']

        # Ensure dob is a date object before calculating the age
        if dob and isinstance(dob, datetime):
            dob = dob.date()

        stock_age = (curr_date - dob).days // 365 if dob else None  # Age in years

        if mob_id not in mob_stock:
            mob_stock[mob_id] = {
                'name': mob['mob_name'],
                'paddock_name': mob['paddock_name'],
                'stock_entries': [],
                'total_weight': 0,  # Initialize total weight
                'num_stock': 0      # Initialize number of stocks
            }

        if mob['stock_id']:  # Ensure there's an actual stock record
            mob_stock[mob_id]['stock_entries'].append({
                'stock_id': mob['stock_id'],
                'stock_age': stock_age,
                'stock_weight': mob['stock_weight']
            })

            # Update total weight and number of stock entries for this mob
            mob_stock[mob_id]['total_weight'] += mob['stock_weight']
            mob_stock[mob_id]['num_stock'] += 1

    # Calculate the average weight for each mob
    for mob_id, mob in mob_stock.items():
        if mob['num_stock'] > 0:
            mob['avg_weight'] = mob['total_weight'] / mob['num_stock']  # Calculate average
        else:
            mob['avg_weight'] = None  # No stock, so no average weight

    return render_template("stock.html", mob_stock=mob_stock)


    

@app.route("/add_paddock", methods=["POST"])

def add_paddock():
    """Add a new paddock"""
    if request.method == "POST":
        name = request.form.get("name")
        area = request.form.get("area")
        dm_per_ha = request.form.get("dm_per_ha")
        total_dm = request.form.get("total_dm")

        cursor = getCursor()
        qstr = f"INSERT INTO paddocks (name, area, dm_per_ha, total_dm) VALUES ('{name}', {area}, {dm_per_ha}, {total_dm});"
        cursor.execute(qstr)
           
        return redirect(url_for('paddocks'))
    

    from datetime import timedelta

@app.route("/next_day", methods=["POST"])
def next_day():
    """Move the current date to the next day."""
    # Get the current date from the session
    curr_date = session.get('curr_date', None)
    
    if curr_date is None:
        curr_date = datetime.today()  # Default to today's date if not set

    # Move the date forward by 1 day
    next_date = curr_date + timedelta(days=1)

    # Update the session with the new date
    session['curr_date'] = next_date

    # Redirect back to the paddocks page
    return redirect(url_for('paddocks'))

@app.route("/create_stock", methods=["GET", "POST"])
def create_stock():
    """Create a new stock entry in a mob."""
    cursor = getCursor()

    # Handle GET request (display the form)
    if request.method == "GET":
        # Fetch all mobs to display in the dropdown
        cursor.execute("SELECT id, name FROM mobs")
        mobs = cursor.fetchall()
        return render_template("create_stock.html", mobs=mobs)

    # Handle POST request (form submission)
    if request.method == "POST":
        # Get form data
        mob_id = request.form.get("mob_id")
        dob = request.form.get("dob")
        weight = request.form.get("weight")

        # Validate inputs
        if not mob_id or not dob or not weight:
            flash("All fields are required!", "danger")
            return redirect(url_for("create_stock"))

        # Insert the new stock entry into the stock table
        qstr = """
        INSERT INTO stock (mob_id, dob, weight)
        VALUES (%s, %s, %s)
        """
        cursor.execute(qstr, (mob_id, dob, weight))

        # Commit the transaction
        db_connection.commit()

        # Redirect to a confirmation or another page
        flash("Stock entry created successfully!", "success")
        return redirect(url_for("mobs"))

    
    
@app.route("/update_stock/<int:stock_id>", methods=["GET", "POST"])
def update_stock(stock_id):
    """Update a stock entry's details, including mob assignment."""
    cursor = getCursor()

    if request.method == "GET":
        # Fetch the stock entry details to pre-fill the form
        qstr = "SELECT id, mob_id, dob, weight FROM stock WHERE id = %s"
        cursor.execute(qstr, (stock_id,))
        stock = cursor.fetchone()

        # Fetch all mobs to display in the dropdown
        cursor.execute("SELECT id, name FROM mobs")
        mobs = cursor.fetchall()

        if stock is None:
            flash("Stock entry not found!", "danger")
            return redirect(url_for("stock"))

        return render_template("update_stock.html", stock=stock, mobs=mobs)

    if request.method == "POST":
        # Get form data
        mob_id = request.form.get("mob_id")
        dob = request.form.get("dob")
        weight = request.form.get("weight")

        # Validate inputs
        if not mob_id or not dob or not weight:
            flash("All fields are required!", "danger")
            return redirect(url_for("update_stock", stock_id=stock_id))

        # Update the stock entry in the database
        qstr = """
        UPDATE stock
        SET mob_id = %s, dob = %s, weight = %s
        WHERE id = %s
        """
        cursor.execute(qstr, (mob_id, dob, weight, stock_id))
        db_connection.commit()

        # Flash success message
        flash("Stock entry updated successfully!", "success")

        # Redirect to the stock page
        return redirect(url_for("stock"))




@app.route("/delete_stock/<int:stock_id>", methods=["POST"])
def delete_stock(stock_id):
    """Delete a stock entry from the database."""
    cursor = getCursor()

    # Delete the stock entry from the database
    qstr = "DELETE FROM stock WHERE id = %s"
    cursor.execute(qstr, (stock_id,))
    db_connection.commit()

    # Flash a success message
    flash("Stock entry deleted successfully!", "success")

    # Redirect back to the stock listing page
    return redirect(url_for("stock"))
