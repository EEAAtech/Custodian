import logging
import json
import os
import pyodbc
from azure.functions import func

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function to fetch budget report data by calling a stored procedure.
    """
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
        budget_name = req_body.get('budgetName')
        amount_flag = req_body.get('amountFlag')
        start_date = req_body.get('startDate')
        end_date = req_body.get('endDate')

        if not all([budget_name, amount_flag, start_date, end_date]):
            return func.HttpResponse(
                "Missing required parameters in request body.",
                status_code=400
            )

        # Get connection string from environment variables
        conn_str = os.environ.get("SqlConnectionString")
        if not conn_str:
            logging.error("SqlConnectionString not found in environment settings.")
            return func.HttpResponse("Server configuration error.", status_code=500)

        results = []
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            # Parameters for the stored procedure
            params = (budget_name, amount_flag, start_date, end_date)
            
            # Note: The syntax for calling a stored procedure can vary by driver
            # This syntax is common for SQL Server
            sql_exec = "{CALL dbo.usp_GetMonthlyBudgetReport(?, ?, ?, ?)}"
            cursor.execute(sql_exec, params)
            
            # Fetch column names from the cursor description
            columns = [column[0] for column in cursor.description]
            
            # Fetch all rows and create a list of dictionaries
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

        # Return the results as a JSON response
        return func.HttpResponse(
            json.dumps(results, default=str), # Use default=str to handle dates/decimals
            mimetype="application/json"
        )

    except json.JSONDecodeError:
        return func.HttpResponse("Invalid JSON format in request body.", status_code=400)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return func.HttpResponse("An internal server error occurred.", status_code=500)
