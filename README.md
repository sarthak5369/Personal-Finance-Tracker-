# Personal Finance Tracker 

A web-based Personal Finance Tracker built with Python, Flask, and MySQL to help users manage their income and expenses. The application provides user authentication, transaction management, and a simple interface for tracking personal finances.

##  Features

- User Authentication:** Register and log in securely.
- Transaction Management:** Add and manage income and expense transactions.
- Financial Dashboard:** View financial information through a dashboard.
- MySQL Database:** Store user accounts and transaction records.
- Password Security:** Passwords are stored as hashes instead of plain text.
- REST API:** Includes API endpoints for accessing application data.

##  Technologies Used

- Backend: Python, Flask
- Database: MySQL
- ORM: Flask-SQLAlchemy
- Authentication: Flask-Login
- Frontend: HTML, CSS, JavaScript
- Database Tool: MySQL Workbench
- Development Tool: Visual Studio Code

##  Project Structure

```text
personal-finance-tracker/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── templates/
    ├── landing.html
    ├── dashboard.html
    ├── login.html
    ├── register.html
    ├── transactions.html
    └── transaction_form.html
```

##  Installation and Setup

 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd personal-finance-tracker
```

2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate
```

3. Install Dependencies

```bash
pip install -r requirements.txt
pip install PyMySQL
```

4. Configure MySQL

Open MySQL Workbench and execute:

```sql
CREATE DATABASE IF NOT EXISTS penny_pilot;
```

Make sure your MySQL server is running.

 5. Configure Environment Variables

In the VS Code PowerShell terminal, set your database connection:

```powershell
$env:DATABASE_URL = "mysql+pymysql://root:YOUR_PASSWORD@localhost/penny_pilot"
$env:SECRET_KEY = "replace-with-a-secure-secret-key"
```

Replace `YOUR_PASSWORD` with your own MySQL password. Never upload real passwords or secret keys to GitHub.

### 6. Run the Application

```bash
python app.py
```

Open your browser and visit:

http://127.0.0.1:5000/

##  Database

The application uses MySQL to store its data in the following tables:

- **user:** Stores registered user information.
- **transaction:** Stores financial transaction records.

Database tables are created by the application when configured correctly.

##  Testing

The application was manually tested for:

- User registration and login.
- Adding financial transactions.
- Saving and retrieving data from MySQL.

##  Future Improvements

- Interactive financial charts.
- Monthly and category-wise spending analysis.
- Transaction search and filtering.
- Budget limits and spending alerts.
- Export financial reports to CSV.

##  Author

Sarthak Negi


