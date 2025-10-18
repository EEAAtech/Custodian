import logging
import json
import os
import pyodbc
from flask import Flask, request, jsonify


# --- App Setup (Flask app object is created as before) ---
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# --- Database Connection and Helpers (No changes in this section) ---
def get_db_connection():
    driver = os.environ.get('DB_DRIVER')
    server = os.environ.get('DB_SERVER')
    database = os.environ.get('DB_NAME')
    username = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    conn_str = f'DRIVER={driver};SERVER=tcp:{server};DATABASE={database};UID={username};PWD={password}'
    try:
        conn = pyodbc.connect(conn_str, autocommit=True) # autocommit=True is good practice for functions
        return conn
    except pyodbc.Error as ex:
        print(f"Database connection failed: {ex}")
        raise

@app.route('/api/get_budget_report', methods=['GET'])
def get_budget_report():
    """
    Azure Function to fetch budget report data by calling a stored procedure.
    """
    logging.info('Python HTTP trigger function processed a request.')

    try:
        budget_name = request.args.get('budgetName')
        amount_flag = request.args.get('amountFlag')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')

        if not all([budget_name, amount_flag, start_date, end_date]):
            return jsonify({"error ": "Missing required parameters in request body."}), 400
        

        results = []
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Parameters for the stored procedure
            params = (budget_name, amount_flag, start_date, end_date)
            
            # Note: The syntax for calling a stored procedure can vary by driver
            # This syntax is common for SQL Server
            sql_exec = "{CALL dbo.usp_GetMonthlyBudgetReport(?, ?, ?, ?)}"
            cursor.execute(sql_exec, params)
            columns = [column[0] for column in cursor.description]
            items = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return jsonify(items)
    except Exception as e:
        print(f"Error fetching filtered budgets: {e}")
        return jsonify({"error": str(e)}), 500        

@app.route('/api/get_categories', methods=['GET'])
def get_categories():
    """
    Azure Function to fetch a distinct list of budget names from the Category table.
    """
    logging.info('Fetching list of budget names.')

    try:
        budget_names = []
        with get_db_connection() as conn:
            cursor = conn.cursor()
            sql = "SELECT DISTINCT BudgetName FROM dbo.Category WHERE BudgetName IS NOT NULL ORDER BY BudgetName;"
            cursor.execute(sql)
            columns = [column[0] for column in cursor.description]
            items = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return jsonify(items)


    except Exception as e:
        print(f"Error fetching categories: {e}")
        return jsonify({"error": str(e)}), 500

