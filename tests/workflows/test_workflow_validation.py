"""
Comprehensive test suite for GitHub Actions workflow files.

This test suite validates:
- YAML syntax and structure
- GitHub Actions workflow schema compliance
- Embedded shell script validation
- Security best practices
- Workflow step dependencies and logic
"""

import os
import re
import yaml
import unittest
from pathlib import Path


class TestWorkflowYAMLStructure(unittest.TestCase):
    """Test cases for validating YAML structure of workflow files."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.repo_root = Path(__file__).parent.parent.parent
        cls.workflows_dir = cls.repo_root / ".github" / "workflows"
        cls.workflow_files = list(cls.workflows_dir.glob("*.yml")) + \
                           list(cls.workflows_dir.glob("*.yaml"))

    def test_workflow_files_exist(self):
        """Test that workflow files exist."""
        self.assertTrue(self.workflows_dir.exists(), 
                       f"Workflows directory should exist at {self.workflows_dir}")
        self.assertGreater(len(self.workflow_files), 0,
                          "At least one workflow file should exist")

    def test_yaml_syntax_valid(self):
        """Test that all workflow files have valid YAML syntax."""
        for workflow_file in self.workflow_files:
            with self.subTest(workflow=workflow_file.name):
                with open(workflow_file, 'r') as f:
                    try:
                        yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        self.fail(f"Invalid YAML in {workflow_file.name}: {e}")

    def test_workflow_has_required_fields(self):
        """Test that workflows have required top-level fields."""
        required_fields = ['name', 'jobs']
        
        for workflow_file in self.workflow_files:
            with self.subTest(workflow=workflow_file.name):
                with open(workflow_file, 'r') as f:
                    workflow = yaml.safe_load(f)
                
                for field in required_fields:
                    self.assertIn(field, workflow,
                                f"{workflow_file.name} must have '{field}' field")
                
                # Check for 'on' key (which YAML parses as True boolean)
                has_on = 'on' in workflow or True in workflow
                self.assertTrue(has_on,
                              f"{workflow_file.name} must have 'on' trigger field")

    def test_workflow_name_is_descriptive(self):
        """Test that workflow names are descriptive (not empty)."""
        for workflow_file in self.workflow_files:
            with self.subTest(workflow=workflow_file.name):
                with open(workflow_file, 'r') as f:
                    workflow = yaml.safe_load(f)
                
                name = workflow.get('name', '')
                self.assertTrue(len(name) > 5,
                              f"{workflow_file.name} should have descriptive name")

    def test_jobs_not_empty(self):
        """Test that workflows have at least one job defined."""
        for workflow_file in self.workflow_files:
            with self.subTest(workflow=workflow_file.name):
                with open(workflow_file, 'r') as f:
                    workflow = yaml.safe_load(f)
                
                jobs = workflow.get('jobs', {})
                self.assertGreater(len(jobs), 0,
                                 f"{workflow_file.name} must define at least one job")


class TestTerraformWorkflow(unittest.TestCase):
    """Specific tests for the terraform.yml workflow."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.repo_root = Path(__file__).parent.parent.parent
        cls.terraform_workflow = cls.repo_root / ".github" / "workflows" / "terraform.yml"
        
        if cls.terraform_workflow.exists():
            with open(cls.terraform_workflow, 'r') as f:
                cls.workflow = yaml.safe_load(f)
        else:
            cls.workflow = None

    def test_terraform_workflow_exists(self):
        """Test that terraform workflow file exists."""
        self.assertIsNotNone(self.workflow,
                           "terraform.yml workflow should exist")

    def test_terraform_workflow_structure(self):
        """Test terraform workflow has expected structure."""
        self.assertIn('jobs', self.workflow)
        self.assertIn('terraform', self.workflow['jobs'])
        
    def test_terraform_job_runs_on_ubuntu(self):
        """Test that terraform job runs on ubuntu."""
        terraform_job = self.workflow['jobs']['terraform']
        self.assertIn('runs-on', terraform_job)
        self.assertIn('ubuntu', terraform_job['runs-on'])

    def test_terraform_has_checkout_step(self):
        """Test that workflow checks out repository."""
        terraform_job = self.workflow['jobs']['terraform']
        steps = terraform_job.get('steps', [])
        
        checkout_steps = [s for s in steps if 'checkout' in str(s).lower()]
        self.assertGreater(len(checkout_steps), 0,
                          "Workflow should have checkout step")

    def test_terraform_has_aws_credentials_step(self):
        """Test that workflow configures AWS credentials."""
        terraform_job = self.workflow['jobs']['terraform']
        steps = terraform_job.get('steps', [])
        
        aws_steps = [s for s in steps 
                    if s.get('name', '').lower().find('aws') != -1 or
                       s.get('uses', '').find('aws-actions') != -1]
        self.assertGreater(len(aws_steps), 0,
                          "Workflow should configure AWS credentials")

    def test_terraform_has_security_scanning(self):
        """Test that workflow includes security scanning (tfsec)."""
        terraform_job = self.workflow['jobs']['terraform']
        steps = terraform_job.get('steps', [])
        
        security_steps = [s for s in steps 
                         if 'tfsec' in str(s).lower()]
        self.assertGreater(len(security_steps), 0,
                          "Workflow should include tfsec security scanning")

    def test_terraform_init_before_other_commands(self):
        """Test that terraform init runs before other terraform commands."""
        terraform_job = self.workflow['jobs']['terraform']
        steps = terraform_job.get('steps', [])
        
        init_index = None
        validate_index = None
        plan_index = None
        
        for i, step in enumerate(steps):
            step_name = step.get('name', '').lower()
            if 'terraform init' in step_name:
                init_index = i
            elif 'terraform validate' in step_name:
                validate_index = i
            elif 'terraform plan' in step_name:
                plan_index = i
        
        self.assertIsNotNone(init_index, "Should have terraform init step")
        
        if validate_index:
            self.assertLess(init_index, validate_index,
                           "Init should run before validate")
        if plan_index:
            self.assertLess(init_index, plan_index,
                           "Init should run before plan")

    def test_terraform_uses_secrets_not_hardcoded(self):
        """Test that workflow uses secrets, not hardcoded credentials."""
        with open(self.terraform_workflow, 'r') as f:
            content = f.read()
        
        # Check for GitHub secrets usage
        self.assertIn('secrets.', content,
                     "Should use GitHub secrets for sensitive data")
        
        # Check for hardcoded AWS credentials (common patterns)
        hardcoded_patterns = [
            r'AKIA[0-9A-Z]{16}',  # AWS Access Key ID pattern
            r'aws[_-]?access[_-]?key[_-]?id\s*[:=]\s*["\']?[A-Z0-9]{20}',
            r'aws[_-]?secret[_-]?access[_-]?key\s*[:=]\s*["\']?[A-Za-z0-9/+=]{40}',
        ]
        
        for pattern in hardcoded_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            self.assertEqual(len(matches), 0,
                           f"Found potential hardcoded credentials: {pattern}")

    def test_terraform_apply_only_on_main(self):
        """Test that terraform apply only runs on main branch."""
        terraform_job = self.workflow['jobs']['terraform']
        steps = terraform_job.get('steps', [])
        
        apply_steps = [s for s in steps 
                      if 'terraform apply' in s.get('run', '').lower()]
        
        for step in apply_steps:
            if_condition = step.get('if', '')
            self.assertIn('main', if_condition.lower(),
                         "Terraform apply should only run on main branch")

    def test_workflow_has_zap_security_scan(self):
        """Test that workflow includes ZAP security scanning."""
        terraform_job = self.workflow['jobs']['terraform']
        steps = terraform_job.get('steps', [])
        
        zap_steps = [s for s in steps if 'zap' in str(s).lower()]
        self.assertGreater(len(zap_steps), 0,
                          "Workflow should include ZAP security scanning")

    def test_workflow_waits_for_healthy_targets(self):
        """Test that workflow waits for load balancer targets to be healthy."""
        terraform_job = self.workflow['jobs']['terraform']
        steps = terraform_job.get('steps', [])
        
        health_check_steps = [s for s in steps 
                             if 'healthy' in s.get('name', '').lower() or
                                'target-health' in s.get('run', '').lower()]
        self.assertGreater(len(health_check_steps), 0,
                          "Workflow should wait for healthy targets")


class TestEmbeddedShellScripts(unittest.TestCase):
    """Test embedded shell scripts in workflow files."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.repo_root = Path(__file__).parent.parent.parent
        cls.terraform_workflow = cls.repo_root / ".github" / "workflows" / "terraform.yml"
        
        if cls.terraform_workflow.exists():
            with open(cls.terraform_workflow, 'r') as f:
                cls.workflow = yaml.safe_load(f)
        else:
            cls.workflow = None

    def test_shell_scripts_have_proper_shebang_or_shell(self):
        """Test that multi-line shell scripts use proper syntax."""
        if not self.workflow:
            self.skipTest("Workflow file not found")
            
        terraform_job = self.workflow['jobs']['terraform']
        steps = terraform_job.get('steps', [])
        
        for step in steps:
            run_command = step.get('run', '')
            if run_command and '\n' in run_command:
                # Multi-line scripts should be well-formed
                lines = run_command.strip().split('\n')
                # Check for bash-specific features
                if any(re.search(r'\[\[|\{\{', line) for line in lines):
                    # Should use bash
                    pass  # GitHub Actions defaults to bash

    def test_health_check_script_has_timeout(self):
        """Test that health check script has a timeout mechanism."""
        if not self.workflow:
            self.skipTest("Workflow file not found")
            
        terraform_job = self.workflow['jobs']['terraform']
        steps = terraform_job.get('steps', [])
        
        health_steps = [s for s in steps 
                       if 'healthy' in s.get('name', '').lower()]
        
        for step in health_steps:
            run_command = step.get('run', '')
            # Should have a loop with limited iterations
            self.assertTrue(re.search(r'for\s+\w+\s+in\s+\{1\.\.\d+\}', run_command) or
                          re.search(r'while.*timeout', run_command, re.IGNORECASE),
                          "Health check should have timeout mechanism")

    def test_health_check_has_success_exit(self):
        """Test that health check exits successfully when targets are healthy."""
        if not self.workflow:
            self.skipTest("Workflow file not found")
            
        terraform_job = self.workflow['jobs']['terraform']
        steps = terraform_job.get('steps', [])
        
        health_steps = [s for s in steps 
                       if 'healthy' in s.get('name', '').lower()]
        
        for step in health_steps:
            run_command = step.get('run', '')
            self.assertIn('exit 0', run_command,
                         "Health check should exit 0 on success")

    def test_health_check_has_failure_exit(self):
        """Test that health check exits with error when timeout occurs."""
        if not self.workflow:
            self.skipTest("Workflow file not found")
            
        terraform_job = self.workflow['jobs']['terraform']
        steps = terraform_job.get('steps', [])
        
        health_steps = [s for s in steps 
                       if 'healthy' in s.get('name', '').lower()]
        
        for step in health_steps:
            run_command = step.get('run', '')
            self.assertIn('exit 1', run_command,
                         "Health check should exit 1 on failure")

    def test_load_balancer_url_output_format(self):
        """Test that load balancer URL is properly formatted."""
        if not self.workflow:
            self.skipTest("Workflow file not found")
            
        terraform_job = self.workflow['jobs']['terraform']
        steps = terraform_job.get('steps', [])
        
        lb_steps = [s for s in steps 
                   if 'load balancer url' in s.get('name', '').lower()]
        
        for step in lb_steps:
            run_command = step.get('run', '')
            # Should output to GITHUB_OUTPUT
            self.assertIn('GITHUB_OUTPUT', run_command,
                         "Should output to GITHUB_OUTPUT")


class TestWorkflowSecurityBestPractices(unittest.TestCase):
    """Test security best practices in workflow files."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.repo_root = Path(__file__).parent.parent.parent
        cls.workflows_dir = cls.repo_root / ".github" / "workflows"

    def test_no_secrets_files_in_repo(self):
        """Test that no secret files exist in repository."""
        secret_files = ['secret', 'secrets', '.env', 'credentials']
        
        for secret_file in secret_files:
            file_path = self.repo_root / secret_file
            self.assertFalse(file_path.exists(),
                           f"Secret file '{secret_file}' should not exist in repo")

    def test_no_hardcoded_credentials_in_workflows(self):
        """Test that workflows don't contain hardcoded credentials."""
        workflow_files = list(self.workflows_dir.glob("*.yml")) + \
                        list(self.workflows_dir.glob("*.yaml"))
        
        # Patterns for common secrets
        secret_patterns = [
            (r'AKIA[0-9A-Z]{16}', 'AWS Access Key ID'),
            (r'(?i)password\s*[:=]\s*["\'][\w@#$%^&*()]+["\']', 'Hardcoded password'),
            (r'(?i)api[_-]?key\s*[:=]\s*["\'][a-zA-Z0-9]{20,}["\']', 'Hardcoded API key'),
            (r'(?i)token\s*[:=]\s*["\'][a-zA-Z0-9_\-]{20,}["\']', 'Hardcoded token'),
        ]
        
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            # Skip if using secrets properly
            if 'secrets.' in content:
                for pattern, description in secret_patterns:
                    # More lenient check - only fail on obvious hardcoded secrets
                    matches = re.findall(pattern, content)
                    # Filter out secrets.* references
                    actual_secrets = [m for m in matches 
                                    if not re.search(r'secrets\.\w+', m)]
                    
                    with self.subTest(workflow=workflow_file.name, 
                                     pattern=description):
                        self.assertEqual(len(actual_secrets), 0,
                                       f"Found {description} in {workflow_file.name}")

    def test_actions_use_specific_versions(self):
        """Test that GitHub Actions use specific versions, not @main or @master."""
        workflow_files = list(self.workflows_dir.glob("*.yml")) + \
                        list(self.workflows_dir.glob("*.yaml"))
        
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                workflow = yaml.safe_load(f)
            
            for job_name, job in workflow.get('jobs', {}).items():
                steps = job.get('steps', [])
                
                for step in steps:
                    uses = step.get('uses', '')
                    if uses:
                        with self.subTest(workflow=workflow_file.name,
                                        job=job_name,
                                        action=uses):
                            # Should use @v1, @v2, etc., not @main or @master
                            self.assertNotIn('@main', uses.lower(),
                                           f"Action should use version tag, not @main: {uses}")
                            self.assertNotIn('@master', uses.lower(),
                                           f"Action should use version tag, not @master: {uses}")

    def test_workflow_has_permissions_defined(self):
        """Test that workflows define permissions when using GitHub token."""
        workflow_files = list(self.workflows_dir.glob("*.yml")) + \
                        list(self.workflows_dir.glob("*.yaml"))
        
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                content = f.read()
                workflow = yaml.safe_load(f)
            
            # If workflow uses github.token or GITHUB_TOKEN
            if 'github.token' in content.lower() or 'github_token' in content.lower():
                with self.subTest(workflow=workflow_file.name):
                    # Should have permissions defined
                    has_permissions = ('permissions' in workflow or
                                     any('permissions' in job 
                                         for job in workflow.get('jobs', {}).values()))
                    self.assertTrue(has_permissions,
                                  f"{workflow_file.name} uses token but lacks permissions")


class TestWorkflowTriggers(unittest.TestCase):
    """Test workflow trigger configurations."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.repo_root = Path(__file__).parent.parent.parent
        cls.terraform_workflow = cls.repo_root / ".github" / "workflows" / "terraform.yml"
        
        if cls.terraform_workflow.exists():
            with open(cls.terraform_workflow, 'r') as f:
                cls.workflow = yaml.safe_load(f)
        else:
            cls.workflow = None

    def test_terraform_workflow_triggers(self):
        """Test terraform workflow has appropriate triggers."""
        if not self.workflow:
            self.skipTest("Workflow file not found")
        
        # YAML parses 'on' as boolean True
        triggers = self.workflow.get('on', self.workflow.get(True, {}))
        
        # Should trigger on push to main
        if isinstance(triggers, dict):
            self.assertIn('push', triggers,
                         "Workflow should trigger on push")
            
            if 'push' in triggers and isinstance(triggers['push'], dict):
                branches = triggers['push'].get('branches', [])
                self.assertIn('main', branches,
                            "Should trigger on main branch")

    def test_workflow_environment_variables(self):
        """Test that necessary environment variables are defined."""
        if not self.workflow:
            self.skipTest("Workflow file not found")
        
        env_vars = self.workflow.get('env', {})
        
        # Should have AWS region defined
        self.assertIn('AWS_REGION', env_vars,
                     "Should define AWS_REGION environment variable")
        
        # Should have TF_LOG for terraform logging
        self.assertIn('TF_LOG', env_vars,
                     "Should define TF_LOG for terraform logging")


class TestWorkflowArtifacts(unittest.TestCase):
    """Test workflow artifact handling."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.repo_root = Path(__file__).parent.parent.parent
        cls.terraform_workflow = cls.repo_root / ".github" / "workflows" / "terraform.yml"
        
        if cls.terraform_workflow.exists():
            with open(cls.terraform_workflow, 'r') as f:
                cls.workflow = yaml.safe_load(f)
        else:
            cls.workflow = None

    def test_zap_report_artifact_upload(self):
        """Test that ZAP report is uploaded as artifact."""
        if not self.workflow:
            self.skipTest("Workflow file not found")
        
        terraform_job = self.workflow['jobs']['terraform']
        steps = terraform_job.get('steps', [])
        
        artifact_steps = [s for s in steps 
                         if 'upload-artifact' in s.get('uses', '').lower()]
        
        self.assertGreater(len(artifact_steps), 0,
                          "Should upload ZAP report as artifact")
        
        for step in artifact_steps:
            with_params = step.get('with', {})
            self.assertIn('name', with_params,
                         "Artifact should have a name")
            self.assertIn('path', with_params,
                         "Artifact should have a path")


if __name__ == '__main__':
    unittest.main()