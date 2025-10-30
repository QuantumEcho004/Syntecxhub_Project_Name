import csv
import os
import json # Used for a clear error message, though main persistence is CSV

# --- Configuration and Constants ---
DATA_FILE = 'students.csv'

# =================================================================
#                         1. Student Class
# =================================================================

class Student:
    """Represents a single student record."""

    def __init__(self, name: str, student_id: str, grade: str):
        """
        Constructor for the Student class.

        :param name: The student's name.
        :param student_id: The student's unique ID.
        :param grade: The student's grade (e.g., A, B, C).
        """
        self.name = name
        self.id = student_id
        self.grade = grade

    def to_dict(self):
        """Returns the student data as a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'grade': self.grade
        }

    def __str__(self):
        """String representation for formatted output."""
        return f"ID: {self.id:<6} | Name: {self.name:<20} | Grade: {self.grade}"

# =================================================================
#                         2. Manager Class
# =================================================================

class StudentManager:
    """
    Manages the collection of student records, handles file I/O,
    and implements core operations (CRUD).
    """

    def __init__(self, filename: str):
        """Initializes the manager and loads existing records from the file."""
        self.filename = filename
        self.students = {}  # Key: student_id, Value: Student object
        self._load_records()

    def _load_records(self):
        """Loads student records from the CSV file."""
        if not os.path.exists(self.filename):
            return

        with open(self.filename, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Simple check for required fields
                    if 'id' in row and 'name' in row and 'grade' in row:
                        student = Student(
                            name=row['name'],
                            student_id=row['id'],
                            grade=row['grade']
                        )
                        self.students[student.id] = student
                except Exception as e:
                    print(f"Error loading record: {row} - {e}")

    def _save_records(self):
        """Saves all current student records to the CSV file."""
        fieldnames = ['id', 'name', 'grade']
        
        # Ensure directory exists if needed, though usually not needed for a file in the same dir
        # os.makedirs(os.path.dirname(self.filename), exist_ok=True) 

        with open(self.filename, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write student data
            for student in self.students.values():
                writer.writerow(student.to_dict())
        
        print(f"\n✅ Records saved successfully to {self.filename}.")


    # --- CRUD Operations ---

    def add_student(self, student: Student) -> bool:
        """Adds a new student, validates for unique ID."""
        if student.id in self.students:
            print(f"\n❌ Error: Student ID '{student.id}' already exists.")
            return False

        self.students[student.id] = student
        self._save_records()
        print(f"\n✨ Student '{student.name}' added successfully.")
        return True

    def update_student(self, student_id: str, new_name: str = None, new_grade: str = None) -> bool:
        """Updates the name and/or grade of an existing student."""
        if student_id not in self.students:
            print(f"\n❌ Error: Student ID '{student_id}' not found.")
            return False

        student = self.students[student_id]
        if new_name is not None:
            student.name = new_name
        if new_grade is not None:
            student.grade = new_grade

        self._save_records()
        print(f"\n🔄 Student ID '{student_id}' updated successfully.")
        return True

    def delete_student(self, student_id: str) -> bool:
        """Deletes a student record by ID."""
        if student_id not in self.students:
            print(f"\n❌ Error: Student ID '{student_id}' not found.")
            return False

        del self.students[student_id]
        self._save_records()
        print(f"\n🗑️ Student ID '{student_id}' deleted successfully.")
        return True

    def list_students(self):
        """Prints all student records in a formatted way."""
        if not self.students:
            print("\n➡️ No student records found.")
            return

        print("\n" + "="*50)
        print(f"| {'STUDENT RECORDS':^48} |")
        print("="*50)
        print(f"| {'ID':<6} | {'NAME':<20} | {'GRADE':<6} |")
        print("-" * 50)
        
        # Sort by ID for a consistent display
        sorted_students = sorted(self.students.values(), key=lambda s: s.id)
        
        for student in sorted_students:
            # Using the __str__ method for formatted output
            print(f"| {student.id:<6} | {student.name:<20} | {student.grade:<6} |")
        
        print("="*50)


# =================================================================
#                           3. CLI Functions
# =================================================================

def get_input(prompt, allow_empty=False):
    """Helper for getting user input."""
    while True:
        user_input = input(f"   {prompt}: ").strip()
        if user_input or allow_empty:
            return user_input
        print("   Input cannot be empty. Please try again.")

def cli_add_student(manager: StudentManager):
    """Handles the command-line flow for adding a student."""
    print("\n--- ➕ Add New Student ---")
    name = get_input("Enter student name")
    student_id = get_input("Enter unique student ID")
    grade = get_input("Enter grade (e.g., A, B, C, P)")
    
    # Simple validation for ID format (can be enhanced)
    if not student_id.isalnum():
        print("\n❌ Error: Student ID must be alphanumeric.")
        return

    new_student = Student(name, student_id, grade.upper())
    manager.add_student(new_student)

def cli_update_student(manager: StudentManager):
    """Handles the command-line flow for updating a student."""
    print("\n--- 🔄 Update Student ---")
    student_id = get_input("Enter ID of student to update")

    if student_id not in manager.students:
        print(f"\n❌ Error: Student ID '{student_id}' not found.")
        return

    print("Note: Leave a field blank to keep the current value.")
    new_name = get_input(f"Enter new name (Current: {manager.students[student_id].name})", allow_empty=True)
    new_grade = get_input(f"Enter new grade (Current: {manager.students[student_id].grade})", allow_empty=True)
    
    # Only pass the values that were actually entered
    manager.update_student(
        student_id, 
        new_name if new_name else None, 
        new_grade.upper() if new_grade else None
    )

def cli_delete_student(manager: StudentManager):
    """Handles the command-line flow for deleting a student."""
    print("\n--- 🗑️ Delete Student ---")
    student_id = get_input("Enter ID of student to delete")
    
    if student_id not in manager.students:
        print(f"\n❌ Error: Student ID '{student_id}' not found.")
        return
        
    confirm = get_input(f"Are you sure you want to delete student ID '{student_id}'? (Y/N)", allow_empty=False).upper()
    if confirm == 'Y':
        manager.delete_student(student_id)
    else:
        print("Operation cancelled.")


# =================================================================
#                          4. Main Execution
# =================================================================

def main():
    """The main entry point for the CLI application."""
    print("🚀 Initializing Student Management System...")
    manager = StudentManager(DATA_FILE)
    
    while True:
        print("\n" + "="*30)
        print("| Student Management System |")
        print("="*30)
        print("| 1. Add Student            |")
        print("| 2. List Students          |")
        print("| 3. Update Student         |")
        print("| 4. Delete Student         |")
        print("| 5. Exit                   |")
        print("="*30)
        
        choice = get_input("Enter your choice (1-5)")

        if choice == '1':
            cli_add_student(manager)
        elif choice == '2':
            manager.list_students()
        elif choice == '3':
            cli_update_student(manager)
        elif choice == '4':
            cli_delete_student(manager)
        elif choice == '5':
            print("\n👋 Exiting Student Management System. Goodbye!")
            break
        else:
            print("\n🚨 Invalid choice. Please enter a number between 1 and 5.")

if __name__ == "__main__":
    main()