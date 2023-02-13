import json
import re
from pathlib import Path
from typing import Iterable, List

from cookiecutter.main import cookiecutter
from gherkin.parser import Parser
from gherkin.token_scanner import TokenScanner
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_all_styles

LEXER = get_lexer_by_name("gherkin", stripall=True)
STYLES = get_all_styles()


def generate(style: str = "default") -> bool:
    print("generating...")
    if style not in STYLES:
        raise ValueError(f"Style must be one of {STYLES}, got '{style}'")
    for feature_file_path in _get_feature_filenames():
        success = _generate_documentation(
            feature_file_path=feature_file_path, style=style
        )
        if success:
            print(f"Created HTML from {feature_file_path}")
        else:
            print(f"Skipped technical file {feature_file_path}")
    print("generated...")


def _get_feature_filenames() -> Iterable[Path]:
    yield from Path(".").glob("feature_tests/features/**/*.feature")


def _generate_documentation(feature_file_path: Path, style: str) -> bool:
    raw_lines = _read_raw_feature_doc_lines(feature_file_path)
    feature_doc = _parse_gherkin_features(feature_file_path)
    if _is_technical(feature_doc):
        return False

    feature_doc["display"] = _prettify_sections(
        feature_doc=feature_doc, raw_lines=raw_lines, style=style
    )
    cookiecutter(
        "packages/cookiecutter-templates/cucumber_features",
        extra_context={"current": feature_doc},
        overwrite_if_exists=True,
        output_dir="report/",
        no_input=True,
    )
    return True


def _is_technical(feature_obj: dict) -> bool:
    return "@technical" in [i.get("name") for i in feature_obj.get("tags", [])]


def _read_raw_feature_doc_lines(feature_file_path: Path) -> List[str]:
    with open(feature_file_path, "r") as f:
        raw_lines = f.read().splitlines()
    return raw_lines


def _parse_gherkin_features(path: str) -> dict:
    return Parser().parse(TokenScanner(path))["feature"]


def _highlight_text(text: str, style: str) -> str:
    formatter = HtmlFormatter(
        linenos="inline",
        noclasses=True,
        full=False,
        style=style,
        anchorlinenos=False,
        lineanchors=False,
        wrapcode=True,
        debug_token_types=False,
        lineseparator="<br></br>",
    )
    return highlight(code=text, lexer=LEXER, formatter=formatter).replace("\n", "")


def _get_scenario_line_range(scenario: dict) -> str:
    first_line = int(scenario["location"]["line"])
    last_step = scenario["steps"][-1]
    lines = (
        len(last_step["docString"]["content"].split("\n")) + 2
        if "docString" in last_step
        else 1
    )
    last_line = int(last_step["location"]["line"]) + lines
    if "dataTable" in last_step.keys():
        last_line = last_step["dataTable"]["rows"][-1]["location"]["line"]
    return first_line, last_line


def _cleanup(raw_feature_doc_lines):
    return "\n".join(
        map(
            lambda line: line.replace("#", "@"),
            raw_feature_doc_lines,
        )
    )


def _clean_and_highlight_scenario(scenario: dict, raw_lines: List[str], style: str):
    if scenario["keyword"] == "X":
        return ""
    first_line, last_line = _get_scenario_line_range(scenario)
    text = _cleanup(raw_lines[first_line:last_line])
    return _highlight_text(text=text, style=style)


def _prettify_sections(feature_doc: dict, raw_lines: List[str], style: str) -> dict:

    sections = []
    for child in feature_doc["children"]:
        scenario = child.get("background", child.get("scenario", {}))
        if _is_technical(scenario) or "@technical" in child.get("description", ""):
            continue

        scenario["highlight"] = _clean_and_highlight_scenario(
            scenario=scenario, raw_lines=raw_lines, style=style
        )
        sections.append(scenario)
    return sections
