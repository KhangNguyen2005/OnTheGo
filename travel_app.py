from flask import Flask, render_template, request
from travel_backend import load_data, filter_trips_by_attributes

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    # Only use 'rating' and 'type' for filtering.
    columns = ["rating", "type"]
    table_html = None
    if request.method == "POST":
        filters = {col: request.form.get(col, "").strip() for col in columns}
        filtered = filter_trips_by_attributes(filters)
        table_html = filtered.to_html(classes="table table-striped", index=False)
    return render_template("index.html", columns=columns, table_html=table_html)

if __name__ == "__main__":
    app.run(debug=True)