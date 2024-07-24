# BeeMoto Sales and Inventory Tracker
## Overview
BeeMoto Sales and Inventory Tracker is a web application designed to help manage the sales and inventory of motorbike spares. This application allows users to track sales, manage inventory, and generate various reports for daily,weekly, monthly, and yearly totals.
## Features
- **User Authentication:**
    - Secure login and registration system.
    - Restrict access to certain features based on user role (admin or employee)
- **Sales Management:**
    - Add sales records
    - View sales history and transaction details
    - Update inventory levels automatically after each sale
- **Inventory Management:**
    - Add new inventory items
    - Update existing inventory
    - Remove items from the inventory
    - View current stock levels.
- **Search Functionality:**
    - Search for spare parts by name or ID
    - Display search results in alphabetical order
- **Reporting:**
    - Get daily, weekly, monthly, and yearly totals for sales.
- **Low Stock Alerts:**
    - Identify items with low stock levels to prevent inventory shortages.
## Technology Stack
- Backend:
  - Python 3.x 
  - Flask
  - Flask-Login (for user authentication)
  - SQLite
  - Werkzeug (for password hashing)
- Frontend:
  - HTML5
  - JavaScript
  - Tailwind CSS (via CDN)

## Installation

1. Clone the repository:
``` console
git clone https://github.com/BilhaNanetia/sales-and-inventory.git
cd sales-and-inventory
```
2. Set up a virtual environment:
```console
python -m venv venv
source venv/bin/activate 
```
3. Install the required packages:
``` console
pip install -r requirements.txt
```
4. Navigate to the backend directory:
``` console
cd backend
```
- Since the database is already setup,

5. Run the Flask application:
``` console
python app.py
```
6. Open a web browser and go to `http://localhost:5000` to access the application.

## Usage
1. **Sign Up / Login:**
- New users can sign up for an account on the signup page.
- Existing users can log in on the login page.
2. **Adding a Sale:**
- Search for an item by name or select an item from the drop down and fill in the quantity.**You can only add a sale of an item that has been added to the inventory.**
- Click "Add Sale" to record the transaction.
3. **Viewing Daily Sales:**
- Select a date in the "View Daily Sales" section.
- Click "View Sales" to see a list of all sales for that day.
4. **Viewing Daily Total:**
- Select a date in the "Get Daily Total" section.
- Click "Get Total" to see the total sales for that day.
5. **Deleting a sale:**
- Click "Delete" to delete a sale in the "View Daily Sales" section.
6. **Viewing Weekly Total:**
- Select a date in the "Get Weekly Total" section.
- **The system calculates the total for the 7-day period starting from the selected date**
- Click "Get Weekly Total" to see the total for the 7-day period
7. **Viewing Monthly Total:**
- Select month and year in the "Get Monthly Total" section
- Click "Get Monthly Total" to see the total sales for that month
8. **Viewing Yearly Total:**
- Select year in the "Get Yearly Total" section
- Click "Get Yearly Total" to see the total sales for that year
9. **Add inventory Item:**
-  Add new items to the inventory with name, quantity, and price.
10. **View Current Inventory:**
- See a list of all inventory items.
11. **Deleting an inventory item:**
- Click "Delete" to delete an inventory item in the "Current Inventory" section.
12. **Check Low Stock:**
- Identify items that are running low;items that are less than or equal to 10 in quantity
13. **Logout:**
- Click the "Logout" button in the top-right corner to end your session.
### Employee Access
**Note:** As an employee, you only have access to the following features:

* Processing sales
* Viewing sales history
* Deleting  sales
* Viewing inventory
* Checking low stock

You do not have access to the following features:

* Managing inventory (adding, removing, or updating items)
* Generating reports of daily,monthly or yearly sales

If you need access to these features, please contact your manager or administrator.

### Manager/ Administrator Access

As a manager or administrator, you have access to all features,
## Database
The system uses an SQLite database (`sales_record.db`) to store sales records and user information. The database is automatically created when you run the initialization script.
- **Note:** If you want to create a new admin;
```console
cd backend
python init_db.py
```
## Security
- User passwords are hashed using Werkzeug's security features before being stored in the database.
- Flask-Login is used to manage user sessions securely.
- All main features require user authentication to access.
## Customization
- To change the background image, replace the file at `frontend/static/images/motorbike-2893991_1920.jpg` with your desired image.
- Modify the Tailwind classes in `index.html` to adjust the styling.
- Additional custom styles can be added to `frontend/static/styles.css`.
## Contributing
Contributions to this project are welcome. Please follow these steps:
1. Fork the repository
2. Create a new branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request
## License
This project is licensed under the MIT License - see the LICENSE file for details.
## Acknowledgments
- Pixabay for background images
- Tailwind CSS for the styling framework
- Flask community for the excellent web framework
## Contact
Feel free to contact me through  bilhaleposo@gmail.com

Project Link: [https://github.com/BilhaNanetia/sales-and-inventory]   (https://github.com/BilhaNanetia/sales-and-inventory)
