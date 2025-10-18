
        document.addEventListener('DOMContentLoaded', function () {
            const reportForm = document.getElementById('reportForm');
            const customDatePickers = document.getElementById('customDatePickers');
            const dateRangeRadios = document.querySelectorAll('input[name="dateRangeType"]');
            
            // Show/hide custom date pickers based on radio selection
            dateRangeRadios.forEach(radio => {
                radio.addEventListener('change', function () {
                    customDatePickers.style.display = this.value === 'custom' ? 'flex' : 'none';
                });
            });

            reportForm.addEventListener('submit', async function (e) {
                e.preventDefault();

                const loader = document.getElementById('loader');
                const resultsContainer = document.getElementById('resultsContainer');
                const errorMessage = document.getElementById('errorMessage');

                loader.style.display = 'block';
                resultsContainer.innerHTML = '';
                errorMessage.style.display = 'none';

                // 1. Get user inputs
                const budgetName = document.getElementById('budgetName').value;
                const amountFlag = document.querySelector('input[name="amountFlag"]:checked').value;
                const dateRangeType = document.querySelector('input[name="dateRangeType"]:checked').value;

                // 2. Determine date range
                let startDate, endDate;
                const today = new Date();
                today.setHours(0, 0, 0, 0);

                switch (dateRangeType) {
                    case 'calendar':
                        startDate = new Date(today.getFullYear(), 0, 1); // Jan 1st of current year
                        endDate = today;
                        break;
                    case 'financial':
                        const currentMonth = today.getMonth(); // 0-11
                        const currentYear = today.getFullYear();
                        // Financial year in India starts in April (month 3)
                        const financialYearStartYear = currentMonth >= 3 ? currentYear : currentYear - 1;
                        startDate = new Date(financialYearStartYear, 3, 1); // April 1st
                        endDate = today;
                        break;
                    case 'custom':
                        startDate = new Date(document.getElementById('startDate').value);
                        endDate = new Date(document.getElementById('endDate').value);
                        if (isNaN(startDate) || isNaN(endDate) || startDate > endDate) {
                            showError("Invalid custom date range.");
                            loader.style.display = 'none';
                            return;
                        }
                        break;
                }

                // Format dates to YYYY-MM-DD for SQL
                const formatDate = (date) => date.toISOString().split('T')[0];

                // 3. Prepare request body and call API
                const requestBody = {
                    budgetName,
                    amountFlag,
                    startDate: formatDate(startDate),
                    endDate: formatDate(endDate)
                };

                try {
                    const response = await fetch('/api/get_budget_report', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(requestBody)
                    });

                    if (!response.ok) {
                        const errorText = await response.text();
                        throw new Error(`API Error: ${response.status} ${errorText}`);
                    }

                    const data = await response.json();
                    renderTable(data);

                } catch (error) {
                    console.error('Error fetching report:', error);
                    showError('Failed to generate report. Check console for details.');
                } finally {
                    loader.style.display = 'none';
                }
            });

            function renderTable(data) {
                const resultsContainer = document.getElementById('resultsContainer');
                if (!data || data.length === 0 || (data.length === 1 && data[0].Result)) {
                     resultsContainer.innerHTML = `<p class="text-center text-muted">${data[0]?.Result || 'No data found for the selected criteria.'}</p>`;
                    return;
                }

                const table = document.createElement('table');
                table.className = 'table table-striped table-hover table-bordered';
                
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                const headers = Object.keys(data[0]);
                headers.forEach(headerText => {
                    const th = document.createElement('th');
                    th.textContent = headerText;
                    headerRow.appendChild(th);
                });
                thead.appendChild(headerRow);
                table.appendChild(thead);

                const tbody = document.createElement('tbody');
                data.forEach((rowData, index) => {
                    const row = document.createElement('tr');
                    // Add a special class for the "Total" row
                    if (rowData.Month === 'Total') {
                        row.classList.add('total-row');
                    }
                    headers.forEach(header => {
                        const cell = document.createElement('td');
                        let value = rowData[header];
                        // Format numbers to 2 decimal places if they are numeric
                        if (header !== 'Month' && typeof value === 'number') {
                             cell.textContent = parseFloat(value).toFixed(2);
                        } else {
                            cell.textContent = value;
                        }
                        row.appendChild(cell);
                    });
                    tbody.appendChild(row);
                });
                table.appendChild(tbody);

                resultsContainer.appendChild(table);
            }
            
            function showError(message) {
                const errorMessage = document.getElementById('errorMessage');
                errorMessage.textContent = message;
                errorMessage.style.display = 'block';
            }
        });
    