from flask import Flask, render_template, request, redirect, url_for, session, flash
import json, datetime

app = Flask("__name__")
app.secret_key = "your-secret-key"

# functions
def load_data():
    # open multiple files
    with open("data/flowers.json") as file, open("data/addons.json") as adds:
        flowers = json.load(file)
        addons = json.load(adds)

    # return flowers
    return flowers, addons

# calculate the total cost of carts and add-ons
def calculate_total(cart, add_ons):
    cart_total = sum(item['price'] * item['quantity'] for item in cart.values())
    addon_total = sum(add_on_item for add_on_item in add_ons.values())

    # returning the total cost
    return cart_total + addon_total, cart_total, addon_total

# routes from url to html template
@app.route("/")
def index():
    # tuple variables
    flowers, addons = load_data()

    # prepare stored cart session
    cart = session.get("cart", {})
    session_addons = session.get("selected_addons", {})
    print(session_addons)

    # calculate the overall total cost of all the items
    total, flower_subtotal, addon_subtotal = calculate_total(cart, session_addons)

    return render_template("index.html",
                           flowers = flowers, addons = addons,
                           cart = cart, total_cost = total, session_addons = session_addons,
                           flower_subtotal = flower_subtotal, addon_subtotal = addon_subtotal)

# index1.html
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    flower = request.form['flower'] # get selected "flower" name
    quantity = int(request.form["quantity"])
    flowers, addons = load_data() # load multiple variables, tuple variables 
    cart = session.get("cart", {})

    # not in (i.e. run if not found)
    if flower not in flowers:
        flash("Invalid flower selected.")
        return redirect(url_for("index"))

    if flower in cart:
        cart[flower]["quantity"] += quantity # add existing quantity
    else:
        cart[flower] = {
            "price": flowers[flower]["price"],
            "quantity": quantity
        }
    
    session["cart"] = cart # update session
    session.modified = True
    flash(f"{quantity} {flower}(s) added to cart.")
    return redirect(url_for("index"))

    # return render_template("index1.html")

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

# remove cart function
def remove_all_items():
    session.pop("cart", None)
    session.pop("selected_addons", None)
    session.modified = True

# cancel order
@app.route("/cancel_order", methods=['POST'])
def cancel_order():
    remove_all_items()

    flash("You cancelled your order.")
    return redirect(url_for("index"))


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/checkout", methods=["POST"])
def checkout():
    # strip = leading whitespace removed | title = capitalised words
    customer_name = request.form['customer_name_input'].strip().title()

    # Check if the customer name is appropriately entered, otherwise display the flask message and return to home page.
    if not customer_name:
        flash("Please enter your name to proceed to checkout.")
        return redirect(url_for('index'))

    # get cart session
    invoice_flower = session.get("cart", {})
    invoice_addons = session.get("selected_addons", {})

    if not invoice_flower and not invoice_addons:
        flash("Your cart is empty.")
        return redirect(url_for('index'))
    
    # fill up basics
    total = calculate_total(invoice_flower, invoice_addons) # get the calculation
    invoice_date = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%S") # date and time from import
    invoice_number = f"INV_{customer_name.replace(' ', '_')}_{invoice_date}"

    remove_all_items() # remove all items in checkout

    return render_template("invoice.html", customer_name = customer_name,
                           get_flower = invoice_flower, get_addon = invoice_addons,
                           invoice_date = invoice_date, invoice_number = invoice_number,
                           total = total)


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
    app.run(debug = True)