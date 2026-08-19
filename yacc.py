import tkinter as tk
import math
import cmath
import re

# Colors:
success_color = "#20c997"
danger_color = "#ff8787"

class Calculator:
    def __init__(self, root):
        self.root = root
        self.root.title("YACC - Yet Another Complex Calculator")
        self.root.geometry("680x650")  # Widened the application to give the text output more horizontal room
        self.root.config(bg="#e5e5e5")

        self.equation_var = tk.StringVar()  # What the user types. Will be updated at keystroke.
        self.current_result_plain = ""  # We will store the plain math string here so it can be passed back if '=' is pressed.

        self.is_polar_mode = False  # Default to cartesian form.
        self.is_shifted = False  # SHIFT key being held down?
        self.buttons = {}  # Create a dictionary to store our button objects. Will be populated later.

        self.equation_var.trace_add("write", self.evaluate_live)  # Watch equation_var; if any changes, evaluate! (See evaluate_live() function below)

        self.root.bind("<KeyPress-Shift_L>", self.activate_shift)
        self.root.bind("<KeyRelease-Shift_L>", self.deactivate_shift)
        self.root.bind("<KeyPress-Shift_R>", self.activate_shift)
        self.root.bind("<KeyRelease-Shift_R>", self.deactivate_shift)

        self.root.bind("<Return>", lambda event: self.on_button_click('='))  # To prevent immediate evaluation, we use lambda.
        self.root.bind("<KP_Enter>", lambda event: self.on_button_click('='))
        self.root.bind("<Escape>", lambda event: self.on_button_click('AC'))

        self.setup_displays()  # Setup physical layout. See function below.
        self.setup_buttons()  # Setup physical layout. See function below.

    def setup_displays(self):
        display_frame = tk.Frame(self.root, bg="#f8f9fa", padx=20, pady=20)  # Creates a container.
        display_frame.pack(fill="x")  # Packs it into a window and stretches horizontally.

        self.entry = tk.Entry(  # Create the main text input field where numbers are typed.
            display_frame, textvariable=self.equation_var,  # Link the input field to our EQUATION variable.
            font=("Helvetica", 24), bg="white", fg="#212529", bd=0, justify="right"
        )
        self.entry.pack(fill="x", ipady=10)  # Packs the input field and gives extra inner vertical padding.
        self.entry.focus_set()  # On startup, place the cursor here.

        # We swap the Label for a Text widget because Text allows us to shrink and lift specific parts of the string!
        self.result_display = tk.Text(
            display_frame, height=1, font=("Helvetica", 32, "bold"),  # Significantly increased base font size
            bg="#f8f9fa", fg=success_color, bd=0, highlightthickness=0, state="disabled"
        )

        # Configure tags for right alignment and true superscript formatting
        self.result_display.tag_configure("right", justify="right")
        self.result_display.tag_configure("superscript", offset=18, font=("Helvetica", 16, "bold"))  # Lift the exponent and shrink it.

        self.result_display.pack(fill="x", pady=(10, 0))  # Pack the result text widget, and add padding.

    def setup_buttons(self):
        btn_frame = tk.Frame(self.root, bg="#f8f9fa")  # Creates a container.
        btn_frame.pack(expand=True, fill="both", padx=15, pady=(0, 15))  # Pack it and make it fill all the remaining space.

        button_layout = (  # A tuple of tuples allows us to spawn these buttons with two nested for loops.
            ('sin(', 'cos(', 'tan(', 'log(', 'AC'),
            ('SHIFT', '(', ')', '^', '⌫'),
            ('7', '8', '9', '/', 'REC'),
            ('4', '5', '6', '*', 'π'),
            ('1', '2', '3', '-', 'e'),
            ('0', '.', '=', '+', 'i')
        )

        for r, row in enumerate(button_layout):
            btn_frame.rowconfigure(r, weight=1)  # Tell the grid to stretch this row equally.
            for c, char in enumerate(row):  # For every column "c",
                btn_frame.columnconfigure(c, weight=1)  # Tell the grid to stretch this column equally.

                font_style = ("Helvetica", 14)

                if char in ['AC', '⌫']:  # Destructive buttons are red.
                    bg_color, fg_color = danger_color, "#ffffff"
                    font_style = ("Helvetica", 14, "bold")
                elif char == '=':
                    bg_color, fg_color = success_color, "#ffffff"
                    font_style = ("Helvetica", 16, "bold")
                elif char in ['/', '*', '-', '+', '^', 'SHIFT']:  # Standard operations and SHIFT
                    bg_color, fg_color = "#e9ecef", "#495057"
                    font_style = ("Helvetica", 16) if char != 'SHIFT' else ("Helvetica", 14, "bold")  # Larger for math, bold for SHIFT.
                elif char == 'REC':  # Specific styling for the new Toggle Button
                    bg_color, fg_color = "#e9ecef", "#495057"
                    font_style = ("Helvetica", 13, "bold")
                elif char in ['π', 'e', 'i']:  # Removed 'φ' from here
                    bg_color, fg_color = "#f3e5f5", "#7b1fa2"
                    font_style = ("Helvetica", 15, "bold" if char == 'i' else "italic")  # Bold 'i' and Italic other constants
                elif char.isalpha() or '(' in char or ')' in char:  # Check if the button is a text function (like sin) or parenthesis
                    bg_color, fg_color = "#e3f2fd", "#1565c0"
                else:  # Only numbers and decimal points are left.
                    bg_color, fg_color = "#ffffff", "#212529"
                    font_style = ("Helvetica", 15, "bold") if char.isdigit() else ("Helvetica", 15)  # Bold numbers, standard decimal.

                btn = tk.Button(  # instantiate the button.
                    btn_frame, text=char, bg=bg_color, fg=fg_color, font=font_style,
                    bd=0, relief="flat", cursor="hand2", activebackground="#dee2e6"  # Removes borders and makes it look nice.
                )

                if char == 'SHIFT':
                    btn.config(command=self.toggle_shift)  # Bind mouse click to the new toggle method
                elif char == 'REC':
                    btn.config(command=self.toggle_mode)  # Bind the mode toggler
                else:
                    btn.config(command=self.create_command(char))  # Assign standard click command using lambda helper. See below.

                btn.grid(row=r, column=c, sticky="nsew", padx=3, pady=3)  # Spawns the button.
                self.buttons[char] = btn  # Saves the button into our already existing dictionary with its base character as the key.

    def create_command(self, char):
        return lambda: self.on_button_click(char)  # Returns an anonymous function that calls the click handler with the specific character.

    def toggle_mode(self):
        self.is_polar_mode = not self.is_polar_mode
        self.buttons['REC'].config(
            text="POL" if self.is_polar_mode else "REC",
            bg="#e3f2fd" if self.is_polar_mode else "#e9ecef",
            fg="#1565c0" if self.is_polar_mode else "#495057"
        )
        self.evaluate_live()  # Instantly re-evaluate to show the format change

    def activate_shift(self, event=None):
        if not self.is_shifted:  # Only run if it's currently OFF.
            self.is_shifted = True
            self.buttons['SHIFT'].config(bg="#ffc107", fg="white")
            self.update_button_labels()  # Call helper to swap all the affected buttons. See below.

    def deactivate_shift(self, event=None):
        if self.is_shifted:  # Only run if it's currently ON.
            self.is_shifted = False
            self.buttons['SHIFT'].config(bg="#e9ecef", fg="#495057")
            self.update_button_labels()  # Call helper to DEswap all the affected buttons. See below.

    def toggle_shift(self):
        if self.is_shifted:
            self.deactivate_shift()
        else:
            self.activate_shift()

    def update_button_labels(self):
        shift_map = {  # Dictionary mapping base functions to their inverse counterparts.
            'sin(': 'asin(',
            'cos(': 'acos(',
            'tan(': 'atan(',
            'log(': 'exp(',
            '^': 'sqrt('
        }

        for base_char, shifted_char in shift_map.items():
            target_char = shifted_char if self.is_shifted else base_char

            self.buttons[base_char].config(
                text=target_char,  # Updates the visual text on the button.
                command=self.create_command(target_char)  # Updates the actual math text it inserts when clicked.
            )

    def update_result_display(self, text, exponent="", color=success_color):
        """Helper method to handle the formatting and insertion of text into the Text widget."""
        self.result_display.config(state="normal", fg=color)
        self.result_display.delete("1.0", tk.END)

        self.result_display.insert(tk.END, text)
        if exponent:
            self.result_display.insert(tk.END, exponent, "superscript")

        self.result_display.tag_add("right", "1.0", "end")
        self.result_display.config(state="disabled")

        # Save a plain-text mathematical equivalent so if the user clicks '=', it drops valid syntax back into the inputfield!
        self.current_result_plain = text + (f"^({exponent})" if exponent else "")

    def on_button_click(self, char):
        current_text = self.equation_var.get()  # We need .get() because self.equation_var is NOT a string but rather contains one!
        if char == 'AC':
            self.equation_var.set("")
        elif char == '⌫':
            self.equation_var.set(current_text[:-1])
        elif char == '=':
            result = self.current_result_plain.replace("= ", "")  # Get the raw string we saved in update_result_display
            if result and result != "...":
                self.equation_var.set(result)  # Move the calculated answer up into the main input box.
                self.update_result_display("")
        else:  # If any normal character button was clicked (numbers, math functions)
            self.equation_var.set(current_text + char)  # Add that character to the end of the existing text.
            self.entry.icursor(tk.END)  # Moves cursor to the end.

    def evaluate_live(self, *args):
        expression = self.equation_var.get()  # We must use .get() because self.equation_var is NOT a string!
        if not expression or not any(character.isalnum() or character in "πφie" for character in expression):
            self.update_result_display("")
            return  # stop here, but function is called at every keystroke.

        # Easter Egg: Before evaluating the maths, check if string matches a key of this dict and return its value.
        easter_eggs = {
            "42": "The meaning of life!",
            "yacc": "Yet Another Complex Calculator",
            "1337": "h4x0r m0d3 0n",
            "ni": "We are the kights who say NI!",
            "cs50": "This was CS50x - Thank you ;-)",
            "(550": "This was CS50x - Thank you ;-)"
        }

        if expression.lower() in easter_eggs:
            self.update_result_display(f"{easter_eggs[expression.lower()]}", color="#ffc107")
            return # stop here, but function is called at every keystroke.

        if "pi" in expression or "phi" in expression:
            expression = expression.replace("pi", "π").replace("phi", "φ")  # Instantly replace pi or phi them with the actual greek letters.
            self.equation_var.set(expression)
            self.entry.icursor(tk.END)  # Keep the cursor at the end to prevent interruptions while typing.

        try:  # Start a big try block to stop ANY error from crashing the live calculator. If any error is not catched, the live trace stops.
            expression = expression.replace('^', '**')  # Swaps the '^' exponent symbol for Python's '**' symbol

            # Start implicit multiplication, making "2π" to be considered "2*π" for isntance.
            funcs = ["asin", "acos", "atan", "sin", "cos", "tan", "log", "exp", "sqrt", "abs"]  # List of "all" math functions.
            for index, func in enumerate(funcs):  # Loop to place safety net.
                expression = expression.replace(func, f"_{index}_")  # Temporarily replacing functions with safe dummy markers like '_exp_'

            # The following r strings have had AI assistance.
            expression = re.sub(r'(\d+\.?\d*)\s*(?=[ieπφ])', r'\1*', expression)  # Intercepts '2π' or '3.5e' and injects a '*' in between.
            expression = re.sub(r'([ieπφ])\s*(?=\d)', r'\1*', expression)         # Intercepts 'π2' or 'e3.5' and injects a '*' in between.
            expression = re.sub(r'([ieπφ])\s*(?=[ieπφ])', r'\1*', expression)     # Intercepts 'πe' or 'eφ' and injects a '*' in between.
            expression = re.sub(r'(\d+\.?\d*)\s*(?=\()', r'\1*', expression)      # Intercepts '2(' and injects '*'
            expression = re.sub(r'\)\s*(?=\()', r')*', expression)                # Intercepts ')(' and injects '*'
            expression = re.sub(r'\)\s*(?=\d)', r')*', expression)                # Intercepts ')2' and injects '*'
            expression = re.sub(r'\)\s*(?=[ieπφ])', r')*', expression)            # Intercepts ')π' or ')e' and injects '*'
            expression = re.sub(r'([ieπφ])\s*(?=\()', r'\1*', expression)         # Intercepts 'π(' or 'i(' and injects '*'
            expression = re.sub(r'([ieπφ\d\)])\s*(?=_\d+_)', r'\1*', expression)  # Allows composing functions with constants.

            for index, func in enumerate(funcs):  # Loop to remove the sefety net.
                expression = expression.replace(f"_{index}_", func)  # Restoring all the dummy markers back to their real function names.

            def smart_sqrt(x):  # Defining our own sqrt() function that accepts negative and complex numbers, using the proper lib for each case.
                if isinstance(x, complex) or x < 0:
                    return cmath.sqrt(x)
                return math.sqrt(x)

            # Count open and closed parentheses to auto-close them for the background eval
            open_parens = expression.count('(')
            closed_parens = expression.count(')')
            if open_parens > closed_parens:
                expression += ')' * (open_parens - closed_parens)
            expression = expression.replace("*()", "") # Prevents python from evaluating empty tuples

            safe_functions = {  # User input is restricted to functions in this dict to prevent unwanted system functions to be injected.
                "sin": cmath.sin, "cos": cmath.cos, "tan": cmath.tan,
                "asin": cmath.asin, "acos": cmath.acos, "atan": cmath.atan,
                "log": cmath.log10, "exp": cmath.exp, "sqrt": smart_sqrt,
                "abs": abs, "phase": cmath.phase, "π": math.pi, "e": math.e,
                "φ": (1 + math.sqrt(5)) / 2, # Note: φ is fully mathematically supported here!
                "i": 1j  # Python's native imaginary unit is denoted '1j'.
            }

            # Runs the math expression securely, completely blocking dangerous system built-ins.
            # Global parameter is a mask {} to prevent python __builtins__ to be called.
            # Local parameter is the dictionary just above.
            # More info at: https://realpython.com/python-eval-function/
            result = eval(expression, {"__builtins__": {}}, safe_functions)

            # Now we format the answer to be human friendly.
            # Changes to apply to complex numbers:
            if isinstance(result, complex):

                if self.is_polar_mode:
                    r, theta = cmath.polar(result)  # Extracts radius and angle (in radians)

                    r = round(r, 8)  # Rounding to prevent floating point glitches.

                    theta_pi = theta / math.pi  # Divide theta by pi to find the coefficient
                    theta_pi = round(theta_pi, 8)

                    # Clean up .0 from integers
                    r = int(r) if r.is_integer() else r
                    theta_pi = int(theta_pi) if theta_pi.is_integer() else theta_pi

                    if r == 0:
                        self.update_result_display("= 0")
                    else:
                        # Format the exponent strings to drop the '1' if it's exactly 1π or -1π
                        if theta_pi == 1:
                            exponent_str = "πi"
                        elif theta_pi == -1:
                            exponent_str = "-πi"
                        elif theta_pi == 0:
                            exponent_str = "0"
                        else:
                            exponent_str = f"{theta_pi}πi"

                        # Use our helper function to append the exponent formatting natively
                        self.update_result_display(f"= {r} e", exponent=exponent_str)

                else:  # If cartesian mode.
                    # Rounding to prevent floating point glitches.
                    real_part = round(result.real, 8)
                    imag_part = round(result.imag, 8)

                    # Convert to int type if indeed an integer.
                    real_part = int(real_part) if real_part.is_integer() else real_part
                    imag_part = int(imag_part) if imag_part.is_integer() else imag_part

                    # A number whose imaginary part is zero can still have type "complex". So we have to do all checks:
                    if real_part == 0 and imag_part == 0:
                        display_str = "0"
                    elif real_part == 0:
                        if imag_part == 1:
                            display_str = "i"
                        elif imag_part == -1:
                            display_str = "-i"
                        else:
                            display_str = f"{imag_part}i"
                    elif imag_part == 0:
                        display_str = str(real_part)
                    else:  # If it has both real and imaginary parts
                        sign = "+" if imag_part > 0 else "-"
                        abs_imag = abs(imag_part)
                        imag_str = "i" if abs_imag == 1 else f"{abs_imag}i"
                        display_str = f"{real_part} {sign} {imag_str}"  # Build the final "a + bi" string layout.

                    self.update_result_display(f"= {display_str}")

            # Changes to apply to non complex numbers:
            else:
                if isinstance(result, float) and result.is_integer():  # Check if it's a decimal that behaves exactly like a whole number
                    result = int(result)
                elif isinstance(result, float):  # If it truly is a decimal number
                    result = round(result, 8)  # To prevent floating point glitches we limit to 8 decimals.
                self.update_result_display(f"= {result}")  # Send the cleaned normal number to the screen label.

        except Exception:
            self.update_result_display("...", color="#adb5bd")  # Instead of crashing the trace, just show three dots indicating it's waiting for more input

if __name__ == "__main__":
    root = tk.Tk()
    app = Calculator(root)
    root.mainloop()
