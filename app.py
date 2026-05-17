from flask import Flask, render_template, request, redirect, url_for, session, flash
import json, datetime, sqlite3

app = Flask("__name__")
app.secret_key = "your-secret-key"

# FUNCTIONS <-------------------->
def load_data():
    # open multiple files
    with open("data/flowers.json") as file, open("data/addons.json") as adds:
        flowers = json.load(file)
        addons = json.load(adds)

    # return flowers
    return flowers, addons

# calculate the total cost of carts and add-ons
def calculate_total(cart, add_ons):
    discount_applied = False

    cart_total = sum(item['price'] * item['quantity'] for item in cart.values())
    addon_total = sum(add_on_item for add_on_item in add_ons.values())

    if (cart_total + addon_total) > 180:
        discount_applied = True

    # returning the total cost
    return cart_total + addon_total, cart_total, addon_total, discount_applied

# load database
def initialise_database():
    with sqlite3.connect("flower_shop.db") as conn:
        cursor = conn.cursor()
        cursor.execute(""" 
            CREATE TABLE IF NOT EXISTS orders (
                       order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                       invoice_number TEXT,
                       customer_name TEXT,
                       items TEXT,
                       addons TEXT,
                       total REAL,
                       date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       )
""")


# ROUTES <-------------------->

# routes from url to html template
@app.route("/")
def index():
    # tuple variables
    flowers, addons = load_data()

    # prepare stored cart session
    cart = session.get("cart", {})
    session_addons = session.get("selected_addons", {})

    retrieve_cart = cart
    # checking for the stock
    for flower_item, o in list(retrieve_cart.items()):

        print(flower_item)
        # if the stock runs out
        if flowers[flower_item]["stock"] <= 0:
            flash(f"Reminder: {flower_item} was removed from the cart due to out of stock.")
            del cart[flower_item]

            session["cart"] = cart # update session
            session.modified = True

    # calculate the overall total cost of all the items
    total, flower_subtotal, addon_subtotal, discounted_price = calculate_total(cart, session_addons)

    return render_template("index.html",
                           flowers = flowers, addons = addons,
                           cart = cart, total_cost = total, session_addons = session_addons,
                           flower_subtotal = flower_subtotal, addon_subtotal = addon_subtotal,
                           discounted = total - (total * 0.1) if discounted_price else False)

# index1.html
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    flower = request.form['flower'] # get selected "flower" name
    quantity = int(request.form["quantity"])
    flowers, addons = load_data() # load multiple variables, tuple variables 
    cart = session.get("cart", {})

    # some cores for validation
    original_quantity = cart[flower]["quantity"] if flower in cart else quantity # used for validating remaining stocks
    is_not_in_cart_yet = False

    # not in (i.e. run if not found)
    if flower not in flowers:
        flash("Invalid flower selected.")
        return redirect(url_for("index"))

    if flower in cart:
        cart[flower]["quantity"] += quantity # add existing quantity
    else:
        is_not_in_cart_yet = True
        cart[flower] = {
            "price": flowers[flower]["price"],
            "quantity": quantity
        }

    # check if there are stocks remaining within the flower
    if flowers[flower]["stock"] == 0:
        flash(f"Sorry, but {flower} runs out of stock.")
        del cart[flower]
        return redirect(url_for("index"))
    
    # Check if it exceeded the amount of stock left
    elif cart[flower]["quantity"] > flowers[flower]["stock"]:
        cart[flower]["quantity"] = flowers[flower]["stock"] # overrides the remaining stock

        # if in the cart
        if not is_not_in_cart_yet:
            stock_dif = flowers[flower]["stock"] - original_quantity

            flash(f"You have exceeded the quantity on a flower than there are left. {stock_dif if stock_dif else "No"} {flower}(s) were added to cart.")
        else:
            flash(f"You have exceeded the quantity on a flower than there are left, so {flowers[flower]["stock"]} {flower}(s) were added to cart.")
    else:
        flash(f"{quantity} {flower}(s) added to cart.")

    session["cart"] = cart # update session
    session.modified = True
    return redirect(url_for("index"))

    # return render_template("index1.html")

# remove cart function
def remove_all_items():
    session.pop("cart", None)
    session.pop("selected_addons", None)
    session.modified = True

# remove from the cart
@app.route("/remove_from_cart/<process_item>")
def remove_from_cart(process_item):
    cart = session.get("cart", {})

    if process_item in cart:
        del cart[process_item]
        session["cart"] = cart # update session
        session.modified = True
        flash(f"Removed all {process_item.capitalize()} from the cart.")
    else:
        flash("Item was not found in the cart")

    return redirect(url_for("index"))

# cancel order
@app.route("/cancel_order", methods=['POST'])
def cancel_order():
    remove_all_items()

    flash("You cancelled your order.")
    return redirect(url_for("index"))


@app.route("/about")
def about():
    return render_template("about.html")

# checkout route
@app.route("/checkout", methods=["POST"])
def checkout():
    # strip = leading whitespace removed | title = capitalised words
    customer_name = request.form['customer_name_input'].strip().title()

    # 1. Check if the customer name is appropriately entered, otherwise display the flask message and return to home page.
    if not customer_name:
        flash("Please enter your name to proceed to checkout.")
        return redirect(url_for('index'))

    # 2. get Flowers & Add-Ons from session
    invoice_flower = session.get("cart", {})
    invoice_addons = session.get("selected_addons", {})

    # 3. Check if the cart is not empty
    if not invoice_flower and not invoice_addons:
        flash("Your cart is empty.")
        return redirect(url_for('index'))
    
    # 4-5. Calculate Total + Fill Up Invoice Number and Date
    total, _1, _2, discounted_price = calculate_total(invoice_flower, invoice_addons) # get the calculation
    invoice_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # date and time from import
    invoice_number = f"INV_{customer_name.replace(' ', '_')}_{invoice_date}"

    remove_all_items() # remove all items in checkout

    # 6. Save order to SQLite database
    with sqlite3.connect("flower_shop.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO orders (invoice_number, customer_name, items, addons, total)
            VALUES (?, ?, ?, ?, ?)
        """, (invoice_number, customer_name, json.dumps(invoice_flower), json.dumps(invoice_addons), total - (total * 0.1) if discounted_price else total))

        conn.commit() # Save changes to the database

    print(f"\nSaved order from: {customer_name}")
    print(f"{invoice_flower}")
    print(f"Total: {total}\n")

    # generate invoice file
    invoice_filename = f"INV_{customer_name.replace(' ', '_')}_{datetime.datetime.now().strftime("%Y-%m-%d %H.%M.%S")}.txt"
    
    with open(invoice_filename, 'w') as f:
        # with open(f"{invoice_number}.txt", "w") as f:
        f.write("----- Flower Shop Invoice -----\n\n")

        f.write(f"Invoice Number: {invoice_number}\n")
        f.write(f"Customer Name: {customer_name}\n")
        f.write(f"Date: {invoice_date}\n\n")

        # list all flower items:
        if invoice_flower:
            f.write("Items:\n\n")

            for item, sectors in invoice_flower.items():
                f.write(f"{item}: {sectors["quantity"]} x ${sectors["price"]:.2f} = ${sectors["quantity"] * sectors["price"]:.2f}\n")
        
        # list all add-ons
        if invoice_addons:
            f.write("\nAdd-Ons:\n\n")

            for addon, data in invoice_addons.items():
                f.write(f"{addon}: ${data:.2f}\n")

        # total
        f.write(f"\nSubtotal: ${total:.2f}\n")
        f.write(f"Discount: (10%): -${total * 0.1:.2f}\n\n")
        f.write(f"Total: ${total - (total * 0.1):.2f}")

    # 7. Update Stocks

    # fetch existing flower.json
    with open("data/flowers.json", "r") as fl_file:
        fetched_flower_data = json.load(fl_file)

    # define from each of the items of 'invoice_flower'
    for flower_name, details in invoice_flower.items():
        if flower_name in fetched_flower_data:
            fetched_flower_data[flower_name]["stock"] -= details["quantity"]

            # resets to 0 to prevent negative miscounts
            if fetched_flower_data[flower_name]["stock"] < 0:
                fetched_flower_data[flower_name]["stock"] = 0

    # opens the file in write mode
    with open("data/flowers.json", "w") as fl_file:
        json.dump(fetched_flower_data, fl_file, indent=4)

    # 8. Display invoice on confirmation page
    return render_template("invoice.html", customer_name = customer_name,
                           get_flower = invoice_flower, get_addon = invoice_addons,
                           invoice_date = invoice_date, invoice_number = invoice_number,
                           total = total, discounted = total - (total * 0.1) if discounted_price else False,
                           discounted_deduct = total * 0.1 if discounted_price else None)


# selected addon
@app.route("/select_addon", methods=["POST"])
def select_addon():
    selected_addons = {}
    _, addons = load_data() # we only need addons, not flowers (_)

    # checkboxes, where multiple lists are selected, use: .getlist('~')
    selected_keys = request.form.getlist("addons_list")

    # loop on selected keys or addons as checklist, leave if nothing has been selected
    for current_add in selected_keys:
        if current_add in addons:
            selected_addons[current_add] = float(addons[current_add]["price"])
            print(selected_addons[current_add])

    # flash message
    if len(selected_keys):
        flash(f"{len(selected_keys)} {"Add-ons" if len(selected_keys) == 2 else "Add-on"}  added to cart.") # message
    else:
        flash(f"No add-ons selected.") # failed message


    session["selected_addons"] = selected_addons
    session.modified = True

    print(session)

    return redirect(url_for("index"))

# order history
@app.route("/order_history")
def order_history():
    return render_template("order_history.html")

# invoice
@app.route("/invoice")
def invoice():
    return render_template("invoice.html")

# comes the last
# if __name__ == 'main': checks if file is being run directly - only runs code if opened directly.
if __name__ == "__main__":
    initialise_database()
    app.run(debug = True)