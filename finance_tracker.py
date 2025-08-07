import sys
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLineEdit, 
                            QPushButton, QTableWidget, QTableWidgetItem, 
                            QComboBox, QHBoxLayout, QLabel, QFormLayout, 
                            QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt

# Constants
FORMAT = "%d-%m-%Y"
COLUMNS = ["Date", "Amount", "Category", "Description"]
CATEGORIES = ["Income", "Expense", "Investment"]

class Finance:
    FILENAME = "Finance.csv"
    df = pd.DataFrame(columns=COLUMNS)  # Class variable to hold data

    @classmethod
    def initialize(cls):
        try:
            # Read CSV and ensure proper datetime conversion
            cls.df = pd.read_csv(cls.FILENAME)
            if not cls.df.empty:
                cls.df["Date"] = pd.to_datetime(cls.df["Date"], format=FORMAT, errors="coerce")
                cls.df = cls.df.dropna(subset=["Date"])  # Remove rows with invalid dates
                cls.save_data()  # Save cleaned data back to file
        except (FileNotFoundError, pd.errors.EmptyDataError):
            # Create new file with headers if doesn't exist
            cls.df = pd.DataFrame(columns=COLUMNS)
            cls.save_data()

    @classmethod
    def save_data(cls):
        """Save DataFrame to CSV, ensuring proper date formatting"""
        cls.df.to_csv(cls.FILENAME, index=False, date_format=FORMAT)

    @classmethod
    def add_transaction(cls, date, amount, category, description):
        try:
            # Validate inputs
            datetime.strptime(date, FORMAT)  # Will raise ValueError if invalid
            amount = float(amount)
            if category not in CATEGORIES:
                raise ValueError("Invalid category")
            
            # Add to DataFrame
            new_row = pd.DataFrame([[date, amount, category, description]], 
                                 columns=COLUMNS)
            cls.df = pd.concat([cls.df, new_row], ignore_index=True)
            
            # Convert date to datetime and save
            cls.df["Date"] = pd.to_datetime(cls.df["Date"], format=FORMAT)
            cls.save_data()
            return True
        except ValueError as e:
            print(f"Validation error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

    @classmethod
    def get_transactions(cls, start_date, end_date):
        try:
            s_date = datetime.strptime(start_date, FORMAT)
            e_date = datetime.strptime(end_date, FORMAT)
            mask = (cls.df["Date"] >= s_date) & (cls.df["Date"] <= e_date)
            return cls.df.loc[mask].copy()
        except ValueError:
            return pd.DataFrame()  # Return empty DataFrame on invalid dates

    @classmethod
    def plot_transactions(cls, start_date, end_date):
        try:
            filtered_df = cls.get_transactions(start_date, end_date)
            if filtered_df.empty:
                return False

            totals = filtered_df.groupby("Category")["Amount"].sum().reindex(CATEGORIES, fill_value=0)
            colors = ["green", "red", "blue"]

            fig, axes = plt.subplots(1, 2, figsize=(16, 7))
            
            # Bar chart
            axes[0].bar(CATEGORIES, totals, color=colors, alpha=0.7)
            axes[0].set_title("Transaction Summary")
            axes[0].set_ylabel("Amount")
            axes[0].grid(axis='y', linestyle='--', alpha=0.7)
            
            # Pie chart
            axes[1].pie(totals, labels=CATEGORIES, autopct="%1.1f%%", 
                       startangle=140, colors=colors)
            axes[1].set_title("Transaction Distribution")
            
            plt.tight_layout()
            plt.show()
            return True
        except Exception as e:
            print(f"Plotting error: {e}")
            return False

class FinanceTrackerApp(QWidget):
    def __init__(self):
        super().__init__()
        Finance.initialize()  # Initialize data
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Personal Finance Tracker")
        self.setGeometry(400, 150, 800, 600)
        
        # Main layout
        self.layout = QVBoxLayout()
        
        # Title
        self.title_label = QLabel("Finance Tracker")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        # Form inputs
        form_layout = QFormLayout()
        self.date_input = QLineEdit(placeholderText="DD-MM-YYYY")
        self.amount_input = QLineEdit(placeholderText="0.00")
        self.category_input = QComboBox()
        self.category_input.addItems(CATEGORIES)
        self.description_input = QLineEdit(placeholderText="Description")
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Transaction")
        self.view_button = QPushButton("View Transactions")
        self.plot_button = QPushButton("Generate Report")
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.setStyleSheet("QTableWidget { font-size: 12px; }")
        
        # Assemble UI
        form_layout.addRow("Date:", self.date_input)
        form_layout.addRow("Amount:", self.amount_input)
        form_layout.addRow("Category:", self.category_input)
        form_layout.addRow("Description:", self.description_input)
        
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.view_button)
        buttons_layout.addWidget(self.plot_button)
        
        self.layout.addWidget(self.title_label)
        self.layout.addLayout(form_layout)
        self.layout.addLayout(buttons_layout)
        self.layout.addWidget(self.table)
        
        self.setLayout(self.layout)
        
        # Connect signals
        self.add_button.clicked.connect(self.add_transaction)
        self.view_button.clicked.connect(self.view_transactions)
        self.plot_button.clicked.connect(self.plot_transactions)

    def add_transaction(self):
        date = self.date_input.text()
        amount = self.amount_input.text()
        category = self.category_input.currentText()
        description = self.description_input.text()

        if not all([date, amount, description]):
            QMessageBox.warning(self, "Error", "All fields are required!")
            return

        if Finance.add_transaction(date, amount, category, description):
            self.clear_inputs()
            QMessageBox.information(self, "Success", "Transaction added successfully!")
        else:
            QMessageBox.warning(self, "Error", "Invalid transaction data. Please check your inputs.")

    def view_transactions(self):
        start_date, ok1 = QInputDialog.getText(self, "Start Date", 
                                              "Enter start date (DD-MM-YYYY):")
        if not ok1: return
        
        end_date, ok2 = QInputDialog.getText(self, "End Date", 
                                            "Enter end date (DD-MM-YYYY):")
        if not ok2: return

        transactions = Finance.get_transactions(start_date, end_date)
        self.update_table(transactions)

    def plot_transactions(self):
        start_date, ok1 = QInputDialog.getText(self, "Start Date", 
                                             "Enter start date (DD-MM-YYYY):")
        if not ok1: return
        
        end_date, ok2 = QInputDialog.getText(self, "End Date", 
                                           "Enter end date (DD-MM-YYYY):")
        if not ok2: return

        if not Finance.plot_transactions(start_date, end_date):
            QMessageBox.warning(self, "Error", "No valid transactions found in this date range.")

    def update_table(self, df):
        self.table.setRowCount(len(df))
        for i, row in df.iterrows():
            self.table.setItem(i, 0, QTableWidgetItem(row["Date"].strftime(FORMAT)))
            self.table.setItem(i, 1, QTableWidgetItem(f"{row['Amount']:.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(row["Category"]))
            self.table.setItem(i, 3, QTableWidgetItem(row["Description"]))

    def clear_inputs(self):
        self.date_input.clear()
        self.amount_input.clear()
        self.category_input.setCurrentIndex(0)
        self.description_input.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FinanceTrackerApp()
    window.show()
    sys.exit(app.exec_())