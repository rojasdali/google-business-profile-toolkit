import ast
import os

MAX_LINES = 120
MAX_COMPLEXITY = 10


def _calculate_complexity(node: ast.AST) -> int:
    """Calculates cyclomatic complexity for an AST node."""
    count = 1
    for child in ast.walk(node):
        if isinstance(
            child,
            (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With, ast.Assert),
        ):
            count += 1
        elif isinstance(child, ast.BoolOp):
            count += len(child.values) - 1
    return count


def test_python_modularity_and_complexity():
    """Enforces strict module line limits (<120) and cyclomatic complexity (<=10)."""
    src_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "src",
        "gbp_toolkit",
    )
    violations = []

    for root, _, files in os.walk(src_dir):
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            rel_path = os.path.relpath(path, src_dir)

            with open(path, "r", encoding="utf-8") as fh:
                lines = fh.readlines()

            if len(lines) > MAX_LINES:
                violations.append(f"{rel_path}: {len(lines)} lines exceeds max {MAX_LINES}")

            tree = ast.parse("".join(lines), filename=path)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    c = _calculate_complexity(node)
                    if c > MAX_COMPLEXITY:
                        violations.append(f"{rel_path}::{node.name}: complexity {c} exceeds max {MAX_COMPLEXITY}")

    assert not violations, "Modularity violations found:\n" + "\n".join(violations)
