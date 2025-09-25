# PlantPal Backend Setup Guide 🌱

This guide will help you set up the PlantPal backend on your EC2 instance with PostgreSQL database.

## Prerequisites

- EC2 instance running (Ubuntu 20.04+ recommended)
- Python 3.8+ installed
- PostgreSQL installed and running
- AWS CLI configured (for S3 access)

## Step 1: EC2 Instance Setup

### 1.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Install Python and PostgreSQL
```bash
# Install Python 3.9+
sudo apt install python3 python3-pip python3-venv -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 1.3 Install additional dependencies
```bash
# Install system dependencies for Python packages
sudo apt install build-essential libpq-dev python3-dev -y
```

## Step 2: Database Setup

### 2.1 Configure PostgreSQL
```bash
# Switch to postgres user
sudo -u postgres psql

# Inside PostgreSQL shell, run:
# (Replace 'your_secure_password_here' with a strong password)
```

### 2.2 Run the database setup script
```sql
-- Copy the contents of setup_database.sql and run it in PostgreSQL
-- Make sure to replace 'your_secure_password_here' with your actual password
```

### 2.3 Configure PostgreSQL for remote connections (if needed)
```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf

# Find and modify:
listen_addresses = 'localhost'  # For local connections only
# OR
listen_addresses = '*'  # For remote connections (less secure)

# Edit pg_hba.conf for authentication
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Add line for your application:
local   plantpal_db    plantpal_user                     md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

## Step 3: Backend Application Setup

### 3.1 Clone and setup project
```bash
# Clone your repository
git clone https://github.com/itmesneha/PlantPal.git
cd PlantPal/backend

# Create virtual environment
python3 -m venv plantpal_env
source plantpal_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3.2 Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

### 3.3 Update your .env file:
```bash
# Database Configuration
DATABASE_URL=postgresql://plantpal_user:your_secure_password@localhost:5432/plantpal_db

# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=ap-southeast-1
S3_BUCKET_NAME=plantpal-images

# Cognito Configuration (from your frontend)
COGNITO_USER_POOL_ID=ap-southeast-1_km8Z7zM54
COGNITO_CLIENT_ID=1ugluq9v60811tf40482j6t6in
COGNITO_REGION=ap-southeast-1

# API Configuration
SECRET_KEY=your-secret-key-for-jwt-token-signing-make-it-long-and-random
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Settings
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-ec2-public-ip
CORS_ORIGINS=http://localhost:3000,https://your-frontend-s3-bucket.s3-website-ap-southeast-1.amazonaws.com
```

### 3.4 Initialize Database
```bash
# Run database initialization script
python init_db.py
```

## Step 4: Start the Application

### 4.1 Development Mode
```bash
# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4.2 Production Mode with Systemd
```bash
# Create systemd service file
sudo nano /etc/systemd/system/plantpal.service
```

Add the following content:
```ini
[Unit]
Description=PlantPal FastAPI application
After=network.target

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/PlantPal/backend
Environment=PATH=/home/ubuntu/PlantPal/backend/plantpal_env/bin
ExecStart=/home/ubuntu/PlantPal/backend/plantpal_env/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 4.3 Start the service
```bash
# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl start plantpal
sudo systemctl enable plantpal

# Check status
sudo systemctl status plantpal
```

## Step 5: Security & Firewall Setup

### 5.1 Configure UFW firewall
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Allow your API port (if not using reverse proxy)
sudo ufw allow 8000

# Check status
sudo ufw status
```

### 5.2 Setup Nginx (Recommended for production)
```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/plantpal
```

Add Nginx configuration:
```nginx
server {
    listen 80;
    server_name your-ec2-public-ip;  # Replace with your domain or IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5.3 Enable Nginx configuration
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/plantpal /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Step 6: AWS S3 Setup for Image Storage

### 6.1 Create S3 Bucket
```bash
# Create bucket (use your preferred region)
aws s3 mb s3://plantpal-images --region ap-southeast-1

# Configure bucket for public read (for serving images)
aws s3api put-bucket-policy --bucket plantpal-images --policy file://bucket-policy.json
```

### 6.2 Create bucket policy file (bucket-policy.json):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::plantpal-images/*"
        }
    ]
}
```

## Step 7: Testing the Setup

### 7.1 Test API endpoints
```bash
# Test health endpoint
curl http://your-ec2-ip:8000/health

# Test root endpoint
curl http://your-ec2-ip:8000/

# Access API documentation
# Open browser: http://your-ec2-ip:8000/docs
```

### 7.2 Test database connection
```bash
# Connect to PostgreSQL and verify tables
sudo -u postgres psql -d plantpal_db -c "\dt"
```

## Step 8: Monitoring and Logs

### 8.1 View application logs
```bash
# View systemd logs
sudo journalctl -u plantpal -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 8.2 Monitor system resources
```bash
# Check system resources
htop

# Check disk space
df -h

# Check memory usage
free -h
```

## Database Schema Overview

The database includes the following main tables:

- **users**: Store user profiles linked to Cognito IDs
- **plants**: User's plant collection with health tracking
- **scan_sessions**: Plant identification and scanning history
- **health_reports**: Detailed health analysis and care recommendations
- **achievements**: Gamification system with user progress
- **plant_species**: Reference database for plant identification
- **plant_care_logs**: Care activity tracking and scheduling

## API Endpoints

Once running, your API will provide:

- `GET /` - API welcome message
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)
- `POST /api/v1/users` - Create user profile
- `GET /api/v1/users/me` - Get current user
- `GET /api/v1/plants` - Get user's plants
- `POST /api/v1/plants` - Add new plant
- `POST /api/v1/scan` - Plant identification and health scan
- `GET /api/v1/dashboard` - Dashboard data

## Next Steps

1. **Implement JWT authentication** to validate Cognito tokens
2. **Add plant identification AI/ML service** integration
3. **Implement image upload to S3** functionality
4. **Add comprehensive error handling** and logging
5. **Set up SSL/TLS certificates** for HTTPS (Let's Encrypt)
6. **Implement rate limiting** and API security measures
7. **Add monitoring and alerting** (CloudWatch, Datadog, etc.)
8. **Set up automated backups** for PostgreSQL database

## Troubleshooting

### Common Issues:

1. **Database connection errors**: Check PostgreSQL is running and credentials are correct
2. **Permission denied errors**: Ensure proper file permissions and user ownership
3. **Port already in use**: Check if another service is using port 8000
4. **Module import errors**: Ensure virtual environment is activated and dependencies installed

### Useful Commands:
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check if port 8000 is in use
sudo netstat -tlnp | grep :8000

# Check application logs
sudo journalctl -u plantpal --since "1 hour ago"

# Restart the application
sudo systemctl restart plantpal
```

Your PlantPal backend is now ready for development! 🚀🌱