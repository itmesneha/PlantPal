# 🔧 EC2/ECS Deployment Troubleshooting Guide

## Issue: Cannot access API at http://54.251.32.63:8000

### ✅ Quick Diagnostic Steps

Run these commands to diagnose the issue:

```bash
# 1. Check if ECS task is running
aws ecs list-tasks --cluster fastapi-cluster

# 2. Get task details
aws ecs describe-tasks --cluster fastapi-cluster --tasks <TASK_ARN>

# 3. Check container logs
aws ecs describe-tasks --cluster fastapi-cluster --tasks <TASK_ARN> --query 'tasks[0].containers[0].lastStatus'

# 4. Get CloudWatch logs
aws logs tail /ecs/fastapi-task --follow
```

---

## 🔥 Most Common Issues & Fixes

### 1. **Security Group Not Configured** ⚠️ MOST LIKELY

**Problem**: EC2 instance security group doesn't allow inbound traffic on port 8000.

**Solution**:
1. Go to AWS Console → EC2 → Security Groups
2. Find your ECS container instance security group
3. Edit Inbound Rules
4. Add rule:
   - **Type**: Custom TCP
   - **Port**: 8000
   - **Source**: 0.0.0.0/0 (or your specific IP)
   - **Description**: FastAPI application port

**CLI Command**:
```bash
aws ec2 authorize-security-group-ingress \
  --group-id <YOUR_SECURITY_GROUP_ID> \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0
```

---

### 2. **Container Not Running**

**Check Task Status**:
```bash
aws ecs describe-services \
  --cluster fastapi-cluster \
  --services fastapi-service \
  --query 'services[0].{running:runningCount,desired:desiredCount}'
```

**Expected Output**: `{"running": 1, "desired": 1}`

**If running count is 0**:
```bash
# Force new deployment
aws ecs update-service \
  --cluster fastapi-cluster \
  --service fastapi-service \
  --force-new-deployment
```

---

### 3. **Port Mapping Issue in Task Definition**

**Check Task Definition**:
```bash
aws ecs describe-task-definition \
  --task-definition plantpal-task \
  --query 'taskDefinition.containerDefinitions[0].portMappings'
```

**Expected Output**:
```json
[
  {
    "containerPort": 8000,
    "hostPort": 8000,
    "protocol": "tcp"
  }
]
```

**If missing, update task definition** to include port mapping.

---

### 4. **Container Health Check Failing**

**View Container Logs**:
```bash
# Get task ARN first
TASK_ARN=$(aws ecs list-tasks --cluster fastapi-cluster --query 'taskArns[0]' --output text)

# Get log stream name
aws ecs describe-tasks \
  --cluster fastapi-cluster \
  --tasks $TASK_ARN \
  --query 'tasks[0].containers[0].name'

# View logs
aws logs tail /ecs/plantpal-task --follow
```

**Common Log Errors**:
- Database connection failed → Check DATABASE_URL
- Missing environment variables → Check task definition
- Migration errors → Check database accessibility

---

### 5. **Wrong API Endpoint URL**

**Correct URLs**:
- ✅ API Root: `http://54.251.32.63:8000/`
- ✅ Docs: `http://54.251.32.63:8000/docs`
- ✅ OpenAPI: `http://54.251.32.63:8000/openapi.json`
- ❌ Wrong: `http://54.251.32.63:8000/api/v1/docs`

**Test Connection**:
```bash
# Test if server is reachable
curl http://54.251.32.63:8000/

# Test health endpoint
curl http://54.251.32.63:8000/health

# View docs in browser
open http://54.251.32.63:8000/docs
```

---

### 6. **Database Connection Issues**

**Check DATABASE_URL in Task Definition**:
```bash
aws ecs describe-task-definition \
  --task-definition plantpal-task \
  --query 'taskDefinition.containerDefinitions[0].environment'
```

**Should include**:
```json
{
  "name": "DATABASE_URL",
  "value": "postgresql://user:pass@rds-endpoint:5432/plantpal"
}
```

**Test Database Connectivity**:
```bash
# SSH into EC2 instance
ssh -i your-key.pem ec2-user@54.251.32.63

# Test database connection
docker exec -it <container_id> python -c "from app.database import engine; print(engine.connect())"
```

---

### 7. **ECS Task Placement Issues**

**Check Container Instance**:
```bash
aws ecs list-container-instances --cluster fastapi-cluster

aws ecs describe-container-instances \
  --cluster fastapi-cluster \
  --container-instances <INSTANCE_ARN>
```

**Look for**:
- Status: ACTIVE
- Agent connected: true
- Registered resources available

---

## 🚀 Quick Fix Commands

### Restart Everything
```bash
# 1. Stop service
aws ecs update-service \
  --cluster fastapi-cluster \
  --service fastapi-service \
  --desired-count 0

# 2. Wait 30 seconds
sleep 30

# 3. Start service
aws ecs update-service \
  --cluster fastapi-cluster \
  --service fastapi-service \
  --desired-count 1 \
  --force-new-deployment

# 4. Monitor deployment
aws ecs describe-services \
  --cluster fastapi-cluster \
  --services fastapi-service \
  --query 'services[0].deployments'
```

### Check Logs in Real-Time
```bash
# Get latest task
TASK_ARN=$(aws ecs list-tasks \
  --cluster fastapi-cluster \
  --service-name fastapi-service \
  --query 'taskArns[0]' \
  --output text)

# Stream logs
aws logs tail /ecs/plantpal-task --follow
```

---

## 🔍 Manual Verification Steps

### 1. SSH into EC2 Instance
```bash
ssh -i fastapi-key.pem ec2-user@54.251.32.63
```

### 2. Check Docker Containers
```bash
# List running containers
docker ps

# Check container logs
docker logs <container_id>

# Test internal connectivity
docker exec -it <container_id> curl http://localhost:8000/health
```

### 3. Check Port Binding
```bash
# Check if port 8000 is listening
sudo netstat -tulpn | grep 8000

# Or
sudo lsof -i :8000
```

### 4. Test from Inside EC2
```bash
# Test localhost
curl http://localhost:8000/

# Test external IP
curl http://54.251.32.63:8000/
```

---

## 📋 Environment Variables Checklist

Ensure these are set in your ECS Task Definition:

- [ ] `DATABASE_URL`
- [ ] `HF_TOKEN`
- [ ] `PLANTNET_API_KEY`
- [ ] `OPENROUTER_API_KEY`
- [ ] `CORS_ORIGINS`

---

## 🔐 Security Group Configuration

**Required Inbound Rules**:

| Type       | Protocol | Port Range | Source      | Description        |
|------------|----------|------------|-------------|--------------------|
| HTTP       | TCP      | 80         | 0.0.0.0/0   | Optional           |
| Custom TCP | TCP      | 8000       | 0.0.0.0/0   | FastAPI app        |
| SSH        | TCP      | 22         | Your IP     | For debugging      |

**Required Outbound Rules**:
| Type       | Protocol | Port Range | Destination | Description        |
|------------|----------|------------|-------------|--------------------|
| All        | All      | All        | 0.0.0.0/0   | Allow all outbound |

---

## 🆘 If Nothing Works

1. **Check CloudWatch Logs**:
   ```bash
   aws logs describe-log-groups --log-group-name-prefix /ecs/
   aws logs tail /ecs/plantpal-task --follow
   ```

2. **Recreate Service**:
   ```bash
   # Delete service
   aws ecs delete-service --cluster fastapi-cluster --service fastapi-service --force
   
   # Wait for deletion
   aws ecs wait services-inactive --cluster fastapi-cluster --services fastapi-service
   
   # Recreate service (run your deployment again)
   ```

3. **Check Task Definition**:
   - Port mappings correct
   - Environment variables set
   - Container image exists in ECR
   - Memory/CPU limits appropriate

---

## 📞 Contact Points

After running diagnostics, check:

1. **CloudWatch Logs**: `/ecs/plantpal-task`
2. **ECS Console**: Check task status and events
3. **EC2 Console**: Verify security groups
4. **RDS Console**: Verify database accessibility

---

## ✅ Success Indicators

When working correctly, you should see:

```bash
$ curl http://54.251.32.63:8000/
{
  "message": "Welcome to PlantPal API! 🌱",
  "version": "1.0.0",
  "docs": "/docs",
  "status": "updated"
}

$ curl http://54.251.32.63:8000/health
{
  "status": "healthy",
  "message": "PlantPal API is running"
}
```

And browser should show FastAPI docs at: `http://54.251.32.63:8000/docs`
