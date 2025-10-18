import logging
import json
import os
import pyodbc
import azure.functions as func

# Define the function app
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# --- Database Connection and Helpers (No changes in this section) ---
def get_db_connection():
    driver = os.environ.get('DB_DRIVER', '{ODBC Driver 18 for SQL Server}')
    server = os.environ.get('DB_SERVER')
    database = os.environ.get('DB_NAME')
    username = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')

    if not all([server, database, username, password]):
        logging.error("FATAL: Database environment variables are not set.")
        raise ValueError("Missing database configuration in environment settings.")
    
    conn_str = f'DRIVER={driver};SERVER=tcp:{server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'
    try:
        conn = pyodbc.connect(conn_str, autocommit=True) # autocommit=True is good practice for functions
        return conn
    except pyodbc.Error as ex:
        print(f"Database connection failed: {ex}")
        raise

# --- API Route for Budget Names ---
@app.route(route="/api/get_budget_names", methods=['GET'])
def get_budget_names(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Fetching list of budget names.')
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            sql_query = "SELECT DISTINCT BudgetName FROM dbo.Category WHERE BudgetName IS NOT NULL ORDER BY BudgetName;"
            cursor.execute(sql_query)
            budget_names = [row[0] for row in cursor.fetchall()]
        return func.HttpResponse(json.dumps(budget_names), mimetype="application/json")
    except Exception as e:
        logging.error(f"An error occurred while fetching budget names: {e}", exc_info=True)
        return func.HttpResponse("An internal server error occurred.", status_code=500)

# --- API Route for Report Generation ---
@app.route(route="/api/get_report", methods=['POST'])
def get_report(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing a report request.')
    try:
        req_body = req.get_json()
        budget_names = req_body.get('budgetNames')
        amount_flag = req_body.get('amountFlag')
        start_date = req_body.get('startDate')
        end_date = req_body.get('endDate')

        if not all([budget_names, amount_flag, start_date, end_date]):
            return func.HttpResponse("Missing required parameters.", status_code=400)

        results = []
        with get_db_connection() as conn:
            cursor = conn.cursor()
            params = (budget_names, amount_flag, start_date, end_date)
            sql_exec = "{CALL dbo.usp_GetMonthlyBudgetReport(?, ?, ?, ?)}"
            cursor.execute(sql_exec, params)
            columns = [column[0] for column in cursor.description]
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
        
        return func.HttpResponse(json.dumps(results, default=str), mimetype="application/json")
    except ValueError as ve:
        return func.HttpResponse(str(ve), status_code=500) # For config errors
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        return func.HttpResponse("An internal server error occurred.", status_code=500)


