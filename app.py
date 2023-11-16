from flask import Flask, render_template, request
from beem.exceptions import ContentDoesNotExistsException

from utils.lookup_edits import lookup_edits

# Create Flask app instance
app = Flask("misctools")

# Define route for homepage and category pages
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/lookup", methods=["GET", "POST"])
def export_edits():
    if request.method == "GET":
        return render_template("edit_search.html")
    elif request.method == "POST":
        q = request.form.get("q")
        if q and q.startswith("@"):
            username, permlink = q.split("/")
            try:
                data = lookup_edits(q)
            except ContentDoesNotExistsException:
                data = {"edits":[{"trx_id":0,"body":"Content does not exist!"}]}
        else:
            data = {"edits":[{"trx_id":0, "body": "Please input a valid authorperm such as @user/permlink"}]}
        return render_template("edit_results.html", data=data)

# Run Flask app
if __name__ == "__main__":
    app.run()
