import csv
import os
import datetime
import tkinter as tk
from tkinter import ttk, messagebox


# =======================================================
# DATA MODELS (OOP & POLYMORPHISM)
# =======================================================

class BaseProduct:
    """Base class for all inventory products"""
    def __init__(self, p_id, name, price, stock, category="General", extra_info="N/A"):
        self.p_id = str(p_id).strip()
        self.name = str(name).strip()
        self.price = float(price)
        self.stock = int(stock)
        self.category = category
        self.extra_info = str(extra_info).strip()

    def get_discount_rate(self) -> float:
        """Base discount is 0%"""
        return 0.0

    def get_effective_price(self) -> float:
        """Calculates final price after applied discount"""
        return self.price * (1.0 - self.get_discount_rate())


class PerishableItem(BaseProduct):
    """Product with expiry date checking for dynamic discounts"""
    def __init__(self, p_id, name, price, stock, expiry_date):
        super().__init__(p_id, name, price, stock, "Perishable", expiry_date)

    def get_discount_rate(self) -> float:
        """30% discount if product expires within 3 days"""
        try:
            exp = datetime.datetime.strptime(self.extra_info, "%Y-%m-%d").date()
            days_left = (exp - datetime.date.today()).days
            if 0 <= days_left <= 3:
                return 0.30
        except ValueError:
            pass
        return 0.0


class ElectronicItem(BaseProduct):
    """Product with warranty period and flat discount"""
    def __init__(self, p_id, name, price, stock, warranty_months):
        super().__init__(p_id, name, price, stock, "Electronics", str(warranty_months))

    def get_discount_rate(self) -> float:
        """Flat 10% promotional discount on electronics"""
        return 0.10


# =======================================================
# BUSINESS LOGIC & PERSISTENCE LAYER
# =======================================================

class StoreInventory:
    def __init__(self, filename="inventory.csv"):
        self.filename = filename
        self.items = {}
        self.initialize_csv_if_missing()
        self.load_data()

    def initialize_csv_if_missing(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["id", "name", "price", "stock", "category", "extra_info"])
                writer.writerow(["P101", "Milk 1L", "2.50", "12", "Perishable", "2026-08-05"])
                writer.writerow(["P102", "USB Cable", "15.00", "3", "Electronics", "24"])
                writer.writerow(["P103", "Notebook", "2.00", "50", "General", "N/A"])

    def load_data(self):
        self.items.clear()
        if not os.path.exists(self.filename):
            return
        
        with open(self.filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                p_id = row["id"]
                name = row["name"]
                price = float(row["price"])
                stock = int(row["stock"])
                cat = row.get("category", "General")
                extra = row.get("extra_info", "N/A")

                if cat == "Perishable":
                    obj = PerishableItem(p_id, name, price, stock, extra)
                elif cat == "Electronics":
                    obj = ElectronicItem(p_id, name, price, stock, extra)
                else:
                    obj = BaseProduct(p_id, name, price, stock, "General", extra)

                self.items[p_id] = obj

    def save_data(self):
        with open(self.filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "name", "price", "stock", "category", "extra_info"])
            for item in self.items.values():
                writer.writerow([item.p_id, item.name, f"{item.price:.2f}", item.stock, item.category, item.extra_info])

    def add_or_update_product(self, p_id, name, price, stock, category, extra):
        if not p_id or not name:
            raise ValueError("ID and Name are required fields.")
        
        price_val = float(price)
        stock_val = int(stock)

        if price_val < 0 or stock_val < 0:
            raise ValueError("Price and Stock must be 0 or higher.")

        if category == "Perishable":
            try:
                datetime.datetime.strptime(extra, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Perishable extra info must be a valid date format: YYYY-MM-DD")
            item = PerishableItem(p_id, name, price_val, stock_val, extra)
        elif category == "Electronics":
            if not str(extra).isdigit():
                raise ValueError("Electronics warranty must be an integer (months).")
            item = ElectronicItem(p_id, name, price_val, stock_val, extra)
        else:
            item = BaseProduct(p_id, name, price_val, stock_val, "General", extra if extra else "N/A")

        self.items[p_id] = item
        self.save_data()

    def remove_product(self, p_id):
        if p_id in self.items:
            del self.items[p_id]
            self.save_data()

    def process_checkout(self, cart_dict):
        for p_id, qty in cart_dict.items():
            if p_id in self.items:
                self.items[p_id].stock = max(0, self.items[p_id].stock - qty)
        self.save_data()


def calculate_linear_regression(data_points):
    """Pure Python implementation of Least Squares Linear Regression"""
    n = len(data_points)
    if n < 2:
        return 0.0

    X = list(range(1, n + 1))
    Y = data_points

    sum_x = sum(X)
    sum_y = sum(Y)
    sum_xy = sum(x * y for x, y in zip(X, Y))
    sum_x2 = sum(x ** 2 for x in X)

    denom = (n * sum_x2 - (sum_x ** 2))
    if denom == 0:
        return round(sum_y / n, 2)

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n

    prediction = slope * (n + 1) + intercept
    return max(0.0, round(prediction, 2))


# =======================================================
# USER INTERFACE (TKINTER GUI)
# =======================================================

class RetailAppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RetailPro - Management System")
        self.root.geometry("1050x680")

        self.inventory = StoreInventory()
        self.cart = {}
        self.low_stock_warning_shown = False

        self.setup_ui()
        self.refresh_inventory_display()

    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#1e293b", height=50)
        header.pack(fill=tk.X)
        tk.Label(header, text="RetailPro POS & Inventory System", font=("Segoe UI", 16, "bold"), fg="white", bg="#1e293b").pack(pady=10)

        # Tabs
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_pos = ttk.Frame(self.tabs)
        self.tab_forecast = ttk.Frame(self.tabs)

        self.tabs.add(self.tab_pos, text=" Operations & Sales ")
        self.tabs.add(self.tab_forecast, text=" Demand Forecasting ")

        self.build_pos_tab()
        self.build_forecast_tab()

    def build_pos_tab(self):
        # Left Panel (Inputs & Controls)
        left = ttk.LabelFrame(self.tab_pos, text=" Product & Cart Controls ", padding=10)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        ttk.Label(left, text="Product ID:").grid(row=0, column=0, sticky="w", pady=3)
        self.txt_id = ttk.Entry(left, width=18)
        self.txt_id.grid(row=0, column=1, pady=3)

        ttk.Label(left, text="Product Name:").grid(row=1, column=0, sticky="w", pady=3)
        self.txt_name = ttk.Entry(left, width=18)
        self.txt_name.grid(row=1, column=1, pady=3)

        ttk.Label(left, text="Price ($):").grid(row=2, column=0, sticky="w", pady=3)
        self.txt_price = ttk.Entry(left, width=18)
        self.txt_price.grid(row=2, column=1, pady=3)

        ttk.Label(left, text="Stock Qty:").grid(row=3, column=0, sticky="w", pady=3)
        self.txt_stock = ttk.Entry(left, width=18)
        self.txt_stock.grid(row=3, column=1, pady=3)

        ttk.Label(left, text="Category:").grid(row=4, column=0, sticky="w", pady=3)
        self.cmb_cat = ttk.Combobox(left, values=["General", "Perishable", "Electronics"], width=15, state="readonly")
        self.cmb_cat.current(0)
        self.cmb_cat.grid(row=4, column=1, pady=3)

        ttk.Label(left, text="Extra Info:\n(Expiry/Warranty)").grid(row=5, column=0, sticky="w", pady=3)
        self.txt_extra = ttk.Entry(left, width=18)
        self.txt_extra.grid(row=5, column=1, pady=3)

        btn_frame = ttk.Frame(left)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Save Item", command=self.btn_save_item).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Delete Item", command=self.btn_delete_item).pack(side=tk.LEFT, padx=3)

        ttk.Separator(left, orient="horizontal").grid(row=7, column=0, columnspan=2, sticky="ew", pady=10)

        # Cart Section
        ttk.Label(left, text="Checkout Options", font=("Segoe UI", 10, "bold")).grid(row=8, column=0, columnspan=2, pady=2)
        
        ttk.Label(left, text="Purchase Qty:").grid(row=9, column=0, sticky="w", pady=3)
        self.txt_cart_qty = ttk.Entry(left, width=18)
        self.txt_cart_qty.insert(0, "1")
        self.txt_cart_qty.grid(row=9, column=1, pady=3)

        ttk.Button(left, text="+ Add to Cart", command=self.btn_add_to_cart).grid(row=10, column=0, columnspan=2, sticky="ew", pady=4)
        ttk.Button(left, text="🛒 Complete Order & Receipt", command=self.btn_checkout).grid(row=11, column=0, columnspan=2, sticky="ew", pady=2)

        # Right Panel (Treeview & Receipt Canvas)
        right = ttk.Frame(self.tab_pos)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        table_frame = ttk.LabelFrame(right, text=" Current Inventory ", padding=5)
        table_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("ID", "Name", "Price", "Stock", "Category", "Discount", "Extra Info")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=7)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=85, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)

        receipt_frame = ttk.LabelFrame(right, text=" Live Receipt View ", padding=5)
        receipt_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.canvas = tk.Canvas(receipt_frame, bg="white", bd=1, relief="sunken")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def build_forecast_tab(self):
        box = ttk.Frame(self.tab_forecast, padding=15)
        box.pack(fill=tk.BOTH, expand=True)

        ttk.Label(box, text="Linear Regression Demand Forecasting", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=5)
        ttk.Label(box, text="Enter historical sales numbers separated by commas (e.g. 100, 120, 130, 150):").pack(anchor="w", pady=2)

        input_row = ttk.Frame(box)
        input_row.pack(anchor="w", pady=10)

        self.txt_sales_data = ttk.Entry(input_row, width=45)
        self.txt_sales_data.insert(0, "45, 50, 58, 62, 70, 82")
        self.txt_sales_data.pack(side=tk.LEFT, padx=5)

        ttk.Button(input_row, text="Forecast Demand", command=self.btn_run_forecast).pack(side=tk.LEFT)

        self.lbl_forecast_res = tk.Label(box, text="Next Month Estimated Demand: --", font=("Segoe UI", 11, "bold"), fg="#1d4ed8")
        self.lbl_forecast_res.pack(anchor="w", pady=10)

        self.forecast_canvas = tk.Canvas(box, bg="#f8fafc", height=230, bd=1, relief="solid")
        self.forecast_canvas.pack(fill=tk.X, pady=5)

    def refresh_inventory_display(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        low_stock = []
        for item in self.inventory.items.values():
            disc_str = f"{item.get_discount_rate() * 100:.0f}%"
            self.tree.insert("", tk.END, values=(item.p_id, item.name, f"${item.price:.2f}", item.stock, item.category, disc_str, item.extra_info))
            if item.stock <= 5:
                low_stock.append(f"{item.name} ({item.stock} left)")

        if low_stock and not self.low_stock_warning_shown:
            messagebox.showwarning("Stock Alert", "Low stock detected for:\n" + "\n".join(low_stock))
            self.low_stock_warning_shown = True

    def on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        self.txt_id.delete(0, tk.END)
        self.txt_id.insert(0, vals[0])
        self.txt_name.delete(0, tk.END)
        self.txt_name.insert(0, vals[1])
        self.txt_price.delete(0, tk.END)
        self.txt_price.insert(0, vals[2].replace("$", ""))
        self.txt_stock.delete(0, tk.END)
        self.txt_stock.insert(0, vals[3])
        self.cmb_cat.set(vals[4])
        self.txt_extra.delete(0, tk.END)
        self.txt_extra.insert(0, vals[6])

    def btn_save_item(self):
        try:
            self.inventory.add_or_update_product(
                self.txt_id.get(),
                self.txt_name.get(),
                self.txt_price.get(),
                self.txt_stock.get(),
                self.cmb_cat.get(),
                self.txt_extra.get()
            )
            self.refresh_inventory_display()
            messagebox.showinfo("Success", "Product successfully saved!")
        except Exception as err:
            messagebox.showerror("Error", str(err))

    def btn_delete_item(self):
        p_id = self.txt_id.get().strip()
        if p_id in self.inventory.items:
            self.inventory.remove_product(p_id)
            self.refresh_inventory_display()
            messagebox.showinfo("Success", f"Product '{p_id}' removed.")
        else:
            messagebox.showerror("Error", "Product ID not found.")

    def btn_add_to_cart(self):
        p_id = self.txt_id.get().strip()
        if p_id not in self.inventory.items:
            messagebox.showerror("Error", "Select a valid product first.")
            return

        try:
            qty = int(self.txt_cart_qty.get())
            if qty <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive number.")
            return

        item = self.inventory.items[p_id]
        current_cart = self.cart.get(p_id, 0)
        if current_cart + qty > item.stock:
            messagebox.showerror("Stock Error", f"Cannot exceed available stock ({item.stock}).")
            return

        self.cart[p_id] = current_cart + qty
        messagebox.showinfo("Cart Updated", f"Added {qty} x {item.name} to cart.")

    def btn_checkout(self):
        if not self.cart:
            messagebox.showwarning("Cart Empty", "Please add items to cart before checkout.")
            return

        self.canvas.delete("all")
        y = 20
        self.canvas.create_text(180, y, text="=== RETAILPRO RECEIPT ===", font=("Courier", 11, "bold"))
        y += 25

        subtotal = 0.0
        discounts = 0.0

        for p_id, qty in self.cart.items():
            item = self.inventory.items[p_id]
            line_orig = item.price * qty
            eff_price = item.get_effective_price()
            line_disc = (item.price - eff_price) * qty

            subtotal += line_orig
            discounts += line_disc

            self.canvas.create_text(20, y, text=f"{item.name[:15]} x{qty}", anchor="w", font=("Courier", 9))
            self.canvas.create_text(300, y, text=f"${line_orig:.2f}", anchor="e", font=("Courier", 9))
            y += 18

            if line_disc > 0:
                self.canvas.create_text(30, y, text=f"Discount: -${line_disc:.2f}", anchor="w", font=("Courier", 8), fill="green")
                y += 15

        vat = (subtotal - discounts) * 0.10
        grand_total = (subtotal - discounts) + vat

        self.canvas.create_line(10, y, 320, y, dash=(4, 2))
        y += 15
        self.canvas.create_text(20, y, text=f"Subtotal: ${subtotal:.2f}", anchor="w", font=("Courier", 9))
        y += 15
        self.canvas.create_text(20, y, text=f"Discounts: -${discounts:.2f}", anchor="w", font=("Courier", 9))
        y += 15
        self.canvas.create_text(20, y, text=f"VAT (10%): ${vat:.2f}", anchor="w", font=("Courier", 9))
        y += 20
        self.canvas.create_text(20, y, text=f"GRAND TOTAL: ${grand_total:.2f}", anchor="w", font=("Courier", 10, "bold"))

        self.inventory.process_checkout(self.cart)
        self.cart.clear()
        self.refresh_inventory_display()

    def btn_run_forecast(self):
        raw = self.txt_sales_data.get().strip()
        try:
            arr = [float(x.strip()) for x in raw.split(",") if x.strip()]
            if len(arr) < 2:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Input Error", "Enter at least 2 comma-separated numbers.")
            return

        pred = calculate_linear_regression(arr)
        self.lbl_forecast_res.config(text=f"Next Month Estimated Demand: ~{pred} units")

        # Visual Chart Rendering
        self.forecast_canvas.delete("all")
        w, h = 480, 180
        pad = 30
        all_vals = arr + [pred]
        min_v, max_v = min(all_vals), max(all_vals)
        rng = max_v - min_v if max_v != min_v else 1

        step_x = (w - 2 * pad) / len(arr)
        pts = []

        for i, val in enumerate(arr):
            x = pad + i * step_x
            y = h - pad - ((val - min_v) / rng) * (h - 2 * pad)
            pts.append((x, y))
            self.forecast_canvas.create_oval(x-3, y-3, x+3, y+3, fill="blue")
            self.forecast_canvas.create_text(x, y-10, text=str(val), font=("Arial", 8))

        for i in range(len(pts) - 1):
            self.forecast_canvas.create_line(pts[i][0], pts[i][1], pts[pts_idx := i+1][0], pts[pts_idx][1], fill="blue", width=2)

        pred_x = pad + len(arr) * step_x
        pred_y = h - pad - ((pred - min_v) / rng) * (h - 2 * pad)
        self.forecast_canvas.create_oval(pred_x-4, pred_y-4, pred_x+4, pred_y+4, fill="red")
        self.forecast_canvas.create_text(pred_x, pred_y-10, text=f"Pred: {pred}", font=("Arial", 8, "bold"), fill="red")
        self.forecast_canvas.create_line(pts[-1][0], pts[-1][1], pred_x, pred_y, fill="red", dash=(3, 3), width=2)


if __name__ == "__main__":
    root = tk.Tk()
    app = RetailAppGUI(root)
    root.mainloop()