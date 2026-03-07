"""
CloudWatch Monitoring Configuration for TravelGo
=================================================
This module configures AWS CloudWatch monitoring, logging, and metrics
for the TravelGo application deployed on AWS EC2.
"""

import os
import logging
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# CloudWatch Configuration
CLOUDWATCH_REGION = os.environ.get("AWS_REGION", "ap-south-1")
LOG_GROUP_NAME = os.environ.get("CLOUDWATCH_LOG_GROUP", "/aws/ec2/travelgo")
ENABLE_MONITORING = os.environ.get("ENABLE_MONITORING", "true").lower() == "true"

# Initialize CloudWatch client
cw_client = None


def get_cloudwatch_client():
    """Get or create CloudWatch client"""
    global cw_client
    if cw_client is None:
        cw_client = boto3.client('cloudwatch', region_name=CLOUDWATCH_REGION)
    return cw_client


def create_log_group():
    """Create CloudWatch log group if it doesn't exist"""
    if not ENABLE_MONITORING:
        return
    
    try:
        cw = get_cloudwatch_client()
        cw.create_log_group(
            logGroupName=LOG_GROUP_NAME,
            tags={
                'Application': 'TravelGo',
                'Environment': os.environ.get('FLASK_ENV', 'production')
            }
        )
        logging.info(f"Created CloudWatch log group: {LOG_GROUP_NAME}")
    except Exception as e:
        # Check if it's a "already exists" error
        error_str = str(e)
        if "ResourceAlreadyExists" in error_str or "already exists" in error_str.lower():
            logging.info(f"Log group {LOG_GROUP_NAME} already exists")
        else:
            logging.warning(f"Could not create log group: {e}")


def setup_log_stream(log_stream_name: str):
    """Create a CloudWatch log stream"""
    if not ENABLE_MONITORING:
        return
    
    try:
        cw = get_cloudwatch_client()
        cw.create_log_stream(
            logGroupName=LOG_GROUP_NAME,
            logStreamName=log_stream_name
        )
    except Exception as e:
        logging.warning(f"Could not create log stream: {e}")


def put_log_events(log_stream_name: str, messages: List[Dict]):
    """Put log events to CloudWatch"""
    if not ENABLE_MONITORING:
        return
    
    try:
        cw = get_cloudwatch_client()
        import datetime
        import time
        
        log_events = []
        timestamp = int(time.time() * 1000)
        
        for i, msg in enumerate(messages):
            log_events.append({
                'timestamp': timestamp + (i * 1000),
                'message': str(msg)
            })
        
        if log_events:
            cw.put_log_events(
                logGroupName=LOG_GROUP_NAME,
                logStreamName=log_stream_name,
                logEvents=log_events
            )
    except Exception as e:
        logging.warning(f"Could not put log events: {e}")


# ==================== CUSTOM METRICS ====================

def put_metric_data(
    namespace: str,
    metric_name: str,
    value: float,
    unit: str = "Count",
    dimensions: Optional[List[Dict]] = None
):
    """Put custom metric data to CloudWatch"""
    if not ENABLE_MONITORING:
        return
    
    try:
        cw = get_cloudwatch_client()
        cw.put_metric_data(
            Namespace=namespace,
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit,
                    'Timestamp': datetime.utcnow(),
                    'Dimensions': dimensions or []
                }
            ]
        )
    except Exception as e:
        logging.warning(f"Could not put metric data: {e}")


# Application-specific metrics
class AppMetrics:
    """TravelGo application metrics"""
    
    NAMESPACE = "TravelGo/Application"
    
    @staticmethod
    def record_page_view(page_name: str):
        """Record a page view"""
        put_metric_data(
            namespace=AppMetrics.NAMESPACE,
            metric_name="PageViews",
            value=1,
            unit="Count",
            dimensions=[{'Name': 'Page', 'Value': page_name}]
        )
    
    @staticmethod
    def record_api_call(endpoint: str, status_code: int):
        """Record an API call"""
        put_metric_data(
            namespace=AppMetrics.NAMESPACE,
            metric_name="APICalls",
            value=1,
            unit="Count",
            dimensions=[
                {'Name': 'Endpoint', 'Value': endpoint},
                {'Name': 'StatusCode', 'Value': str(status_code)}
            ]
        )
    
    @staticmethod
    def record_booking(type: str, success: bool):
        """Record a booking attempt"""
        put_metric_data(
            namespace=AppMetrics.NAMESPACE,
            metric_name="Bookings",
            value=1 if success else 0,
            unit="Count",
            dimensions=[{'Name': 'BookingType', 'Value': type}]
        )
    
    @staticmethod
    def record_response_time(endpoint: str, duration_ms: float):
        """Record response time"""
        put_metric_data(
            namespace=AppMetrics.NAMESPACE,
            metric_name="ResponseTime",
            value=duration_ms,
            unit="Milliseconds",
            dimensions=[{'Name': 'Endpoint', 'Value': endpoint}]
        )
    
    @staticmethod
    def record_error(error_type: str):
        """Record an error occurrence"""
        put_metric_data(
            namespace=AppMetrics.NAMESPACE,
            metric_name="Errors",
            value=1,
            unit="Count",
            dimensions=[{'Name': 'ErrorType', 'Value': error_type}]
        )


# ==================== DYNAMODB METRICS ====================

class DynamoDBMetrics:
    """DynamoDB operation metrics"""
    
    NAMESPACE = "TravelGo/DynamoDB"
    
    @staticmethod
    def record_read(capacity_units: float, table_name: str):
        """Record DynamoDB read capacity"""
        put_metric_data(
            namespace=DynamoDBMetrics.NAMESPACE,
            metric_name="ConsumedReadCapacityUnits",
            value=capacity_units,
            unit="Count",
            dimensions=[{'Name': 'TableName', 'Value': table_name}]
        )
    
    @staticmethod
    def record_write(capacity_units: float, table_name: str):
        """Record DynamoDB write capacity"""
        put_metric_data(
            namespace=DynamoDBMetrics.NAMESPACE,
            metric_name="ConsumedWriteCapacityUnits",
            value=capacity_units,
            unit="Count",
            dimensions=[{'Name': 'TableName', 'Value': table_name}]
        )


# ==================== SNS METRICS ====================

class SNSMetrics:
    """SNS notification metrics"""
    
    NAMESPACE = "TravelGo/SNS"
    
    @staticmethod
    def record_notification(notification_type: str, success: bool):
        """Record SNS notification"""
        put_metric_data(
            namespace=SNSMetrics.NAMESPACE,
            metric_name="Notifications",
            value=1,
            unit="Count",
            dimensions=[
                {'Name': 'Type', 'Value': notification_type},
                {'Name': 'Status', 'Value': 'Success' if success else 'Failed'}
            ]
        )


# ==================== DASHBOARD CREATION ====================

def create_dashboard():
    """Create CloudWatch dashboard for TravelGo"""
    if not ENABLE_MONITORING:
        return
    
    try:
        cw = get_cloudwatch_client()
        
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "title": "Page Views",
                        "period": 300,
                        "stat": "Sum",
                        "region": CLOUDWATCH_REGION,
                        "metrics": [
                            ["TravelGo/Application", "PageViews", {"stat": "Sum"}],
                            [".", "APICalls", {"stat": "Sum"}]
                        ]
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "title": "Response Time",
                        "period": 300,
                        "stat": "Average",
                        "region": CLOUDWATCH_REGION,
                        "metrics": [
                            ["TravelGo/Application", "ResponseTime", {"stat": "Average"}]
                        ]
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "title": "Bookings",
                        "period": 3600,
                        "stat": "Sum",
                        "region": CLOUDWATCH_REGION,
                        "metrics": [
                            ["TravelGo/Application", "Bookings", {"stat": "Sum"}]
                        ]
                    }
                },
                {
                    "type": "metric",
                    "properties": {
                        "title": "Errors",
                        "period": 300,
                        "stat": "Sum",
                        "region": CLOUDWATCH_REGION,
                        "metrics": [
                            ["TravelGo/Application", "Errors", {"stat": "Sum"}]
                        ]
                    }
                }
            ]
        }
        
        cw.put_dashboard(
            DashboardName='TravelGo-Dashboard',
            DashboardBody=str(dashboard_body)
        )
        logging.info("Created CloudWatch dashboard")
    except Exception as e:
        logging.warning(f"Could not create dashboard: {e}")


# ==================== ALARM CREATION ====================

def create_alarms():
    """Create CloudWatch alarms for TravelGo"""
    if not ENABLE_MONITORING:
        return
    
    try:
        cw = get_cloudwatch_client()
        
        # Error rate alarm
        cw.put_metric_alarm(
            AlarmName='TravelGo-HighErrorRate',
            AlarmDescription='Alert when error rate exceeds threshold',
            MetricName='Errors',
            Namespace='TravelGo/Application',
            Statistic='Sum',
            Period=300,
            EvaluationPeriods=2,
            Threshold=10,
            ComparisonOperator='GreaterThanThreshold',
            AlarmActions=[],
            Dimensions=[]
        )
        
        # Response time alarm
        cw.put_metric_alarm(
            AlarmName='TravelGo-HighResponseTime',
            AlarmDescription='Alert when response time exceeds threshold',
            MetricName='ResponseTime',
            Namespace='TravelGo/Application',
            Statistic='Average',
            Period=300,
            EvaluationPeriods=2,
            Threshold=1000,
            ComparisonOperator='GreaterThanThreshold',
            AlarmActions=[],
            Dimensions=[]
        )
        
        logging.info("Created CloudWatch alarms")
    except Exception as e:
        logging.warning(f"Could not create alarms: {e}")


# ==================== INITIALIZATION ====================

def init_monitoring():
    """Initialize CloudWatch monitoring"""
    if not ENABLE_MONITORING:
        logging.info("Monitoring is disabled")
        return
    
    create_log_group()
    setup_log_stream("Application")
    create_dashboard()
    create_alarms()
    logging.info("CloudWatch monitoring initialized")


if __name__ == '__main__':
    init_monitoring()

