#!/usr/bin/env python3
"""
Test suite for dependency scanning and SBOM generation.
Tests TASK-SEC-010: Implement Dependency Scanning and SBOM Generation
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from backend.core.dependency_scanner import (
    DependencyScanner,
    scan_dependencies,
    generate_sbom,
    check_vulnerabilities,
    Dependency,
    Vulnerability,
)


@pytest.fixture
def dependency_scanner():
    """Create a dependency scanner instance for testing."""
    return DependencyScanner()


def test_dependency_scanner_initialization(dependency_scanner):
    """Test that DependencyScanner initializes correctly."""
    assert dependency_scanner is not None
    assert hasattr(dependency_scanner, "dependencies")
    assert hasattr(dependency_scanner, "vulnerability_db")
    assert isinstance(dependency_scanner.dependencies, list)
    assert isinstance(dependency_scanner.vulnerability_db, dict)


def test_dependency_creation():
    """Test creation of Dependency objects."""
    dep = Dependency(
        name="fastapi",
        version="0.95.2",
        license="MIT",
        source="pypi",
        dependencies=["starlette", "pydantic"],
    )

    assert dep.name == "fastapi"
    assert dep.version == "0.95.2"
    assert dep.license == "MIT"
    assert dep.source == "pypi"
    assert dep.dependencies == ["starlette", "pydantic"]
    assert dep.is_direct is True


def test_vulnerability_creation():
    """Test creation of Vulnerability objects."""
    vuln = Vulnerability(
        id="CVE-2023-1234",
        package="fastapi",
        version="0.95.2",
        severity="HIGH",
        description="Remote code execution vulnerability",
        fixed_version="0.95.3",
        cvss_score=8.5,
        references=["https://nvd.nist.gov/vuln/detail/CVE-2023-1234"],
    )

    assert vuln.id == "CVE-2023-1234"
    assert vuln.package == "fastapi"
    assert vuln.version == "0.95.2"
    assert vuln.severity == "HIGH"
    assert vuln.description == "Remote code execution vulnerability"
    assert vuln.fixed_version == "0.95.3"
    assert vuln.cvss_score == 8.5
    assert vuln.references == ["https://nvd.nist.gov/vuln/detail/CVE-2023-1234"]


def test_scan_dependencies_basic(dependency_scanner):
    """Test basic dependency scanning functionality."""
    # Mock the subprocess call to pip freeze
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock()
        mock_run.return_value.stdout = "fastapi==0.95.2\nstarlette==0.20.4\npydantic==1.10.7"
        mock_run.return_value.returncode = 0

        # Mock the requests call for vulnerability data
        with patch("requests.get") as mock_get:
            mock_get.return_value = MagicMock()
            mock_get.return_value.json.return_value = {"results": [], "totalResults": 0}
            mock_get.return_value.status_code = 200

            result = scan_dependencies()

            # Verify dependencies were scanned
            assert len(result) == 3
            assert any(dep.name == "fastapi" for dep in result)
            assert any(dep.name == "starlette" for dep in result)
            assert any(dep.name == "pydantic" for dep in result)


def test_generate_sbom_basic(dependency_scanner):
    """Test basic SBOM generation."""
    # Add some test dependencies
    dep1 = Dependency("fastapi", "0.95.2", "MIT", "pypi")
    dep2 = Dependency("starlette", "0.20.4", "BSD-3-Clause", "pypi")

    dependency_scanner.dependencies = [dep1, dep2]

    # Generate SBOM
    sbom = generate_sbom(dependency_scanner.dependencies)

    # Verify SBOM structure
    assert "bomFormat" in sbom
    assert "specVersion" in sbom
    assert "version" in sbom
    assert "metadata" in sbom
    assert "components" in sbom

    # Verify components
    assert len(sbom["components"]) == 2
    fastapi_comp = next(c for c in sbom["components"] if c["name"] == "fastapi")
    assert fastapi_comp["version"] == "0.95.2"
    assert fastapi_comp["licenseDeclared"] == "MIT"


def test_check_vulnerabilities_found(dependency_scanner):
    """Test vulnerability detection with actual vulnerabilities."""
    # Add a vulnerable dependency
    dep = Dependency("fastapi", "0.95.2", "MIT", "pypi")
    dependency_scanner.dependencies = [dep]

    # Mock vulnerability database
    dependency_scanner.vulnerability_db = {
        "fastapi": [
            {
                "id": "CVE-2023-1234",
                "version": "0.95.2",
                "severity": "HIGH",
                "description": "Remote code execution vulnerability",
                "fixed_version": "0.95.3",
            }
        ]
    }

    # Check for vulnerabilities
    vulnerabilities = check_vulnerabilities(dependency_scanner.dependencies, dependency_scanner.vulnerability_db)

    # Verify vulnerability was found
    assert len(vulnerabilities) == 1
    assert vulnerabilities[0].id == "CVE-2023-1234"
    assert vulnerabilities[0].package == "fastapi"
    assert vulnerabilities[0].severity == "HIGH"


def test_check_vulnerabilities_none(dependency_scanner):
    """Test vulnerability detection with no vulnerabilities."""
    # Add a clean dependency
    dep = Dependency("fastapi", "0.95.3", "MIT", "pypi")
    dependency_scanner.dependencies = [dep]

    # Mock empty vulnerability database
    dependency_scanner.vulnerability_db = {}

    # Check for vulnerabilities
    vulnerabilities = check_vulnerabilities(dependency_scanner.dependencies, dependency_scanner.vulnerability_db)

    # Verify no vulnerabilities found
    assert len(vulnerabilities) == 0


def test_generate_sbom_with_vulnerabilities(dependency_scanner):
    """Test SBOM generation including vulnerability information."""
    # Add dependencies with vulnerabilities
    dep1 = Dependency("fastapi", "0.95.2", "MIT", "pypi")
    dep2 = Dependency("starlette", "0.20.4", "BSD-3-Clause", "pypi")
    dependency_scanner.dependencies = [dep1, dep2]

    # Add vulnerabilities
    dependency_scanner.vulnerability_db = {
        "fastapi": [
            {
                "id": "CVE-2023-1234",
                "version": "0.95.2",
                "severity": "HIGH",
                "description": "Remote code execution vulnerability",
                "fixed_version": "0.95.3",
            }
        ]
    }

    # Generate SBOM with vulnerability info
    sbom = generate_sbom(
        dependency_scanner.dependencies,
        include_vulnerabilities=True,
        scanner=dependency_scanner,
    )

    # Verify vulnerabilities are included
    assert "vulnerabilities" in sbom
    assert len(sbom["vulnerabilities"]) == 1
    assert sbom["vulnerabilities"][0]["id"] == "CVE-2023-1234"


def test_scan_dependencies_with_error_handling(dependency_scanner):
    """Test dependency scanning with error handling."""
    # Mock subprocess call that fails
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock()
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "Error: pip not found"

        # Should not raise exception, return empty list
        result = scan_dependencies()
        assert result == []


def test_generate_sbom_file_output():
    """Test SBOM generation to file."""
    # Create test dependencies
    deps = [
        Dependency("fastapi", "0.95.2", "MIT", "pypi"),
        Dependency("starlette", "0.20.4", "BSD-3-Clause", "pypi"),
    ]

    # Generate SBOM to temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_path = f.name

    try:
        generate_sbom(deps, output_file=temp_path)

        # Verify file was created and contains valid JSON
        assert os.path.exists(temp_path)
        with open(temp_path, "r") as f:
            sbom_content = json.load(f)
            assert "components" in sbom_content
            assert len(sbom_content["components"]) == 2
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_dependency_scanner_update_vulnerability_db(dependency_scanner):
    """Test updating vulnerability database."""
    # Mock requests to vulnerability database
    with patch("requests.get") as mock_get:
        # Mock response for fastapi vulnerabilities
        fastapi_vulns = {
            "results": [
                {
                    "vulnerabilities": [
                        {
                            "cve": {"id": "CVE-2023-1234"},
                            "cvssMetricV31": [{"cvssData": {"baseScore": 8.5}}],
                            "descriptions": [{"value": "Remote code execution"}],
                            "published": "2023-01-01T00:00:00Z",
                        }
                    ]
                }
            ]
        }

        mock_get.return_value = MagicMock()
        mock_get.return_value.json.side_effect = [fastapi_vulns, {"results": []}]
        mock_get.return_value.status_code = 200

        # Update vulnerability database
        dependency_scanner.update_vulnerability_database(["fastapi", "starlette"])

        # Verify database was updated
        assert "fastapi" in dependency_scanner.vulnerability_db
        assert len(dependency_scanner.vulnerability_db["fastapi"]) == 1
        assert dependency_scanner.vulnerability_db["fastapi"][0]["id"] == "CVE-2023-1234"


def test_generate_compliance_report(dependency_scanner):
    """Test compliance report generation."""
    # Add test dependencies with mixed vulnerability status
    deps = [
        Dependency("fastapi", "0.95.2", "MIT", "pypi"),
        Dependency("starlette", "0.20.4", "BSD-3-Clause", "pypi"),
        Dependency("pydantic", "1.10.7", "MIT", "pypi"),
    ]
    dependency_scanner.dependencies = deps

    # Add some vulnerabilities
    dependency_scanner.vulnerability_db = {
        "fastapi": [
            {
                "id": "CVE-2023-1234",
                "version": "0.95.2",
                "severity": "HIGH",
                "description": "Remote code execution vulnerability",
                "fixed_version": "0.95.3",
            }
        ],
        "starlette": [
            {
                "id": "CVE-2023-5678",
                "version": "0.20.4",
                "severity": "MEDIUM",
                "description": "Denial of service vulnerability",
                "fixed_version": "0.20.5",
            }
        ],
    }

    # Generate compliance report
    report = dependency_scanner.generate_compliance_report()

    # Verify report structure
    assert "total_dependencies" in report
    assert "vulnerable_dependencies" in report
    assert "critical_vulnerabilities" in report
    assert "high_vulnerabilities" in report
    assert "medium_vulnerabilities" in report
    assert "low_vulnerabilities" in report
    assert "compliance_status" in report

    # Verify counts
    assert report["total_dependencies"] == 3
    assert report["vulnerable_dependencies"] == 2
    assert report["high_vulnerabilities"] == 1
    assert report["medium_vulnerabilities"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
