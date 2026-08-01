import datetime as dt
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Class 1: Pet

class Pet:

    VALID_STATUSES = ("Available", "Pending", "Adopted")

    def __init__(self, name, breed, age, status="Available", notes=None):
        self.name = name
        self.breed = breed
        self.age = age
        self.adoption_status = status if status in Pet.VALID_STATUSES else "Available"
        self.behavioral_notes = list(notes) if notes else []

    def add_note(self, note):
        """Append a new behavioral note to this pet's record."""
        self.behavioral_notes.append(note)

    def notes_summary(self):
        return "; ".join(self.behavioral_notes) if self.behavioral_notes else "No notes"

    def to_tuple(self):
        return (self.name, self.breed, self.age, self.adoption_status)

    def to_dict(self):
        return {"name": self.name, "breed": self.breed, "age": self.age,
                "adoption_status": self.adoption_status,
                "behavioral_notes": self.behavioral_notes}

    @classmethod
    def from_dict(cls, data):
        return cls(data["name"], data["breed"], data["age"],
                    data.get("adoption_status", "Available"),
                    data.get("behavioral_notes", []))

    def __str__(self):
        return "{0} ({1}, age {2}) - {3}".format(
            self.name, self.breed, self.age, self.adoption_status)


# Class 2: Donation
class Donation:

    def __init__(self, donor_name, amount, date=None):
        self.donor_name = donor_name
        self.amount = float(amount)
        self.date = date if date else dt.date.today().isoformat()

    def month_key(self):
        """Return the 'YYYY-MM' key used to group donations by month."""
        return self.date[:7]

    def to_dict(self):
        return {"donor_name": self.donor_name, "amount": self.amount, "date": self.date}

    @classmethod
    def from_dict(cls, data):
        return cls(data["donor_name"], data["amount"], data.get("date"))

    def __str__(self):
        return "{0}: ${1} on {2}".format(
            self.donor_name, "{:,.2f}".format(self.amount), self.date)

# Class 3: Volunteer
class Volunteer:

    def __init__(self, name, phone, skills=None):
        self.name = name
        self.phone = phone
        self.skills = list(skills) if skills else []
        self.hours_logged = 0.0

    def log_hours(self, hours):
        self.hours_logged += float(hours)

    def to_dict(self):
        return {"name": self.name, "phone": self.phone, "skills": self.skills,
                "hours_logged": self.hours_logged}

    @classmethod
    def from_dict(cls, data):
        v = cls(data["name"], data.get("phone", ""), data.get("skills", []))
        v.hours_logged = data.get("hours_logged", 0.0)
        return v

    def __str__(self):
        return "{0} ({1}) - {2} hrs".format(
            self.name, ", ".join(self.skills), self.hours_logged)


# Class 4: ShelterManager (data / business logic, no GUI code)
class ShelterManager:
    """
    Owns all shelter data and business logic:
      * self.pets        -> list of Pet objects
      * self.donations   -> list of Donation objects
      * self.volunteers  -> dict {name: Volunteer}
      * FIXED_DONOR_RECORDS -> tuple of tuples: unchanging donor-category
        reference data (name, donor category).
    """

    FIXED_DONOR_RECORDS = (
        ("Alice Johnson", "Monthly Giving Circle"),
        ("Bright Future Foundation", "Corporate Grant"),
        ("Marcus Lee", "Monthly Giving Circle"),
        ("Riverside Veterinary Clinic", "In-Kind Partner"),
        ("Dana Whitfield", "First-Time Donor"),
    )

    SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "shelter_data.json")

    def __init__(self):
        self.pets = []
        self.donations = []
        self.volunteers = {}
        if not self._load_data():
            self._load_sample_data()
            self.save_data()

    def _load_sample_data(self):
        self.add_pet(Pet("Bella", "Pit Bull Mix", 9, "Available",
                          ["Good with kids"]))
        self.add_pet(Pet("Bully", "Pit Bull", 1, "Adopted",
                          ["Loves treats"]))

        for name, category in self.FIXED_DONOR_RECORDS:
            self.add_donation(Donation(name, amount=self._seed_amount(category),
                                        date=self._seed_date(category)))

        self.add_donation(Donation("Alice Johnson", 50.00, "2026-07-02"))
        self.add_donation(Donation("Community Pet Store", 250.00, "2026-06-15"))

        self.add_volunteer(Volunteer("John Smith", "555-0142",
                                      ["Dog walking", "Cleaning"]))
        self.add_volunteer(Volunteer("Tom Holland", "555-0198",
                                      ["Adoption events", "Photography"]))

    @staticmethod
    def _seed_amount(category):
        return {"Monthly Giving Circle": 40.00, "Corporate Grant": 1000.00,
                "In-Kind Partner": 0.00, "First-Time Donor": 25.00}.get(category, 0.0)

    @staticmethod
    def _seed_date(category):
        return {"Monthly Giving Circle": "2026-07-01", "Corporate Grant": "2026-05-20",
                "In-Kind Partner": "2026-07-10", "First-Time Donor": "2026-06-01"}.get(
            category, dt.date.today().isoformat())

    def save_data(self):
        """Write all current pets, donations, and volunteers to disk as JSON."""
        payload = {
            "pets": [p.to_dict() for p in self.pets],
            "donations": [d.to_dict() for d in self.donations],
            "volunteers": [v.to_dict() for v in self.volunteers.values()],
        }
        try:
            with open(self.SAVE_FILE, "w") as f:
                json.dump(payload, f, indent=2)
        except OSError as e:
            print("Warning: could not save shelter data: {0}".format(e))

    def _load_data(self):
        """Load pets/donations/volunteers from disk. Returns True on success,
        False if no save file exists yet (or if it couldn't be read)."""
        if not os.path.exists(self.SAVE_FILE):
            return False
        try:
            with open(self.SAVE_FILE, "r") as f:
                payload = json.load(f)
            self.pets = [Pet.from_dict(p) for p in payload.get("pets", [])]
            self.donations = [Donation.from_dict(d) for d in payload.get("donations", [])]
            self.volunteers = {}
            for v in payload.get("volunteers", []):
                vol = Volunteer.from_dict(v)
                self.volunteers[vol.name] = vol
            return True
        except (OSError, json.JSONDecodeError, KeyError) as e:
            print("Warning: could not load shelter data ({0}); starting fresh.".format(e))
            return False

    def add_pet(self, pet):
        self.pets.append(pet)
        self.save_data()

    def unique_breeds(self):
        return sorted({p.breed for p in self.pets})

    def filter_pets(self, breed="All", status="All"):
        result = self.pets
        if breed and breed != "All":
            result = [p for p in result if p.breed == breed]
        if status and status != "All":
            result = [p for p in result if p.adoption_status == status]
        return result

    def add_donation(self, donation):
        self.donations.append(donation)
        self.save_data()

    def total_donations_by_month(self):
        """Return a dict: {'YYYY-MM': total_amount}."""
        totals = {}
        for d in self.donations:
            key = d.month_key()
            totals[key] = totals.get(key, 0.0) + d.amount
        return totals

    def available_months(self):
        return sorted(self.total_donations_by_month().keys())

    def total_all_donations(self):
        return sum(d.amount for d in self.donations)

    def add_volunteer(self, volunteer):
        self.volunteers[volunteer.name] = volunteer
        self.save_data()

    def log_volunteer_hours(self, name, hours):
        if name in self.volunteers:
            self.volunteers[name].log_hours(hours)
            self.save_data()
            return True
        return False


# Class 5: ShelterInterface  (Tkinter GUI)
class ShelterInterface:

    def __init__(self, root):
        self.root = root
        self.root.title("Humane Society Animal Shelter Management System")
        self.root.geometry("820x520")
        self.manager = ShelterManager()

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.pets_tab = ttk.Frame(notebook)
        self.donations_tab = ttk.Frame(notebook)
        self.volunteers_tab = ttk.Frame(notebook)

        notebook.add(self.pets_tab, text="Adoptable Pets")
        notebook.add(self.donations_tab, text="Donations")
        notebook.add(self.volunteers_tab, text="Volunteers")

        self._build_pets_tab()
        self._build_donations_tab()
        self._build_volunteers_tab()

    # Pets Tab
    def _build_pets_tab(self):
        frame = self.pets_tab

        filter_bar = ttk.Frame(frame)
        filter_bar.pack(fill="x", padx=10, pady=8)

        ttk.Label(filter_bar, text="Breed:").grid(row=0, column=0, padx=4)
        self.breed_var = tk.StringVar(value="All")
        breed_values = ["All"] + self.manager.unique_breeds()
        self.breed_combo = ttk.Combobox(filter_bar, textvariable=self.breed_var,
                                         values=breed_values, state="readonly", width=20)
        self.breed_combo.grid(row=0, column=1, padx=4)

        ttk.Label(filter_bar, text="Status:").grid(row=0, column=2, padx=4)
        self.status_var = tk.StringVar(value="All")
        status_values = ["All"] + list(Pet.VALID_STATUSES)
        self.status_combo = ttk.Combobox(filter_bar, textvariable=self.status_var,
                                          values=status_values, state="readonly", width=15)
        self.status_combo.grid(row=0, column=3, padx=4)

        ttk.Button(filter_bar, text="Apply Filter",
                   command=self.refresh_pets_table).grid(row=0, column=4, padx=8)
        ttk.Button(filter_bar, text="Add Pet",
                   command=self.open_add_pet_dialog).grid(row=0, column=5, padx=4)

        columns = ("name", "breed", "age", "status", "notes")
        self.pets_tree = ttk.Treeview(frame, columns=columns, show="headings", height=14)
        headings = {"name": "Name", "breed": "Breed", "age": "Age",
                    "status": "Status", "notes": "Behavioral Notes"}
        widths = {"name": 100, "breed": 140, "age": 50, "status": 90, "notes": 320}
        for col in columns:
            self.pets_tree.heading(col, text=headings[col])
            self.pets_tree.column(col, width=widths[col], anchor="w")
        self.pets_tree.pack(fill="both", expand=True, padx=10, pady=6)

        self.pets_count_label = ttk.Label(frame, text="")
        self.pets_count_label.pack(anchor="w", padx=10)

        self.refresh_pets_table()

    def refresh_pets_table(self):
        for row in self.pets_tree.get_children():
            self.pets_tree.delete(row)
        filtered = self.manager.filter_pets(self.breed_var.get(), self.status_var.get())
        for pet in filtered:
            self.pets_tree.insert("", "end", values=(
                pet.name, pet.breed, pet.age, pet.adoption_status, pet.notes_summary()))
        self.pets_count_label.config(text="Showing {0} of {1} pets".format(
            len(filtered), len(self.manager.pets)))

    def open_add_pet_dialog(self):
        name = simpledialog.askstring("Add Pet", "Pet name:", parent=self.root)
        if not name:
            return
        breed = simpledialog.askstring("Add Pet", "Breed:", parent=self.root) or "Unknown"
        age = simpledialog.askinteger("Add Pet", "Age (years):", parent=self.root, minvalue=0) or 0
        note = simpledialog.askstring("Add Pet", "Optional behavioral note (blank ok):",
                                       parent=self.root)
        notes = [note] if note else []
        self.manager.add_pet(Pet(name, breed, age, "Available", notes))

        self.breed_combo["values"] = ["All"] + self.manager.unique_breeds()
        self.refresh_pets_table()
        messagebox.showinfo("Pet Added", "{0} was added to the adoptable pets list.".format(name))

    # Donations Tab
    def _build_donations_tab(self):
        frame = self.donations_tab

        top_bar = ttk.Frame(frame)
        top_bar.pack(fill="x", padx=10, pady=8)
        ttk.Button(top_bar, text="Add Donation",
                   command=self.open_add_donation_dialog).pack(side="left")

        columns = ("donor", "amount", "date")
        self.donations_tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        for col, text, width in (("donor", "Donor Name", 260),
                                  ("amount", "Amount", 120), ("date", "Date", 120)):
            self.donations_tree.heading(col, text=text)
            self.donations_tree.column(col, width=width, anchor="w")
        self.donations_tree.pack(fill="both", expand=True, padx=10, pady=6)

        totals_bar = ttk.LabelFrame(frame, text="Monthly Donation Totals")
        totals_bar.pack(fill="x", padx=10, pady=8)

        ttk.Label(totals_bar, text="Month:").grid(row=0, column=0, padx=6, pady=6)
        self.month_var = tk.StringVar(value="All")
        self.month_combo = ttk.Combobox(totals_bar, textvariable=self.month_var,
                                         state="readonly", width=12)
        self.month_combo.grid(row=0, column=1, padx=6)

        ttk.Button(totals_bar, text="Calculate Total",
                   command=self.calculate_monthly_total).grid(row=0, column=2, padx=8)

        self.total_result_label = ttk.Label(totals_bar, text="", font=("TkDefaultFont", 10, "bold"))
        self.total_result_label.grid(row=0, column=3, padx=10)

        self.refresh_donations_table()

    def refresh_donations_table(self):
        for row in self.donations_tree.get_children():
            self.donations_tree.delete(row)
        for d in self.manager.donations:
            self.donations_tree.insert("", "end",
                                        values=(d.donor_name, "${0}".format("{:,.2f}".format(d.amount)), d.date))
        months = ["All"] + self.manager.available_months()
        self.month_combo["values"] = months

    def calculate_monthly_total(self):
        month = self.month_var.get()
        if not month or month == "All":
            total = self.manager.total_all_donations()
            self.total_result_label.config(
                text="All-time total: ${0}".format("{:,.2f}".format(total)))
            return
        totals = self.manager.total_donations_by_month()
        total = totals.get(month, 0.0)
        self.total_result_label.config(
            text="{0} total: ${1}".format(month, "{:,.2f}".format(total)))

    def open_add_donation_dialog(self):
        donor = simpledialog.askstring("Add Donation", "Donor name:", parent=self.root)
        if not donor:
            return
        amount = simpledialog.askfloat("Add Donation", "Amount ($):",
                                        parent=self.root, minvalue=0.0)
        if amount is None:
            return
        date_str = simpledialog.askstring(
            "Add Donation", "Date (YYYY-MM-DD), blank = today:", parent=self.root)
        date_str = date_str.strip() if date_str else None
        try:
            self.manager.add_donation(Donation(donor, amount, date_str))
        except ValueError:
            messagebox.showerror("Invalid Input", "Amount must be a number.")
            return
        self.refresh_donations_table()
        messagebox.showinfo("Donation Added", "Thank you, {0}! Donation recorded.".format(donor))

    # Volunteers Tab
    def _build_volunteers_tab(self):
        frame = self.volunteers_tab

        top_bar = ttk.Frame(frame)
        top_bar.pack(fill="x", padx=10, pady=8)
        ttk.Button(top_bar, text="Add Volunteer",
                   command=self.open_add_volunteer_dialog).pack(side="left")
        ttk.Button(top_bar, text="Log Hours",
                   command=self.open_log_hours_dialog).pack(side="left", padx=6)

        columns = ("name", "phone", "skills", "hours")
        self.volunteers_tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
        for col, text, width in (("name", "Name", 140), ("phone", "Phone", 110),
                                  ("skills", "Skills", 260), ("hours", "Hours Logged", 100)):
            self.volunteers_tree.heading(col, text=text)
            self.volunteers_tree.column(col, width=width, anchor="w")
        self.volunteers_tree.pack(fill="both", expand=True, padx=10, pady=6)

        self.refresh_volunteers_table()

    def refresh_volunteers_table(self):
        for row in self.volunteers_tree.get_children():
            self.volunteers_tree.delete(row)
        for v in self.manager.volunteers.values():
            self.volunteers_tree.insert("", "end", values=(
                v.name, v.phone, ", ".join(v.skills), v.hours_logged))

    def open_add_volunteer_dialog(self):
        name = simpledialog.askstring("Add Volunteer", "Volunteer name:", parent=self.root)
        if not name:
            return
        phone = simpledialog.askstring("Add Volunteer", "Phone number:", parent=self.root) or ""
        skills_str = simpledialog.askstring(
            "Add Volunteer", "Skills (comma-separated):", parent=self.root) or ""
        skills = [s.strip() for s in skills_str.split(",") if s.strip()]
        self.manager.add_volunteer(Volunteer(name, phone, skills))
        self.refresh_volunteers_table()

    def open_log_hours_dialog(self):
        if not self.manager.volunteers:
            messagebox.showinfo("No Volunteers", "Add a volunteer first.")
            return
        name = simpledialog.askstring(
            "Log Hours", "Volunteer name (one of: {0}):".format(
                ", ".join(self.manager.volunteers)), parent=self.root)
        if not name:
            return
        hours = simpledialog.askfloat("Log Hours", "Hours to add:", parent=self.root, minvalue=0.0)
        if hours is None:
            return
        if self.manager.log_volunteer_hours(name, hours):
            self.refresh_volunteers_table()
        else:
            messagebox.showerror("Not Found", "No volunteer named '{0}' was found.".format(name))


def main():
    root = tk.Tk()
    app = ShelterInterface(root)
    root.mainloop()


if __name__ == "__main__":
    main()