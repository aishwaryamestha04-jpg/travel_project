import boto3

# Create SNS client
sns = boto3.client(
    'sns',
    region_name='ap-south-1'
)

def send_booking_notification(phone_number, message):
    try:
        response = sns.publish(
            PhoneNumber=phone_number,
            Message=message
        )

        print("Notification sent successfully")
        return response

    except Exception as e:
        print("SNS Error:", str(e))
        return None