#!/bin/bash
# PlantPal ECS Deployment Diagnostic Script

echo "🔍 PlantPal Deployment Diagnostics"
echo "===================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CLUSTER_NAME="fastapi-cluster"
SERVICE_NAME="fastapi-service"
TASK_FAMILY="plantpal-task"
EC2_IP="54.251.32.63"

echo "📋 Configuration:"
echo "  Cluster: $CLUSTER_NAME"
echo "  Service: $SERVICE_NAME"
echo "  EC2 IP: $EC2_IP"
echo ""

# 1. Check ECS Service Status
echo "1️⃣ Checking ECS Service Status..."
SERVICE_STATUS=$(aws ecs describe-services \
  --cluster $CLUSTER_NAME \
  --services $SERVICE_NAME \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,Pending:pendingCount}' \
  --output table 2>/dev/null)

if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓${NC} Service found"
  echo "$SERVICE_STATUS"
else
  echo -e "${RED}✗${NC} Failed to get service status"
fi
echo ""

# 2. Check Running Tasks
echo "2️⃣ Checking Running Tasks..."
TASK_ARNS=$(aws ecs list-tasks \
  --cluster $CLUSTER_NAME \
  --service-name $SERVICE_NAME \
  --query 'taskArns[0]' \
  --output text 2>/dev/null)

if [ ! -z "$TASK_ARNS" ] && [ "$TASK_ARNS" != "None" ]; then
  echo -e "${GREEN}✓${NC} Task running: $TASK_ARNS"
  
  # Get task details
  echo ""
  echo "   Task Details:"
  aws ecs describe-tasks \
    --cluster $CLUSTER_NAME \
    --tasks $TASK_ARNS \
    --query 'tasks[0].{Status:lastStatus,Health:healthStatus,Container:containers[0].{Name:name,Status:lastStatus}}' \
    --output table
else
  echo -e "${RED}✗${NC} No running tasks found"
fi
echo ""

# 3. Check Container Instance
echo "3️⃣ Checking Container Instance..."
INSTANCE_ARNS=$(aws ecs list-container-instances \
  --cluster $CLUSTER_NAME \
  --query 'containerInstanceArns[0]' \
  --output text 2>/dev/null)

if [ ! -z "$INSTANCE_ARNS" ] && [ "$INSTANCE_ARNS" != "None" ]; then
  echo -e "${GREEN}✓${NC} Container instance found"
  aws ecs describe-container-instances \
    --cluster $CLUSTER_NAME \
    --container-instances $INSTANCE_ARNS \
    --query 'containerInstances[0].{Status:status,AgentConnected:agentConnected,RunningTasks:runningTasksCount}' \
    --output table
else
  echo -e "${RED}✗${NC} No container instances found"
fi
echo ""

# 4. Check Task Definition
echo "4️⃣ Checking Task Definition..."
TASK_DEF=$(aws ecs describe-task-definition \
  --task-definition $TASK_FAMILY \
  --query 'taskDefinition.{Family:family,Revision:revision,Status:status}' \
  --output table 2>/dev/null)

if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓${NC} Task definition exists"
  echo "$TASK_DEF"
  
  # Check port mappings
  echo ""
  echo "   Port Mappings:"
  aws ecs describe-task-definition \
    --task-definition $TASK_FAMILY \
    --query 'taskDefinition.containerDefinitions[0].portMappings' \
    --output table
else
  echo -e "${RED}✗${NC} Task definition not found"
fi
echo ""

# 5. Check Environment Variables
echo "5️⃣ Checking Environment Variables..."
ENV_VARS=$(aws ecs describe-task-definition \
  --task-definition $TASK_FAMILY \
  --query 'taskDefinition.containerDefinitions[0].environment[*].name' \
  --output text 2>/dev/null)

if [ ! -z "$ENV_VARS" ]; then
  echo -e "${GREEN}✓${NC} Environment variables configured:"
  echo "   $ENV_VARS"
else
  echo -e "${YELLOW}⚠${NC} No environment variables found"
fi
echo ""

# 6. Test API Connectivity
echo "6️⃣ Testing API Connectivity..."

# Test root endpoint
echo "   Testing http://$EC2_IP:8000/ ..."
ROOT_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://$EC2_IP:8000/ 2>/dev/null)

if [ "$ROOT_RESPONSE" = "200" ]; then
  echo -e "   ${GREEN}✓${NC} Root endpoint accessible (HTTP $ROOT_RESPONSE)"
  curl -s http://$EC2_IP:8000/ | jq '.' 2>/dev/null || curl -s http://$EC2_IP:8000/
elif [ "$ROOT_RESPONSE" = "000" ]; then
  echo -e "   ${RED}✗${NC} Connection failed - Check security group!"
else
  echo -e "   ${YELLOW}⚠${NC} Unexpected response (HTTP $ROOT_RESPONSE)"
fi

# Test health endpoint
echo ""
echo "   Testing http://$EC2_IP:8000/health ..."
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://$EC2_IP:8000/health 2>/dev/null)

if [ "$HEALTH_RESPONSE" = "200" ]; then
  echo -e "   ${GREEN}✓${NC} Health endpoint accessible (HTTP $HEALTH_RESPONSE)"
elif [ "$HEALTH_RESPONSE" = "000" ]; then
  echo -e "   ${RED}✗${NC} Connection failed - Check security group!"
else
  echo -e "   ${YELLOW}⚠${NC} Unexpected response (HTTP $HEALTH_RESPONSE)"
fi

# Test docs
echo ""
echo "   Testing http://$EC2_IP:8000/docs ..."
DOCS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://$EC2_IP:8000/docs 2>/dev/null)

if [ "$DOCS_RESPONSE" = "200" ]; then
  echo -e "   ${GREEN}✓${NC} API docs accessible (HTTP $DOCS_RESPONSE)"
elif [ "$DOCS_RESPONSE" = "000" ]; then
  echo -e "   ${RED}✗${NC} Connection failed"
else
  echo -e "   ${YELLOW}⚠${NC} Unexpected response (HTTP $DOCS_RESPONSE)"
fi
echo ""

# 7. Recent CloudWatch Logs
echo "7️⃣ Fetching Recent Logs..."
LOG_GROUP="/ecs/$TASK_FAMILY"

echo "   Checking log group: $LOG_GROUP"
aws logs tail $LOG_GROUP --since 10m --format short 2>/dev/null | head -20

if [ $? -ne 0 ]; then
  echo -e "   ${YELLOW}⚠${NC} Could not fetch logs. Log group may not exist."
fi
echo ""

# Summary
echo "======================================"
echo "📊 Summary"
echo "======================================"

if [ "$ROOT_RESPONSE" = "200" ]; then
  echo -e "${GREEN}✓ API is accessible and working!${NC}"
  echo ""
  echo "🌐 Access Points:"
  echo "   • API Root: http://$EC2_IP:8000/"
  echo "   • API Docs: http://$EC2_IP:8000/docs"
  echo "   • Health: http://$EC2_IP:8000/health"
else
  echo -e "${RED}✗ API is NOT accessible${NC}"
  echo ""
  echo "🔧 Common Fixes:"
  echo "   1. Check security group - Port 8000 must be open"
  echo "   2. Verify ECS task is running"
  echo "   3. Check container logs for errors"
  echo "   4. Ensure DATABASE_URL is set correctly"
  echo ""
  echo "📖 See TROUBLESHOOTING.md for detailed steps"
fi
echo ""

# Provide next steps
if [ "$ROOT_RESPONSE" != "200" ]; then
  echo "🚀 Quick Fix Commands:"
  echo ""
  echo "# Add security group rule for port 8000:"
  echo "aws ec2 describe-security-groups --filters \"Name=group-name,Values=*ECS*\" --query 'SecurityGroups[0].GroupId'"
  echo "# Then:"
  echo "aws ec2 authorize-security-group-ingress --group-id <GROUP_ID> --protocol tcp --port 8000 --cidr 0.0.0.0/0"
  echo ""
  echo "# Restart ECS service:"
  echo "aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --force-new-deployment"
  echo ""
fi
