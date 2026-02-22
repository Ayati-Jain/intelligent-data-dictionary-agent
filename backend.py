import plotly.express as px
import plotly.io as pio
import json
from flask import Flask, jsonify, render_template, request
import sqlite3
import os
import pandas as pd

app = Flask(__name__, template_folder="../templates")

UPLOAD_FOLDER = "../uploads"
DATABASE = "dynamic.db"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------------
# DATABASE CONNECTION
# -------------------------
def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    return render_template("dashboard.html")

# -------------------------
# UPLOAD EXCEL
# -------------------------
@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    excel = pd.ExcelFile(filepath)
    sheets = excel.sheet_names

    conn = get_connection()

    for sheet in sheets:
        df = pd.read_excel(filepath, sheet_name=sheet)
        df.to_sql(sheet, conn, if_exists="replace", index=False)

    conn.close()

    return jsonify({"tables": sheets})

# -------------------------
# GET TABLE DETAILS
# -------------------------
@app.route("/table/<table_name>")
def table_details(table_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info([{table_name}])")
    columns = [row[1] for row in cursor.fetchall()]

    cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
    count = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "columns": columns,
        "row_count": count
    })
# -------------------------
# CONNECT SQLITE DATABASE
# -------------------------
@app.route("/connect_sql", methods=["POST"])
def connect_sql():
    db_name = request.json.get("database")

    if not db_name.endswith(".db"):
        db_name += ".db"

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, db_name)

    if not os.path.exists(db_path):
        return jsonify({"message": "Database not found.", "tables": []})

    global DATABASE
    DATABASE = db_path

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%';
    """)
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "message": f"Connected to {db_name}",
        "tables": tables
    })
# -------------------------
# ASK QUESTION
# -------------------------
@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    question = "".join(c for c in data["question"].lower() if c.isalnum() or c.isspace())
    table = data["table"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info([{table}])")
    columns_info = cursor.fetchall()
    column_names = [col[1] for col in columns_info]
    
    target_column = None
    sorted_cols = sorted(column_names, key=len, reverse=True)
    for col in sorted_cols:
        if col.lower() in question:
            target_column = col
            break

    answer = ""
    chart_json = None 

    try:
        if "row" in question or "count" in question:
            cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
            count = cursor.fetchone()[0]
            answer = f"{table} contains {count} rows."

        elif any(k in question for k in ["average", "avg", "max", "min", "sum", "total"]):

            if not target_column:
              return jsonify({"answer": "Please mention a valid column name."})

    # Detect aggregation function
            if any(k in question for k in ["average", "avg"]):
              func = "AVG"
            elif "max" in question:
              func = "MAX"
            elif "min" in question:
             func = "MIN"
            else:
             func = "SUM"

    # Ensure column is numeric
            cursor.execute(f"""
              SELECT [{target_column}] 
              FROM [{table}] 
              WHERE [{target_column}] IS NOT NULL 
              LIMIT 5
            """)
            sample = cursor.fetchall()

            try:
             float(sample[0][0])
            except:
             return jsonify({"answer": f"{target_column} is not numeric."})

            cursor.execute(f"SELECT {func}([{target_column}]) FROM [{table}]")
            res = cursor.fetchone()[0]

            answer = f"{func.capitalize()} of {target_column} is {round(res or 0,2)}"
                
            # --- PIE CHART GENERATION LOGIC ---
            preferred_categories = ["Region", "Category", "Customer Segment", "Ship Mode"]

            category_col = None
            for col in column_names:
             if col in preferred_categories:
                category_col = col
                break

            if not category_col:
                # fallback to first non-numeric column
              for col in column_names:
                 cursor.execute(f"SELECT [{col}] FROM [{table}] LIMIT 5")
                 sample = cursor.fetchall()
                 try:
                    float(sample[0][0])
                 except:
                    category_col = col
                    break
                
            if category_col:
                    query = f"SELECT [{category_col}], {func}([{target_column}]) as val FROM [{table}] GROUP BY [{category_col}] ORDER BY val DESC LIMIT 10"
                    df_chart = pd.read_sql_query(query, conn)
                    
                    # Changed from px.bar to px.pie
                    fig = px.pie(
                        df_chart, 
                        names=category_col, 
                        values='val', 
                        title=f"{func} {target_column} by {category_col}"
                    )
                    chart_json = pio.to_json(fig)

        elif "show" in question:
            cursor.execute(f"SELECT * FROM [{table}] LIMIT 5")
            rows = cursor.fetchall()
            answer = [dict(row) for row in rows]
            
    except Exception as e:
        answer = f"Error: {str(e)}"

    conn.close()
    return jsonify({"answer": answer, "chart": chart_json})

if __name__ == "__main__":
    app.run(debug=True)

