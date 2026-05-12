from flask import Flask, render_template, request, redirect, url_for, session, flash
import json

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

def calculate_total(cart):
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    return total

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
    total = calculate_total(cart)

    return render_template("index.html", flowers = flowers, addons = addons, cart = cart, total_cost = total, session_addons = session_addons)

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

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/checkout")
def checkout():
    return render_template("checkout.html")

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