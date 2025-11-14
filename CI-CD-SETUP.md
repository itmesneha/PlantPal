# CI/CD Setup Guide for PlantPal

This guide explains how to set up Continuous Integration and Continuous Deployment (CI/CD) for the PlantPal project using GitHub Actions.

## 🚀 Quick Start

1. **Push the workflow files** to your GitHub repository
2. **Set up branch protection rules** (see instructions below)
3. **Install pre-commit hooks** for local development (optional but recommended)
4. **Create your first pull request** to test the setup

## 📋 What's Included

### GitHub Actions Workflows

#### 1. **Test Workflow** (`.github/workflows/test.yml`)
Runs on every pull request and push to main branch:

- **Backend Tests**: Runs pytest with coverage reporting
- **Frontend Tests**: Runs Jest tests with coverage
- **Linting & Formatting**: Checks code style with Black, isort, flake8, and Prettier
- **Security Scanning**: Uses Trivy to scan for vulnerabilities
- **Build Testing**: Ensures Docker builds work and frontend compiles
- **Test Summary**: Provides overall pass/fail status

#### 2. **Existing Deployment Workflows**
- `ecr-deploy.yml`: Deploys backend to AWS ECR
- `frontend-deploy.yml`: Deploys frontend to AWS S3

### Code Quality Tools

#### Backend (Python)
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting and style checking
- **pytest**: Testing with coverage

#### Frontend (React/TypeScript)
- **Prettier**: Code formatting
- **ESLint**: Linting (if configured in package.json)
- **Jest**: Testing framework

## 🔧 Setup Instructions

### 1. Branch Protection Rules

Navigate to your GitHub repository settings and set up branch protection:

1. Go to **Settings** → **Branches**
2. Click **Add rule**
3. Branch name pattern: `main`
4. Enable these options:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Include administrators

5. **Required status checks** (select these):
   - `Backend Tests`
   - `Frontend Tests`
   - `Lint and Format Check`
   - `Build Test`
   - `Test Summary`

### 2. Repository Secrets

Ensure these secrets are configured in **Settings** → **Secrets and variables** → **Actions**:

#### For Testing (minimal requirements):
- No additional secrets needed for basic testing

#### For Deployment (existing):
- `AWS_REGION`
- `ECR_REPOSITORY`
- `AWS_ROLE_TO_ASSUME`
- `REACT_APP_USER_POOL_ID`
- `REACT_APP_USER_POOL_CLIENT_ID`
- `REACT_APP_API_URL`

### 3. Local Development Setup (Optional)

Install pre-commit hooks for local code quality checks:

```bash
# Install pre-commit
pip install pre-commit

# Install the git hook scripts
pre-commit install

# (Optional) Run against all files
pre-commit run --all-files
```

### 4. Code Quality Tools Setup

#### Backend Setup
```bash
cd backend

# Install development dependencies
pip install black isort flake8 pytest pytest-cov

# Format code
black .
isort .

# Run linting
flake8 .

# Run tests
pytest --cov=app
```

#### Frontend Setup
```bash
cd frontend

# Install prettier (if not already in package.json)
npm install --save-dev prettier

# Format code
npx prettier --write "src/**/*.{js,jsx,ts,tsx,json,css,md}"

# Run tests
npm test
```

## 🔄 Workflow Triggers

### Test Workflow Runs On:
- **Pull Requests**: To `main` or `develop` branches
- **Pushes**: To `main` branch
- **Manual**: Can be triggered manually from Actions tab

### Deployment Workflows Run On:
- **Pushes**: To `main` branch (only when relevant files change)

## 📊 Monitoring and Reports

### Test Coverage
- Backend coverage reports are generated with pytest-cov
- Frontend coverage reports are generated with Jest
- Coverage reports can be uploaded to Codecov (configured in workflow)

### Security Scanning
- Trivy scans for vulnerabilities in dependencies and code
- Results are uploaded to GitHub Security tab

### Status Checks
- All status checks must pass before merging
- Failed checks will block pull request merging
- Detailed logs available in Actions tab

## 🐛 Troubleshooting

### Common Issues

#### Tests Not Running
- Check workflow file syntax with GitHub Actions validator
- Ensure workflow file is in `.github/workflows/` directory
- Verify branch names match your repository structure

#### Status Checks Not Required
- Double-check branch protection rule configuration
- Ensure status check names match exactly (case-sensitive)
- Wait for at least one workflow run to populate available checks

#### Test Failures
- Check Actions tab for detailed error logs
- Ensure all dependencies are properly specified
- Verify environment variables and secrets are configured

#### Database Connection Issues (Backend Tests)
- The workflow includes a PostgreSQL service for testing
- Ensure your test configuration uses the correct database URL
- Check that migrations run successfully in the workflow

### Getting Help

1. **Check Actions Tab**: View detailed logs of workflow runs
2. **Review Pull Request**: Status checks show detailed information
3. **Local Testing**: Run the same commands locally to debug issues

## 📈 Best Practices

### For Developers
1. **Run tests locally** before pushing
2. **Use pre-commit hooks** to catch issues early
3. **Write tests** for new features
4. **Keep PRs small** and focused
5. **Update tests** when changing functionality

### For Maintainers
1. **Review test coverage** regularly
2. **Monitor security scan results**
3. **Keep dependencies updated**
4. **Enforce code review requirements**
5. **Document any workflow changes**

## 🔄 Workflow Customization

### Adding New Test Categories
To add new test types, modify `.github/workflows/test.yml`:

```yaml
new-test-job:
  name: New Test Category
  runs-on: ubuntu-latest
  steps:
    - name: Checkout code
      uses: actions/checkout@v4
    # Add your test steps here
```

### Modifying Coverage Thresholds
Update pytest configuration in `backend/pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = [
    "--cov-fail-under=80",  # Fail if coverage below 80%
]
```

### Environment-Specific Testing
Add environment-specific jobs for staging/production testing:

```yaml
staging-tests:
  name: Staging Environment Tests
  runs-on: ubuntu-latest
  if: github.ref == 'refs/heads/develop'
  # Add staging-specific test steps
```

This setup provides a robust CI/CD pipeline that ensures code quality, runs comprehensive tests, and maintains security standards while allowing for easy customization and monitoring.