import csv
import customtkinter as ctk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from database import (
    add_class,
    add_session,
    add_student,
    clear_all_sessions,
    delete_class,
    delete_session,
    delete_student,
    get_classes,
    get_monthly_earnings,
    get_scheduled_sessions,
    get_session,
    get_session_report_rows,
    get_sessions,
    get_students,
    get_today_sessions,
    get_total_earnings,
    get_total_paid,
    get_total_sessions_taken,
    get_total_unpaid,
    mark_session_taken,
    update_class,
    update_session,
    update_student,
)


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CURRENCY_PREFIX = "NGN "
SESSION_STATUSES = ["scheduled", "taken", "missed", "cancelled"]
PAYMENT_STATUSES = ["unpaid", "paid"]
CURRICULUMS = ["Coding", "WAEC", "IGCSE", "GCSE", "AQA", "OCR"]


def format_currency(amount, hidden=False):
    if hidden:
        return f"{CURRENCY_PREFIX}******"
    return f"{CURRENCY_PREFIX}{amount:,.2f}"


def launch_gui():
    app = ctk.CTk()
    app.geometry("1100x650")
    app.title("Teaching Revenue Tracker")

    main_frame = ctk.CTkFrame(app)
    main_frame.pack(fill="both", expand=True)

    sidebar = ctk.CTkFrame(main_frame, width=200)
    sidebar.pack(side="left", fill="y")

    content = ctk.CTkFrame(main_frame)
    content.pack(side="right", fill="both", expand=True)

    title_label = ctk.CTkLabel(
        sidebar,
        text="Teaching\nTracker",
        font=("Arial", 20, "bold")
    )
    title_label.pack(pady=30)

    container = ctk.CTkFrame(content)
    container.pack(fill="both", expand=True, padx=20, pady=20)

    frames = {}

    def show_frame(name):
        for frame in frames.values():
            frame.pack_forget()
        frames[name].pack(fill="both", expand=True)

    dashboard_frame = ctk.CTkFrame(container)
    frames["Dashboard"] = dashboard_frame

    ctk.CTkLabel(
        dashboard_frame,
        text="Dashboard Overview",
        font=("Arial", 20, "bold")
    ).pack(pady=20)

    earnings_visible = True

    earnings_value = ctk.CTkLabel(
        dashboard_frame,
        text="",
        font=("Arial", 40, "bold")
    )
    earnings_value.pack(pady=10)

    toggle_button = ctk.CTkButton(
        dashboard_frame,
        text="Hide / Show Earnings"
    )
    toggle_button.pack(pady=10)

    stats_frame = ctk.CTkFrame(dashboard_frame)
    stats_frame.pack(pady=20)

    sessions_taken = ctk.CTkLabel(stats_frame, font=("Arial", 16))
    sessions_taken.grid(row=0, column=0, padx=20)

    scheduled_sessions = ctk.CTkLabel(stats_frame, font=("Arial", 16))
    scheduled_sessions.grid(row=0, column=1, padx=20)

    monthly_income = ctk.CTkLabel(stats_frame, font=("Arial", 16))
    monthly_income.grid(row=0, column=2, padx=20)

    paid_income = ctk.CTkLabel(stats_frame, font=("Arial", 16))
    paid_income.grid(row=1, column=0, padx=20, pady=(12, 0))

    unpaid_income = ctk.CTkLabel(stats_frame, font=("Arial", 16))
    unpaid_income.grid(row=1, column=1, padx=20, pady=(12, 0))

    today_frame = ctk.CTkFrame(dashboard_frame)
    today_frame.pack(pady=20, fill="x")

    ctk.CTkLabel(
        today_frame,
        text="Today's Sessions",
        font=("Arial", 16, "bold")
    ).pack(pady=5)

    today_list = ctk.CTkTextbox(today_frame, height=120)
    today_list.pack(fill="x", padx=20)

    students_overview_frame = ctk.CTkFrame(dashboard_frame)
    students_overview_frame.pack(pady=20, fill="both", expand=True)

    ctk.CTkLabel(
        students_overview_frame,
        text="All Students",
        font=("Arial", 16, "bold")
    ).pack(pady=5)

    students_list = ctk.CTkTextbox(students_overview_frame, height=160)
    students_list.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    def update_dashboard():
        total = get_total_earnings()

        if earnings_visible:
            earnings_value.configure(text=format_currency(total))
        else:
            earnings_value.configure(text=format_currency(total, hidden=True))

        sessions_taken.configure(
            text=f"Sessions Taken: {get_total_sessions_taken()}"
        )
        scheduled_sessions.configure(
            text=f"Scheduled: {get_scheduled_sessions()}"
        )
        monthly_income.configure(
            text=f"This Month: {format_currency(get_monthly_earnings())}"
        )
        paid_income.configure(
            text=f"Paid: {format_currency(get_total_paid())}"
        )
        unpaid_income.configure(
            text=f"Unpaid: {format_currency(get_total_unpaid())}"
        )

        today_list.delete("1.0", "end")
        today_sessions = get_today_sessions()

        if not today_sessions:
            today_list.insert("end", "No sessions today.")
        else:
            for session in today_sessions:
                student, class_name, time_value, status = session
                today_list.insert(
                    "end",
                    f"{time_value} - {student} - {class_name} ({status})\n"
                )

        students_list.delete("1.0", "end")
        students = get_students()

        if not students:
            students_list.insert("end", "No students added yet.")
        else:
            for student in students:
                name = student[1]
                email = student[2] or "No email"
                current_class = student[3] or "No class/year group"
                curriculum = student[4] or "No curriculum"
                students_list.insert(
                    "end",
                    f"{name} - {email} - {current_class} - {curriculum}\n"
                )

    def toggle_earnings():
        nonlocal earnings_visible
        earnings_visible = not earnings_visible
        update_dashboard()

    toggle_button.configure(command=toggle_earnings)

    students_frame = ctk.CTkFrame(container)
    frames["Students"] = students_frame

    student_form_title = ctk.CTkLabel(
        students_frame,
        text="Add Student",
        font=("Arial", 16)
    )
    student_form_title.pack(pady=10)

    student_name = ctk.CTkEntry(students_frame, placeholder_text="Name")
    student_name.pack(pady=5)

    student_email = ctk.CTkEntry(students_frame, placeholder_text="Email")
    student_email.pack(pady=5)

    student_current_class = ctk.CTkEntry(
        students_frame,
        placeholder_text="Current Class / Year Group"
    )
    student_current_class.pack(pady=5)

    student_curriculum_var = ctk.StringVar(value=CURRICULUMS[0])
    student_curriculum = ctk.CTkOptionMenu(
        students_frame,
        variable=student_curriculum_var,
        values=CURRICULUMS
    )
    student_curriculum.pack(pady=5)

    selected_student_id = None

    def parse_positive_number(raw_value, field_name):
        try:
            value = float(raw_value)
        except ValueError:
            messagebox.showerror("Invalid Input", f"{field_name} must be a number.")
            return None

        if value <= 0:
            messagebox.showerror("Invalid Input", f"{field_name} must be greater than 0.")
            return None

        return value

    def is_valid_email(email):
        return "@" in email and "." in email

    def reset_student_form():
        nonlocal selected_student_id
        selected_student_id = None
        student_name.delete(0, "end")
        student_email.delete(0, "end")
        student_current_class.delete(0, "end")
        student_curriculum_var.set(CURRICULUMS[0])
        student_form_title.configure(text="Add Student")
        save_student_button.configure(text="Save Student")
        new_student_button.configure(state="disabled")
        if student_tree.selection():
            student_tree.selection_remove(student_tree.selection())

    def save_student():
        nonlocal selected_student_id
        name = student_name.get().strip()
        email = student_email.get().strip()
        current_class = student_current_class.get().strip()
        curriculum = student_curriculum_var.get().strip()

        if not name:
            messagebox.showerror("Invalid Input", "Student name is required.")
            return

        if email and not is_valid_email(email):
            messagebox.showerror("Invalid Input", "Enter a valid email address.")
            return

        if curriculum not in CURRICULUMS:
            messagebox.showerror("Invalid Input", "Select a valid curriculum.")
            return

        try:
            if selected_student_id is None:
                add_student(name, email, current_class, curriculum)
                messagebox.showinfo("Success", "Student added")
            else:
                update_student(
                    selected_student_id,
                    name,
                    email,
                    current_class,
                    curriculum
                )
                messagebox.showinfo("Success", "Student updated")
        except ValueError as error:
            messagebox.showerror("Error", str(error))
            return

        refresh_dropdowns()
        load_students_table()
        load_sessions()
        update_dashboard()
        reset_session_form()
        reset_student_form()

    def delete_selected_student():
        if selected_student_id is None:
            messagebox.showwarning("No Selection", "Select a student to delete.")
            return

        confirmed = messagebox.askyesno(
            "Delete Student",
            "Are you sure you want to delete the selected student?"
        )
        if not confirmed:
            return

        try:
            delete_student(selected_student_id)
        except ValueError as error:
            messagebox.showerror("Error", str(error))
            return

        refresh_dropdowns()
        load_students_table()
        update_dashboard()
        reset_student_form()
        messagebox.showinfo("Success", "Student deleted.")

    student_actions = ctk.CTkFrame(students_frame)
    student_actions.pack(pady=10)

    save_student_button = ctk.CTkButton(
        student_actions,
        text="Save Student",
        command=save_student
    )
    save_student_button.grid(row=0, column=0, padx=8)

    new_student_button = ctk.CTkButton(
        student_actions,
        text="New Student",
        command=reset_student_form,
        state="disabled"
    )
    new_student_button.grid(row=0, column=1, padx=8)

    delete_student_button = ctk.CTkButton(
        student_actions,
        text="Delete Student",
        command=delete_selected_student,
        fg_color="#B33636",
        hover_color="#922B2B"
    )
    delete_student_button.grid(row=0, column=2, padx=8)

    students_table_frame = ctk.CTkFrame(students_frame)
    students_table_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))

    student_tree = ttk.Treeview(
        students_table_frame,
        columns=("ID", "Name", "Email", "Class / Year", "Curriculum", "Created"),
        show="headings"
    )

    for col in student_tree["columns"]:
        student_tree.heading(col, text=col)
        student_tree.column(col, width=140)

    student_tree.pack(fill="both", expand=True)

    def load_students_table():
        for row in student_tree.get_children():
            student_tree.delete(row)
        for student in get_students():
            student_tree.insert("", "end", values=student)

    def on_student_select(_event=None):
        nonlocal selected_student_id
        selected = student_tree.focus()
        if not selected:
            return

        values = student_tree.item(selected, "values")
        if not values:
            return

        selected_student_id = int(values[0])
        student_name.delete(0, "end")
        student_name.insert(0, values[1])
        student_email.delete(0, "end")
        student_email.insert(0, values[2] or "")
        student_current_class.delete(0, "end")
        student_current_class.insert(0, values[3] or "")
        student_curriculum_var.set(values[4] or CURRICULUMS[0])
        student_form_title.configure(text="Edit Student")
        save_student_button.configure(text="Update Student")
        new_student_button.configure(state="normal")

    student_tree.bind("<<TreeviewSelect>>", on_student_select)

    classes_frame = ctk.CTkFrame(container)
    frames["Classes"] = classes_frame

    class_form_title = ctk.CTkLabel(
        classes_frame,
        text="Add Class",
        font=("Arial", 16)
    )
    class_form_title.pack(pady=10)

    class_title = ctk.CTkEntry(classes_frame, placeholder_text="Title")
    class_title.pack(pady=5)

    class_desc = ctk.CTkEntry(classes_frame, placeholder_text="Description")
    class_desc.pack(pady=5)

    class_rate = ctk.CTkEntry(classes_frame, placeholder_text="Hourly Rate")
    class_rate.pack(pady=5)

    selected_class_id = None

    def reset_class_form():
        nonlocal selected_class_id
        selected_class_id = None
        class_title.delete(0, "end")
        class_desc.delete(0, "end")
        class_rate.delete(0, "end")
        class_form_title.configure(text="Add Class")
        save_class_button.configure(text="Save Class")
        new_class_button.configure(state="disabled")
        if class_tree.selection():
            class_tree.selection_remove(class_tree.selection())

    def save_class():
        nonlocal selected_class_id
        title = class_title.get().strip()
        description = class_desc.get().strip()
        rate = parse_positive_number(class_rate.get().strip(), "Hourly rate")

        if not title:
            messagebox.showerror("Invalid Input", "Class title is required.")
            return

        if rate is None:
            return

        try:
            if selected_class_id is None:
                add_class(title, description, rate)
                messagebox.showinfo("Success", "Class added")
            else:
                update_class(selected_class_id, title, description, rate)
                messagebox.showinfo("Success", "Class updated")
        except ValueError as error:
            messagebox.showerror("Error", str(error))
            return

        refresh_dropdowns()
        load_classes_table()
        load_sessions()
        update_dashboard()
        reset_class_form()

    def delete_selected_class():
        if selected_class_id is None:
            messagebox.showwarning("No Selection", "Select a class to delete.")
            return

        confirmed = messagebox.askyesno(
            "Delete Class",
            "Are you sure you want to delete the selected class?"
        )
        if not confirmed:
            return

        try:
            delete_class(selected_class_id)
        except ValueError as error:
            messagebox.showerror("Error", str(error))
            return

        refresh_dropdowns()
        load_classes_table()
        update_dashboard()
        reset_class_form()
        messagebox.showinfo("Success", "Class deleted.")

    class_actions = ctk.CTkFrame(classes_frame)
    class_actions.pack(pady=10)

    save_class_button = ctk.CTkButton(
        class_actions,
        text="Save Class",
        command=save_class
    )
    save_class_button.grid(row=0, column=0, padx=8)

    new_class_button = ctk.CTkButton(
        class_actions,
        text="New Class",
        command=reset_class_form,
        state="disabled"
    )
    new_class_button.grid(row=0, column=1, padx=8)

    delete_class_button = ctk.CTkButton(
        class_actions,
        text="Delete Class",
        command=delete_selected_class,
        fg_color="#B33636",
        hover_color="#922B2B"
    )
    delete_class_button.grid(row=0, column=2, padx=8)

    classes_table_frame = ctk.CTkFrame(classes_frame)
    classes_table_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))

    class_tree = ttk.Treeview(
        classes_table_frame,
        columns=("ID", "Title", "Description", "Rate", "Created"),
        show="headings"
    )

    for col in class_tree["columns"]:
        class_tree.heading(col, text=col)
        class_tree.column(col, width=150)

    class_tree.pack(fill="both", expand=True)

    def load_classes_table():
        for row in class_tree.get_children():
            class_tree.delete(row)
        for class_item in get_classes():
            class_tree.insert("", "end", values=class_item)

    def on_class_select(_event=None):
        nonlocal selected_class_id
        selected = class_tree.focus()
        if not selected:
            return

        values = class_tree.item(selected, "values")
        if not values:
            return

        selected_class_id = int(values[0])
        class_title.delete(0, "end")
        class_title.insert(0, values[1])
        class_desc.delete(0, "end")
        class_desc.insert(0, values[2] or "")
        class_rate.delete(0, "end")
        class_rate.insert(0, values[3])
        class_form_title.configure(text="Edit Class")
        save_class_button.configure(text="Update Class")
        new_class_button.configure(state="normal")

    class_tree.bind("<<TreeviewSelect>>", on_class_select)

    sessions_frame = ctk.CTkFrame(container)
    frames["Sessions"] = sessions_frame

    form_frame = ctk.CTkFrame(sessions_frame)
    form_frame.pack(pady=15)

    student_var = ctk.StringVar()
    student_dropdown = ctk.CTkOptionMenu(form_frame, variable=student_var)
    student_dropdown.grid(row=0, column=0, padx=10)

    class_var = ctk.StringVar()
    class_dropdown = ctk.CTkOptionMenu(form_frame, variable=class_var)
    class_dropdown.grid(row=0, column=1, padx=10)

    date_entry = ctk.CTkEntry(form_frame, placeholder_text="YYYY-MM-DD")
    date_entry.grid(row=1, column=0, padx=10, pady=5)

    time_entry = ctk.CTkEntry(form_frame, placeholder_text="HH:MM")
    time_entry.grid(row=1, column=1, padx=10, pady=5)

    duration_entry = ctk.CTkEntry(form_frame, placeholder_text="Hours")
    duration_entry.grid(row=2, column=0, padx=10, pady=5)

    status_var = ctk.StringVar(value="scheduled")
    status_dropdown = ctk.CTkOptionMenu(
        form_frame,
        variable=status_var,
        values=SESSION_STATUSES
    )
    status_dropdown.grid(row=2, column=1, padx=10, pady=5)

    payment_var = ctk.StringVar(value="unpaid")
    payment_dropdown = ctk.CTkOptionMenu(
        form_frame,
        variable=payment_var,
        values=PAYMENT_STATUSES
    )
    payment_dropdown.grid(row=3, column=0, padx=10, pady=5)

    payment_date_entry = ctk.CTkEntry(
        form_frame,
        placeholder_text="Payment Date YYYY-MM-DD"
    )
    payment_date_entry.grid(row=3, column=1, padx=10, pady=5)

    selected_session_id = None

    def set_dropdown_by_id(variable, values, item_id):
        for value in values:
            if value.startswith(f"{item_id} - "):
                variable.set(value)
                return

    def refresh_dropdowns():
        students = get_students()
        classes = get_classes()

        student_values = [f"{student[0]} - {student[1]}" for student in students]
        class_values = [f"{class_item[0]} - {class_item[1]}" for class_item in classes]

        student_dropdown.configure(values=student_values or ["No students available"])
        class_dropdown.configure(values=class_values or ["No classes available"])

        if student_values:
            student_var.set(student_values[0])
        else:
            student_var.set("No students available")

        if class_values:
            class_var.set(class_values[0])
        else:
            class_var.set("No classes available")

    def reset_session_form():
        nonlocal selected_session_id
        selected_session_id = None
        date_entry.delete(0, "end")
        time_entry.delete(0, "end")
        duration_entry.delete(0, "end")
        payment_date_entry.delete(0, "end")
        status_var.set("scheduled")
        payment_var.set("unpaid")
        save_session_button.configure(text="Create Session")
        new_session_button.configure(state="disabled")
        if tree.selection():
            tree.selection_remove(tree.selection())

    def save_session():
        nonlocal selected_session_id
        student_value = student_var.get().strip()
        class_value = class_var.get().strip()
        date_value = date_entry.get().strip()
        time_value = time_entry.get().strip()
        duration = parse_positive_number(duration_entry.get().strip(), "Duration")
        status = status_var.get().strip()
        payment_status = payment_var.get().strip()
        payment_date = payment_date_entry.get().strip() or None

        if " - " not in student_value:
            messagebox.showerror("Invalid Input", "Add a student before saving a session.")
            return

        if " - " not in class_value:
            messagebox.showerror("Invalid Input", "Add a class before saving a session.")
            return

        try:
            datetime.strptime(date_value, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Input", "Date must be in YYYY-MM-DD format.")
            return

        try:
            datetime.strptime(time_value, "%H:%M")
        except ValueError:
            messagebox.showerror("Invalid Input", "Time must be in HH:MM format.")
            return

        if duration is None:
            return

        if status not in SESSION_STATUSES:
            messagebox.showerror("Invalid Input", "Select a valid session status.")
            return

        if payment_status not in PAYMENT_STATUSES:
            messagebox.showerror("Invalid Input", "Select a valid payment status.")
            return

        if status != "taken" and payment_status == "paid":
            messagebox.showerror(
                "Invalid Input",
                "Only taken sessions can be marked as paid."
            )
            return

        if payment_date is not None:
            try:
                datetime.strptime(payment_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror(
                    "Invalid Input",
                    "Payment date must be in YYYY-MM-DD format."
                )
                return

        student_id = int(student_value.split(" - ")[0])
        class_id = int(class_value.split(" - ")[0])

        try:
            if selected_session_id is None:
                add_session(
                    class_id,
                    student_id,
                    date_value,
                    time_value,
                    duration,
                    status,
                    payment_status,
                    payment_date
                )
                messagebox.showinfo("Success", "Session created")
            else:
                update_session(
                    selected_session_id,
                    class_id,
                    student_id,
                    date_value,
                    time_value,
                    duration,
                    status,
                    payment_status,
                    payment_date
                )
                messagebox.showinfo("Success", "Session updated")
        except ValueError as error:
            messagebox.showerror("Error", str(error))
            return

        load_sessions()
        update_dashboard()
        reset_session_form()

    save_session_button = ctk.CTkButton(
        form_frame,
        text="Create Session",
        command=save_session
    )
    save_session_button.grid(row=4, column=0, padx=10, pady=5)

    new_session_button = ctk.CTkButton(
        form_frame,
        text="New Session",
        command=reset_session_form,
        state="disabled"
    )
    new_session_button.grid(row=4, column=1, padx=10, pady=5)

    filters_frame = ctk.CTkFrame(sessions_frame)
    filters_frame.pack(fill="x", padx=10, pady=(5, 10))

    session_search = ctk.CTkEntry(
        filters_frame,
        placeholder_text="Search student, class, date, status"
    )
    session_search.grid(row=0, column=0, padx=6, pady=6, sticky="ew")

    status_filter_var = ctk.StringVar(value="All")
    status_filter = ctk.CTkOptionMenu(
        filters_frame,
        variable=status_filter_var,
        values=["All"] + SESSION_STATUSES
    )
    status_filter.grid(row=0, column=1, padx=6, pady=6)

    payment_filter_var = ctk.StringVar(value="All")
    payment_filter = ctk.CTkOptionMenu(
        filters_frame,
        variable=payment_filter_var,
        values=["All"] + PAYMENT_STATUSES
    )
    payment_filter.grid(row=0, column=2, padx=6, pady=6)

    date_from_filter = ctk.CTkEntry(filters_frame, placeholder_text="From YYYY-MM-DD")
    date_from_filter.grid(row=1, column=0, padx=6, pady=6, sticky="ew")

    date_to_filter = ctk.CTkEntry(filters_frame, placeholder_text="To YYYY-MM-DD")
    date_to_filter.grid(row=1, column=1, padx=6, pady=6)

    filters_frame.grid_columnconfigure(0, weight=1)

    table_frame = ctk.CTkFrame(sessions_frame)
    table_frame.pack(fill="both", expand=True, pady=15)

    tree = ttk.Treeview(
        table_frame,
        columns=(
            "ID",
            "Student",
            "Class",
            "Date",
            "Time",
            "Duration",
            "Status",
            "Earnings",
            "Payment",
            "Paid Date",
        ),
        show="headings"
    )

    sort_directions = {}

    def sort_tree_by(column):
        reverse = sort_directions.get(column, False)
        numeric_columns = {"ID", "Duration", "Earnings"}

        def sort_value(item):
            value = tree.set(item, column)
            if column in numeric_columns:
                try:
                    return float(value)
                except ValueError:
                    return 0
            return value.lower()

        rows = list(tree.get_children(""))
        rows.sort(key=sort_value, reverse=reverse)

        for index, item in enumerate(rows):
            tree.move(item, "", index)

        sort_directions[column] = not reverse

    for col in tree["columns"]:
        tree.heading(col, text=col, command=lambda column=col: sort_tree_by(column))
        tree.column(col, width=120)

    tree.pack(fill="both", expand=True)

    def get_session_filters():
        return {
            "search_text": session_search.get().strip(),
            "status": status_filter_var.get().strip(),
            "payment_status": payment_filter_var.get().strip(),
            "date_from": date_from_filter.get().strip(),
            "date_to": date_to_filter.get().strip(),
        }

    def validate_filter_dates():
        filters = get_session_filters()

        for field_name, label in (
            ("date_from", "From date"),
            ("date_to", "To date"),
        ):
            value = filters[field_name]
            if not value:
                continue
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror(
                    "Invalid Filter",
                    f"{label} must be in YYYY-MM-DD format."
                )
                return None

        if filters["date_from"] and filters["date_to"]:
            if filters["date_from"] > filters["date_to"]:
                messagebox.showerror(
                    "Invalid Filter",
                    "From date cannot be after To date."
                )
                return None

        return filters

    def load_sessions():
        filters = validate_filter_dates()
        if filters is None:
            return

        for row in tree.get_children():
            tree.delete(row)
        for session in get_sessions(**filters):
            tree.insert("", "end", values=session)

    def clear_session_filters():
        session_search.delete(0, "end")
        date_from_filter.delete(0, "end")
        date_to_filter.delete(0, "end")
        status_filter_var.set("All")
        payment_filter_var.set("All")
        load_sessions()

    def export_sessions_csv():
        filters = validate_filter_dates()
        if filters is None:
            return

        rows = get_session_report_rows(**filters)
        if not rows:
            messagebox.showinfo("No Data", "There are no sessions to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="session_report.csv",
            title="Export Session Report"
        )
        if not file_path:
            return

        headers = tree["columns"]
        try:
            with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(headers)
                writer.writerows(rows)
        except OSError as error:
            messagebox.showerror("Export Failed", str(error))
            return

        messagebox.showinfo("Export Complete", "Session report exported.")

    filter_actions = ctk.CTkFrame(filters_frame)
    filter_actions.grid(row=1, column=2, padx=6, pady=6)

    ctk.CTkButton(
        filter_actions,
        text="Apply Filters",
        command=load_sessions
    ).grid(row=0, column=0, padx=4)

    ctk.CTkButton(
        filter_actions,
        text="Clear Filters",
        command=clear_session_filters
    ).grid(row=0, column=1, padx=4)

    ctk.CTkButton(
        filter_actions,
        text="Export CSV",
        command=export_sessions_csv
    ).grid(row=0, column=2, padx=4)

    def on_session_select(_event=None):
        nonlocal selected_session_id
        selected = tree.focus()
        if not selected:
            return

        values = tree.item(selected, "values")
        if not values:
            return

        session = get_session(values[0])
        if session is None:
            messagebox.showerror("Error", "Session not found.")
            return

        (
            selected_session_id,
            class_id,
            student_id,
            date_value,
            time_value,
            duration,
            status,
            payment_status,
            payment_date,
        ) = session

        students = [f"{student[0]} - {student[1]}" for student in get_students()]
        classes = [f"{class_item[0]} - {class_item[1]}" for class_item in get_classes()]
        set_dropdown_by_id(student_var, students, student_id)
        set_dropdown_by_id(class_var, classes, class_id)

        date_entry.delete(0, "end")
        date_entry.insert(0, date_value)
        time_entry.delete(0, "end")
        time_entry.insert(0, time_value)
        duration_entry.delete(0, "end")
        duration_entry.insert(0, duration)
        status_var.set(status)
        payment_var.set(payment_status)
        payment_date_entry.delete(0, "end")
        payment_date_entry.insert(0, payment_date or "")
        save_session_button.configure(text="Update Session")
        new_session_button.configure(state="normal")

    tree.bind("<<TreeviewSelect>>", on_session_select)

    def mark_taken():
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Select a session to mark as taken.")
            return

        values = tree.item(selected, "values")
        try:
            mark_session_taken(values[0])
        except ValueError as error:
            messagebox.showerror("Error", str(error))
            return

        load_sessions()
        update_dashboard()
        reset_session_form()

    def delete_selected_session():
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("No Selection", "Select a session to delete.")
            return

        values = tree.item(selected, "values")
        session_id = values[0]

        confirmed = messagebox.askyesno(
            "Delete Session",
            "Are you sure you want to delete the selected session?"
        )
        if not confirmed:
            return

        try:
            delete_session(session_id)
        except ValueError as error:
            messagebox.showerror("Error", str(error))
            return

        load_sessions()
        update_dashboard()
        reset_session_form()
        messagebox.showinfo("Success", "Session deleted.")

    def clear_sessions():
        if not tree.get_children():
            messagebox.showinfo("No Sessions", "There are no sessions to clear.")
            return

        confirmed = messagebox.askyesno(
            "Clear All Sessions",
            "This will permanently delete all sessions. Continue?"
        )
        if not confirmed:
            return

        clear_all_sessions()
        load_sessions()
        update_dashboard()
        reset_session_form()
        messagebox.showinfo("Success", "All sessions cleared.")

    session_actions = ctk.CTkFrame(sessions_frame)
    session_actions.pack(pady=10)

    ctk.CTkButton(
        session_actions,
        text="Mark Selected As Taken",
        command=mark_taken
    ).grid(row=0, column=0, padx=8)

    ctk.CTkButton(
        session_actions,
        text="Delete Selected Session",
        command=delete_selected_session,
        fg_color="#B33636",
        hover_color="#922B2B"
    ).grid(row=0, column=1, padx=8)

    ctk.CTkButton(
        session_actions,
        text="Clear All Sessions",
        command=clear_sessions,
        fg_color="#7A1F1F",
        hover_color="#611818"
    ).grid(row=0, column=2, padx=8)

    ctk.CTkButton(
        sidebar,
        text="Dashboard",
        command=lambda: show_frame("Dashboard")
    ).pack(pady=10)
    ctk.CTkButton(
        sidebar,
        text="Students",
        command=lambda: show_frame("Students")
    ).pack(pady=10)
    ctk.CTkButton(
        sidebar,
        text="Classes",
        command=lambda: show_frame("Classes")
    ).pack(pady=10)
    ctk.CTkButton(
        sidebar,
        text="Sessions",
        command=lambda: show_frame("Sessions")
    ).pack(pady=10)

    def refresh_views():
        load_students_table()
        load_classes_table()
        load_sessions()
        update_dashboard()
        app.after(60000, refresh_views)

    refresh_dropdowns()
    load_students_table()
    load_classes_table()
    load_sessions()
    update_dashboard()
    show_frame("Dashboard")
    app.after(60000, refresh_views)

    app.mainloop()
