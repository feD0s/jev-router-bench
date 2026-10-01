"""Local harness checks: navigation and import boundaries, no network."""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bench.core import check_freeze


def main():
    check_freeze()
    if len((ROOT / "AGENTS.md").read_text().splitlines()) > 100:
        raise ValueError("AGENTS.md must stay a short map")
    if (ROOT / ".github/workflows").exists():
        raise ValueError("Owner requested no CI/CD workflows")
    for path in [ROOT / "AGENTS.md", ROOT / "README.md", ROOT / "ARCHITECTURE.md", *ROOT.glob("docs/**/*.md")]:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if "://" in target or target.startswith("#"):
                continue
            if not (path.parent / target.split("#")[0]).exists():
                raise ValueError(f"Broken documentation link in {path.relative_to(ROOT)}: {target}")
    allowed = {
        "core": set(), "adapters": {"core"}, "transport": set(), "metrics": {"core"},
        "runner": {"core", "adapters", "transport"}, "report": {"core", "metrics"},
        "estimate": {"core", "adapters"}, "__main__": {"core", "estimate", "report", "runner"}, "__init__": set()}
    for path in (ROOT / "bench").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.level:
                if node.module not in allowed[path.stem]:
                    raise ValueError(f"Forbidden dependency: {path.stem} -> {node.module}")
            modules = [n.name.split(".")[0] for n in node.names] if isinstance(node, ast.Import) else [node.module.split(".")[0]] if isinstance(node, ast.ImportFrom) and not node.level else []
            for module in modules:
                if module not in sys.stdlib_module_names:
                    raise ValueError(f"Unexpected dependency: {module}")
                if module in ("urllib", "http", "socket", "multiprocessing") and path.stem != "transport":
                    raise ValueError(f"Network boundary violation: {path.stem} imports {module}")
    print("Local documentation, freeze, stdlib and architecture checks passed")


if __name__ == "__main__":
    main()
