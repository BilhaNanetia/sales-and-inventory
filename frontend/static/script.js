// Utility function to handle errors
function handleError(error, message) {
    console.error('Error:', error);
    alert(message || 'An unknown error occurred.');
}

// Utility function to process responses
function processResponse(response) {
    if (!response.ok) {
        return response.json().then(err => Promise.reject(err));
    }
    return response.json();
}

// Add event listener for adding a sale
document.getElementById('addSaleForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const itemId = parseInt(document.getElementById('item').value);
    const quantity = parseInt(document.getElementById('quantity').value);

    if (isNaN(itemId) || isNaN(quantity)) {
        return alert('Please select an item and enter a valid quantity.');
    }

    fetch('/add_sale', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId, quantity })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Sale added successfully!');
            this.reset();
            loadInventory(); // Refresh the inventory
        } else {
            if (data.error.includes('Insufficient stock')) {
                // Extract the available quantity from the error message
                const match = data.error.match(/Available: (\d+)/);
                const availableQuantity = match ? match[1] : 'unknown';
                alert(`Error adding sale: Insufficient stock. Available quantity: ${availableQuantity}`);
            } else {
                alert('Error adding sale: ' + data.error);
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while adding the sale.');
    });
});
// Add event listener for getting daily total sales
document.getElementById('getDailyTotalForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const date = document.getElementById('totalDate').value;

    fetch(`/get_daily_total?date=${date}`)
    .then(response => response.json())
    .then(data => {
        document.getElementById('dailyTotal').textContent = `Total sales for ${date}: KES ${data.total.toFixed(2)}`;
    })
    .catch(error => handleError(error, 'An error occurred while fetching daily total.'));
});

// Add event listener for getting daily sales
document.getElementById('getDailySalesForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const date = document.getElementById('salesDate').value;

    fetch(`/get_daily_sales?date=${date}`)
    .then(response => response.json())
    .then(data => {
        const salesList = document.getElementById('dailySales');
        salesList.innerHTML = '';
        data.sales.forEach((sale, index) => {
            const li = document.createElement('li');
            li.className = 'bg-gray-100 p-3 rounded mb-2 flex justify-between items-center';
            li.innerHTML = `
                <span>${index + 1}. Item: ${sale.item}, Quantity: ${sale.quantity}, Price: KES ${sale.price.toFixed(2)}</span>
                <button class="delete-btn bg-red-500 text-white px-2 py-1 rounded" data-id="${sale.id}">Delete</button>
            `;
            salesList.appendChild(li);
        });
        document.querySelectorAll('.delete-btn').forEach(btn => btn.addEventListener('click', deleteSale));
    })
    .catch(error => handleError(error, 'An error occurred while fetching daily sales.'));
});

// Function to delete a sale
function deleteSale(e) {
    const saleId = e.target.getAttribute('data-id');
    if (confirm('Are you sure you want to delete this sale?')) {
        fetch('/delete_sale', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: saleId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Sale deleted successfully!');
                document.getElementById('getDailySalesForm').dispatchEvent(new Event('submit'));
            } else {
                alert('Error deleting sale: ' + data.error);
            }
        })
        .catch(error => handleError(error, 'An error occurred while deleting the sale.'));
    }
}

// Add event listener for getting monthly total sales
document.getElementById('getMonthlyTotalForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const monthYear = document.getElementById('monthYear').value;
    const [year, month] = monthYear.split('-');

    fetch(`/get_monthly_total?year=${year}&month=${month}`)
    .then(response => response.json())
    .then(data => {
        document.getElementById('monthlyTotal').textContent = `Total sales for ${monthYear}: KES ${data.total.toFixed(2)}`;
    })
    .catch(error => handleError(error, 'An error occurred while fetching monthly total.'));
});

// Add event listener for getting yearly total sales
document.getElementById('getYearlyTotalForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const year = document.getElementById('year').value;

    fetch(`/get_yearly_total?year=${year}`)
    .then(response => response.json())
    .then(data => {
        document.getElementById('yearlyTotal').textContent = `Total sales for ${year}: KES ${data.total.toFixed(2)}`;
    })
    .catch(error => handleError(error, 'An error occurred while fetching yearly total.'));
});

// Add event listener for adding inventory
document.getElementById('addInventoryForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const item = document.getElementById('inventoryItem').value;
    const quantity = parseInt(document.getElementById('inventoryQuantity').value);
    const price = parseFloat(document.getElementById('inventoryPrice').value);

    fetch('/add_inventory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item, quantity, price })
    })
    .then(response => processResponse(response))
    .then(data => {
        if (data.success) {
            alert(data.message);
            this.reset();
            loadInventory();
        } else {
            alert('Error updating inventory: ' + data.error);
        }
    })
    .catch(error => handleError(error, 'An error occurred while updating the inventory item.'));
});

// Function to load inventory
function loadInventory() {
    fetch('/get_inventory')
    .then(response => response.json())
    .then(data => {
        const inventoryList = document.getElementById('inventoryList');
        const itemSelect = document.getElementById('item');
        inventoryList.innerHTML = '';
        itemSelect.innerHTML = '<option value="">Select an item</option>';
        data.items.forEach((item, index) => {
            const li = document.createElement('li');
            li.className = 'bg-gray-100 p-3 rounded mb-2 flex justify-between items-center';
            li.innerHTML = `
                <span>${index + 1}. Item: ${item[1]}, Quantity: ${item[2]}, Price: KES ${item[3].toFixed(2)}</span>
                <button class="delete-inventory-btn bg-red-500 text-white px-2 py-1 rounded" data-id="${item[0]}">Delete</button>
            `;
            inventoryList.appendChild(li);

            const option = document.createElement('option');
            option.value = item[0];
            option.textContent = item[1];
            itemSelect.appendChild(option);
        });
        document.querySelectorAll('.delete-inventory-btn').forEach(btn => btn.addEventListener('click', deleteInventoryItem));
    })
    .catch(error => handleError(error, 'An error occurred while loading the inventory.'));
}

// Function to delete an inventory item
function deleteInventoryItem(e) {
    const itemId = e.target.getAttribute('data-id');
    if (confirm('Are you sure you want to delete this inventory item?')) {
        fetch('/delete_inventory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_id: itemId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Inventory item deleted successfully!');
                loadInventory();
            } else {
                alert('Error deleting inventory item: ' + data.error);
            }
        })
        .catch(error => handleError(error, 'An error occurred while deleting the inventory item.'));
    }
}

// Add event listener for checking low stock
document.getElementById('checkLowStockBtn').addEventListener('click', function() {
    fetch('/check_low_stock')
    .then(response => response.json())
    .then(data => {
        const lowStockList = document.getElementById('lowStockList');
        lowStockList.innerHTML = '';
        data.low_stock_items.forEach((item, index) => {
            const li = document.createElement('li');
            li.className = 'bg-yellow-100 p-3 rounded mb-2';
            li.textContent = `${index + 1}. Item: ${item[1]}, Quantity: ${item[2]}, Price: KES ${item[3].toFixed(2)}`;
            lowStockList.appendChild(li);
        });
    })
    .catch(error => handleError(error, 'An error occurred while checking low stock.'));
});

// Load inventory when the page loads
document.addEventListener('DOMContentLoaded', loadInventory);
