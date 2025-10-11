# GitHub Actions Workflow Tests

This directory contains comprehensive tests for validating GitHub Actions workflow files.

## Test Coverage

### 1. YAML Structure Tests (`TestWorkflowYAMLStructure`)
- Validates YAML syntax
- Checks for required fields (name, on, jobs)
- Ensures descriptive workflow names
- Verifies at least one job is defined

### 2. Terraform Workflow Tests (`TestTerraformWorkflow`)
- Validates terraform.yml structure
- Checks for proper step ordering (init before validate/plan)
- Ensures security scanning (tfsec) is present
- Validates AWS credential configuration
- Confirms terraform apply only runs on main branch
- Checks for ZAP security scanning
- Validates health check logic

### 3. Embedded Shell Script Tests (`TestEmbeddedShellScripts`)
- Validates shell script syntax
- Tests health check timeout mechanisms
- Ensures proper exit codes
- Validates output formatting

### 4. Security Best Practices Tests (`TestWorkflowSecurityBestPractices`)
- Ensures no secret files in repository
- Checks for hardcoded credentials
- Validates action version pinning
- Tests permission definitions

### 5. Workflow Trigger Tests (`TestWorkflowTriggers`)
- Validates trigger configurations
- Checks environment variable definitions

### 6. Artifact Tests (`TestWorkflowArtifacts`)
- Validates artifact upload configurations

## Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
python3 -m unittest discover -s workflows -p "test_*.py" -v

# Or use the test runner script
./run_tests.sh
```

## Adding New Tests

When adding new workflow files or modifying existing ones:

1. Add test cases to validate new functionality
2. Ensure security best practices are tested
3. Validate any embedded shell scripts
4. Test error handling and edge cases

## Test Principles

- **Bias for Action**: All workflow changes should have corresponding tests
- **Security First**: Always test for credential leaks and security misconfigurations
- **Validation Over Execution**: Test configuration validity, not execution
- **Comprehensive Coverage**: Test happy paths, edge cases, and failure scenarios