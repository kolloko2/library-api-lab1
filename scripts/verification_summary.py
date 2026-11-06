from pathlib import Path
import xml.etree.ElementTree as ET


def main():
    suite = ET.parse(Path("artifacts/junit.xml")).getroot().find("testsuite")
    coverage = ET.parse(Path("artifacts/coverage.xml")).getroot()
    print(
        "Tests:",
        suite.attrib["tests"],
        "Failures:",
        suite.attrib["failures"],
        "Errors:",
        suite.attrib["errors"],
    )
    print("Application statement coverage:", round(float(coverage.attrib["line-rate"]) * 100, 2), "%")


if __name__ == "__main__":
    main()
