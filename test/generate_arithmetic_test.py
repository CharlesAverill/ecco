import random
from pathlib import Path

def generate_arithmetic_test(n: int, stdout: bool = False):
    out = ""
    expected_out = ""

    for _ in range(n):
        ops = ["+", "-", "*", "//"]

        def get_subexpression(left_subst = None):
            op = random.choice(ops)
            left = random.randint(0, 10) if not left_subst else left_subst
            right = random.randint(0, 10)
            if not left_subst:
                return f"{left} {op} {right}"
            elif random.randint(0, 1) == 0:
                return f"({left}) {op} {right}"
            else:
                return f"{left} {op} {right}"
            
        def get_expr():
            last_expr = get_subexpression()
            for i in range(random.randint(5, 10)):
                last_expr = get_subexpression(last_expr)
            return last_expr
        
        didnt_get_dbz = False
        while not didnt_get_dbz:
            try:
                last_expr = get_expr()
                expected_out += f"{eval(last_expr)}\n"
                # Clever trick to avoid collision between C comment syntax and Python division syntax
                out += f"\tprintint({last_expr}); //// {eval(last_expr)}\n"
                didnt_get_dbz = True
            except ZeroDivisionError:
                pass

    out = "int main() {\n" + out + "}"
    out = out.replace("//", "/")
    # out = out.replace("(", "").replace(")", "") + "}"

    if stdout:
        print(out)
    else:
        with open(Path(__file__).parents[1] / "examples" / "test_arithmetic", "w") as file:
            file.write(out)

    return expected_out

if __name__ == "__main__":
    generate_arithmetic_test(5, True)
