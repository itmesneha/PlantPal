# Branch Protection Setup Guide

This guide will help you set up branch protection rules in GitHub to ensure all tests pass before merging pull requests.

## Setting up Branch Protection Rules

1. **Navigate to your repository settings:**
   - Go to your GitHub repository
   - Click on "Settings" tab
   - Click on "Branches" in the left sidebar

2. **Add a branch protection rule:**
   - Click "Add rule"
   - Enter `main` as the branch name pattern

3. **Configure the following settings:**

   ### Required Status Checks
   ✅ **Require status checks to pass before merging**
   - ✅ Require branches to be up to date before merging
   - Select the following required status checks:
     - `Backend Tests`
     - `Frontend Tests`
     - `Lint and Format Check`
     - `Build Test`
     - `Test Summary`

   ### Pull Request Requirements
   ✅ **Require a pull request before merging**
   - ✅ Require approvals: 1 (or more based on your team size)
   - ✅ Dismiss stale PR approvals when new commits are pushed
   - ✅ Require review from code owners (if you have a CODEOWNERS file)

   ### Additional Restrictions
   ✅ **Restrict pushes that create files**
   ✅ **Require signed commits** (optional but recommended)
   ✅ **Include administrators** (applies rules to repository admins too)

4. **Click "Create" to save the rule**

## Additional Recommendations

### 1. Create a CODEOWNERS file
Create `.github/CODEOWNERS` to automatically request reviews from specific team members:

```
# Global owners
* @your-username

# Backend specific
backend/ @backend-team-member
backend/app/routers/ @api-team-lead

# Frontend specific
frontend/ @frontend-team-member
frontend/src/components/ @ui-team-lead

# Infrastructure
.github/workflows/ @devops-team-lead
docker-compose.yml @devops-team-lead
```

### 2. Set up auto-merge for dependabot PRs
If you use Dependabot, you can set up auto-merge for dependency updates that pass all tests.

### 3. Configure notifications
Set up Slack or email notifications for failed CI/CD runs in your repository settings.

## Testing the Setup

1. Create a test branch: `git checkout -b test-ci-cd`
2. Make a small change to trigger tests
3. Push the branch: `git push origin test-ci-cd`
4. Create a pull request
5. Verify that all status checks run and must pass before merging

## Troubleshooting

### Common Issues:
- **Tests not running**: Check that the workflow file is in the correct location (`.github/workflows/`)
- **Status checks not required**: Make sure you've selected the correct status check names in branch protection
- **Secrets missing**: Ensure all required secrets are set in repository settings

### Required Secrets:
The test workflow uses minimal secrets, but for full deployment you'll need:
- `AWS_REGION`
- `ECR_REPOSITORY`
- `AWS_ROLE_TO_ASSUME` (for OIDC)
- Other deployment-specific secrets

## Monitoring

- Check the "Actions" tab to monitor workflow runs
- Set up notifications for failed workflows
- Review coverage reports uploaded to Codecov (if configured)