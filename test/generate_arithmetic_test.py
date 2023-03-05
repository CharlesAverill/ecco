import random
from pathlib import Path

def generate_arithmetic_test(n: int):
    out = ""
    expected_out = ""

    for _ in range(n):
        ops = ["+", "-", "*"] #, "//"]

        def get_subexpression(left_subst = None):
            op = random.choice(ops)
            min_val = 1 if op == "//" else 0
            left = random.randint(min_val, 10) if not left_subst else left_subst
            return f"{left} {op} {random.randint(0, 10)}"
        
        last_expr = get_subexpression()
        for i in range(random.randint(5, 10)):
            last_expr = get_subexpression(last_expr)

        out += f"\tprint {last_expr}; // {eval(last_expr)}\n"
        expected_out += f"{eval(last_expr)}\n"

    out = "int main() {\n" + out.replace("(", "").replace(")", "") + "}"

    with open(Path(__file__).parents[1] / "examples" / "arith_test", "w") as file:
        file.write(out)

    return expected_out
