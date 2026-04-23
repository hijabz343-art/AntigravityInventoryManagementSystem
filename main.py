import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib

# --- Database Setup ---
def setup_database():
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    
    # Create Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL
    )
    ''')
    
    # Create Products Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        sku TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        description TEXT,
        unit_price REAL,
        stock_level INTEGER DEFAULT 0,
        threshold INTEGER DEFAULT 10
    )
    ''')
    
    # Create default admin user if not exists
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        hashed_pw = hashlib.sha256('aadmin'.encode()).hexdigest()
        cursor.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                       ('admin', hashed_pw, 'Admin'))
    
    conn.commit()
    conn.close()

# --- Main Application Class ---
class InventorySystem(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Antigravity Inventory Management System")
        self.geometry("1000x600")
        self.configure(bg="#f4f6f9")
        
        # Apply some styles
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#f4f6f9')
        self.style.configure('Sidebar.TFrame', background='#2c3e50')
        self.style.configure('Sidebar.TButton', background='#34495e', foreground='white', font=('Arial', 11, 'bold'), borderwidth=0)
        self.style.map('Sidebar.TButton', background=[('active', '#1abc9c')])
        self.style.configure('Header.TLabel', font=('Arial', 16, 'bold'), background='#f4f6f9', foreground='#2c3e50')
        
        self.current_user = None
        
        self.frames = {}
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        
        self.show_login_screen()

    def show_login_screen(self):
        # Clear container
        for widget in self.container.winfo_children():
            widget.destroy()
            
        login_frame = ttk.Frame(self.container)
        login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(login_frame, text="Antigravity IMS Login", font=('Arial', 20, 'bold')).pack(pady=20)
        
        ttk.Label(login_frame, text="Username:").pack(anchor="w")
        self.username_entry = ttk.Entry(login_frame, width=30)
        self.username_entry.pack(pady=5)
        
        ttk.Label(login_frame, text="Password:").pack(anchor="w")
        self.password_entry = ttk.Entry(login_frame, show="*", width=30)
        self.password_entry.pack(pady=5)
        
        ttk.Button(login_frame, text="Login", command=self.authenticate).pack(pady=20)
        ttk.Label(login_frame, text="Default: admin / admin123", foreground="gray").pack()

    def authenticate(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
            
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, role FROM users WHERE username=? AND password_hash=?', (username, hashed_pw))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            self.current_user = {'id': user[0], 'username': user[1], 'role': user[2]}
            self.build_main_layout()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def build_main_layout(self):
        for widget in self.container.winfo_children():
            widget.destroy()
            
        # Sidebar
        sidebar = ttk.Frame(self.container, style='Sidebar.TFrame', width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        ttk.Label(sidebar, text=f"Welcome, {self.current_user['username']}", background='#2c3e50', foreground='white', font=('Arial', 12)).pack(pady=20)
        
        # Navigation Buttons
        ttk.Button(sidebar, text="Dashboard", style='Sidebar.TButton', command=lambda: self.show_frame("Dashboard")).pack(fill="x", pady=5, padx=10)
        ttk.Button(sidebar, text="Products", style='Sidebar.TButton', command=lambda: self.show_frame("Products")).pack(fill="x", pady=5, padx=10)
        ttk.Button(sidebar, text="Stock Adjustment", style='Sidebar.TButton', command=lambda: self.show_frame("Stock")).pack(fill="x", pady=5, padx=10)
        
        if self.current_user['role'] == 'Admin':
            ttk.Button(sidebar, text="Users", style='Sidebar.TButton', command=lambda: self.show_frame("Users")).pack(fill="x", pady=5, padx=10)
            
        ttk.Button(sidebar, text="Logout", style='Sidebar.TButton', command=self.logout).pack(side="bottom", fill="x", pady=20, padx=10)
        
        # Main Content Area
        self.content_area = ttk.Frame(self.container)
        self.content_area.pack(side="right", fill="both", expand=True)
        
        self.frames["Dashboard"] = DashboardFrame(self.content_area, self)
        self.frames["Products"] = ProductsFrame(self.content_area, self)
        self.frames["Stock"] = StockFrame(self.content_area, self)
        if self.current_user['role'] == 'Admin':
            self.frames["Users"] = UsersFrame(self.content_area, self)
            
        self.show_frame("Dashboard")

    def show_frame(self, frame_name):
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[frame_name].pack(fill="both", expand=True)
        self.frames[frame_name].refresh_data()

    def logout(self):
        self.current_user = None
        self.show_login_screen()

class DashboardFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        ttk.Label(self, text="Dashboard", style='Header.TLabel').pack(pady=20, padx=20, anchor="w")
        
        self.stats_frame = ttk.Frame(self)
        self.stats_frame.pack(fill="x", padx=20)
        
        self.total_products_var = tk.StringVar()
        self.low_stock_var = tk.StringVar()
        
        self.create_stat_card("Total Products", self.total_products_var)
        self.create_stat_card("Low Stock Alerts", self.low_stock_var)
        
        ttk.Label(self, text="Low Stock Items:", font=('Arial', 12, 'bold')).pack(anchor="w", padx=20, pady=(20,5))
        
        self.tree = ttk.Treeview(self, columns=('SKU', 'Name', 'Stock', 'Threshold'), show='headings')
        self.tree.heading('SKU', text='SKU')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Stock', text='Current Stock')
        self.tree.heading('Threshold', text='Threshold')
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)

    def create_stat_card(self, title, string_var):
        card = ttk.Frame(self.stats_frame, relief="ridge", padding=20)
        card.pack(side="left", padx=(0, 20))
        ttk.Label(card, text=title, font=('Arial', 10)).pack()
        ttk.Label(card, textvariable=string_var, font=('Arial', 18, 'bold')).pack(pady=5)

    def refresh_data(self):
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM products")
        self.total_products_var.set(str(cursor.fetchone()[0]))
        
        cursor.execute("SELECT sku, name, stock_level, threshold FROM products WHERE stock_level <= threshold")
        low_stock_items = cursor.fetchall()
        self.low_stock_var.set(str(len(low_stock_items)))
        
        # Clear treeview
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        # Populate treeview
        for item in low_stock_items:
            self.tree.insert('', 'end', values=item)
            
        conn.close()

class ProductsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=20, pady=20)
        
        ttk.Label(header_frame, text="Product Management", style='Header.TLabel').pack(side="left")
        ttk.Button(header_frame, text="Add New Product", command=self.add_product).pack(side="right")
        
        self.tree = ttk.Treeview(self, columns=('SKU', 'Name', 'Category', 'Price', 'Stock'), show='headings')
        self.tree.heading('SKU', text='SKU')
        self.tree.heading('Name', text='Name')
        self.tree.heading('Category', text='Category')
        self.tree.heading('Price', text='Price')
        self.tree.heading('Stock', text='Stock')
        self.tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tree.bind("<Double-1>", self.on_double_click)

    def refresh_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
            
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT sku, name, category, unit_price, stock_level FROM products")
        for item in cursor.fetchall():
            self.tree.insert('', 'end', values=item)
        conn.close()

    def add_product(self):
        self.open_product_form("Add Product")

    def on_double_click(self, event):
        item = self.tree.selection()
        if not item: return
        sku = self.tree.item(item[0], "values")[0]
        self.open_product_form("Edit Product", sku)

    def open_product_form(self, title, sku=None):
        top = tk.Toplevel(self)
        top.title(title)
        top.geometry("400x400")
        
        ttk.Label(top, text="SKU:").pack(anchor="w", padx=20, pady=(10,0))
        sku_entry = ttk.Entry(top)
        sku_entry.pack(fill="x", padx=20)
        
        ttk.Label(top, text="Name:").pack(anchor="w", padx=20, pady=(10,0))
        name_entry = ttk.Entry(top)
        name_entry.pack(fill="x", padx=20)
        
        ttk.Label(top, text="Category:").pack(anchor="w", padx=20, pady=(10,0))
        category_entry = ttk.Entry(top)
        category_entry.pack(fill="x", padx=20)
        
        ttk.Label(top, text="Unit Price:").pack(anchor="w", padx=20, pady=(10,0))
        price_entry = ttk.Entry(top)
        price_entry.pack(fill="x", padx=20)
        
        ttk.Label(top, text="Low Stock Threshold:").pack(anchor="w", padx=20, pady=(10,0))
        threshold_entry = ttk.Entry(top)
        threshold_entry.pack(fill="x", padx=20)
        
        if sku:
            sku_entry.insert(0, sku)
            sku_entry.config(state="readonly")
            
            conn = sqlite3.connect('inventory.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name, category, unit_price, threshold FROM products WHERE sku=?", (sku,))
            prod = cursor.fetchone()
            conn.close()
            
            if prod:
                name_entry.insert(0, prod[0])
                category_entry.insert(0, prod[1] if prod[1] else "")
                price_entry.insert(0, prod[2] if prod[2] else "")
                threshold_entry.insert(0, str(prod[3]))

        def save():
            v_sku = sku_entry.get()
            v_name = name_entry.get()
            v_cat = category_entry.get()
            try:
                v_price = float(price_entry.get() or 0.0)
            except ValueError:
                v_price = 0.0
            try:
                v_thresh = int(threshold_entry.get() or 10)
            except ValueError:
                v_thresh = 10
            
            conn = sqlite3.connect('inventory.db')
            cursor = conn.cursor()
            try:
                if sku:
                    cursor.execute("UPDATE products SET name=?, category=?, unit_price=?, threshold=? WHERE sku=?", 
                                   (v_name, v_cat, v_price, v_thresh, v_sku))
                else:
                    cursor.execute("INSERT INTO products (sku, name, category, unit_price, threshold) VALUES (?, ?, ?, ?, ?)", 
                                   (v_sku, v_name, v_cat, v_price, v_thresh))
                conn.commit()
                top.destroy()
                self.refresh_data()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "SKU already exists!", parent=top)
            finally:
                conn.close()

        ttk.Button(top, text="Save", command=save).pack(pady=20)
        if sku:
            def delete():
                if messagebox.askyesno("Confirm", f"Delete {sku}?", parent=top):
                    conn = sqlite3.connect('inventory.db')
                    conn.cursor().execute("DELETE FROM products WHERE sku=?", (sku,))
                    conn.commit()
                    conn.close()
                    top.destroy()
                    self.refresh_data()
            ttk.Button(top, text="Delete", command=delete).pack()

class StockFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        ttk.Label(self, text="Stock Adjustment / Scanning", style='Header.TLabel').pack(pady=20, padx=20, anchor="w")
        
        scan_frame = ttk.Frame(self)
        scan_frame.pack(fill="x", padx=20)
        
        ttk.Label(scan_frame, text="Scan/Enter SKU:").pack(side="left")
        self.sku_entry = ttk.Entry(scan_frame)
        self.sku_entry.pack(side="left", padx=10)
        self.sku_entry.bind("<Return>", self.lookup_product)
        
        ttk.Button(scan_frame, text="Lookup", command=self.lookup_product).pack(side="left")
        
        self.detail_frame = ttk.Frame(self, padding=20)
        self.detail_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.current_sku_var = tk.StringVar()
        self.current_name_var = tk.StringVar()
        self.current_stock_var = tk.StringVar()
        
        ttk.Label(self.detail_frame, text="Product Name:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(self.detail_frame, textvariable=self.current_name_var, font=('Arial', 10, 'bold')).grid(row=0, column=1, sticky="w", pady=5)
        
        ttk.Label(self.detail_frame, text="Current Stock:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Label(self.detail_frame, textvariable=self.current_stock_var, font=('Arial', 10, 'bold')).grid(row=1, column=1, sticky="w", pady=5)
        
        ttk.Label(self.detail_frame, text="Adjustment Quantity:").grid(row=2, column=0, sticky="w", pady=15)
        self.adj_qty = ttk.Entry(self.detail_frame, width=10)
        self.adj_qty.grid(row=2, column=1, sticky="w", pady=15)
        
        btn_frame = ttk.Frame(self.detail_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Receive Stock (+)", command=lambda: self.adjust_stock(1)).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Dispatch Stock (-)", command=lambda: self.adjust_stock(-1)).pack(side="left", padx=5)

    def refresh_data(self):
        self.sku_entry.delete(0, 'end')
        self.current_sku_var.set("")
        self.current_name_var.set("")
        self.current_stock_var.set("")
        self.adj_qty.delete(0, 'end')

    def lookup_product(self, event=None):
        sku = self.sku_entry.get()
        if not sku: return
        
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT sku, name, stock_level FROM products WHERE sku=?", (sku,))
        prod = cursor.fetchone()
        conn.close()
        
        if prod:
            self.current_sku_var.set(prod[0])
            self.current_name_var.set(prod[1])
            self.current_stock_var.set(str(prod[2]))
            self.adj_qty.focus()
        else:
            messagebox.showinfo("Not Found", "Product SKU not found.")
            self.refresh_data()

    def adjust_stock(self, multiplier):
        sku = self.current_sku_var.get()
        if not sku: return
        
        try:
            qty = int(self.adj_qty.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for quantity.")
            return
            
        change = qty * multiplier
        
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET stock_level = stock_level + ? WHERE sku=?", (change, sku))
        conn.commit()
        
        cursor.execute("SELECT stock_level FROM products WHERE sku=?", (sku,))
        new_stock = cursor.fetchone()[0]
        conn.close()
        
        self.current_stock_var.set(str(new_stock))
        self.adj_qty.delete(0, 'end')
        messagebox.showinfo("Success", f"Stock adjusted successfully. New stock: {new_stock}")

class UsersFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        ttk.Label(self, text="User Management (Admin Only)", style='Header.TLabel').pack(pady=20, padx=20, anchor="w")
        ttk.Label(self, text="This feature is coming soon!").pack(padx=20, anchor="w")

    def refresh_data(self):
        pass

if __name__ == "__main__":
    setup_database()
    app = InventorySystem()
    app.mainloop()
