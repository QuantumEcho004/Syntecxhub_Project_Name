def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b

def calculate(num1, operator, num2):
    if operator == '+':
        return add(num1, num2)
    elif operator == '-':
        return subtract(num1, num2)
    elif operator == '*':
        return multiply(num1, num2)
    elif operator == '/':
        return divide(num1, num2)
    else:
        raise ValueError("Invalid operator.")

def main():
    print("=== Simple Command-Line Calculator ===")
    print("Supported operations: +, -, *, /, clear, exit\n")

    while True:
        user_input = input("Enter calculation (e.g., 5 + 3): ").strip()

        # Handle clear
        if user_input.lower() == "clear":
            print("\n--- Screen cleared ---\n")
            continue

        # Handle exit
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        try:
            # Parse input
            parts = user_input.split()
            if len(parts) != 3:
                print("❌ Invalid format. Use: number operator number")
                continue

            num1 = float(parts[0])
            operator = parts[1]
            num2 = float(parts[2])

            # Perform calculation
            result = calculate(num1, operator, num2)
            print(f"✅ Result: {result}\n")

        except ValueError as e:
            print(f"⚠️ Error: {e}\n")
        except Exception:
            print("❌ Something went wrong. Please try again.\n")

if __name__ == "__main__":
    main()
