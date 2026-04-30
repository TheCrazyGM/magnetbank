import os
import sys
from flask import Flask, render_template, request
from beem.exceptions import ContentDoesNotExistsException

# Add current directory and subdirectory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
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
            try:
                data = lookup_edits(q)
            except ContentDoesNotExistsException:
                data = {"edits": [{"trx_id": 0, "body": "Content does not exist!"}]}
            except Exception as e:
                data = {"edits": [{"trx_id": 0, "body": f"Error: {str(e)}"}]}
        else:
            data = {
                "edits": [
                    {
                        "trx_id": 0,
                        "body": "Please input a valid authorperm such as @user/permlink",
                    }
                ]
            }
        return render_template("edit_results.html", data=data)


# Run Flask app
if __name__ == "__main__":
    app.run(debug=True, port=5001)
