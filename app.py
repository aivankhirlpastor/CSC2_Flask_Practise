from flask import Flask, render_template, request, redirect, url_for, session, flash
import json

app = Flask("__name__")
app.secret_key = "your-secret-key"

# functions
def load_data():
    with open("data/flowers.json") as file:
        flowers = json.load(file)
    return flowers

# routes from url to html template
@app.route("/")
def index():
    flowers = load_data()
    return render_template("index.html", flowers = flowers)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/checkout")
def checkout():
    return render_template("checkout.html")

# comes the last
# if __name__ == 'main': checks if file is being run directly - only runs code if opened directly.
if __name__ == "__main__":
    app.run(debug = True)