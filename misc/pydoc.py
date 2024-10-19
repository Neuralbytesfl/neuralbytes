import os

# Get all attributes and functions in the 'os' module
def list_module_functions(module):
    functions_list = dir(module)
    for func_name in functions_list:
        func = getattr(module, func_name)
        if callable(func):  # Check if it's a function or callable
            print(f"Function: {func_name}")
            print(f"Help: {func.__doc__}\n")

if __name__ == "__main__":
    # Example: Using dir to get the functions in 'os' module
    print("\nFunctions from 'os' module:\n")
    list_module_functions(os)
