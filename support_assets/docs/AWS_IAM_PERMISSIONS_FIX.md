# 🔐 AWS IAM Permissions Fix

## The Problem

Your IAM user (`weathercast-s3-user`) doesn't have DynamoDB permissions.
Error shows:
```
User: arn:aws:iam::340752797090/weathercast-s3-user
is not authorized to perform: dynamodb:Scan
on resource: arn:aws:dynamodb:us-west-2:340752797090:table/news_metadata
```

But your Lambda role (`newsinsights-lambda-role`) DOES have permissions.

---

## Solution 1: Add DynamoDB Permissions to Your IAM User (Recommended for Development)

### Step 1: Go to AWS IAM Console
1. Go to https://console.aws.amazon.com/iam
2. Click **Users** in the left sidebar
3. Click **weathercast-s3-user**

### Step 2: Add DynamoDB Policy
1. Click **Add permissions** → **Attach policies directly**
2. Search for: `AmazonDynamoDBFullAccess` (or create custom policy)
3. Select it and click **Attach policies**

### Step 3: Verify It Works
```bash
python TEST_API_QUICK_START.py
# Should now work! ✅
```

---

## Solution 2: Use Lambda Role via boto3 (Advanced)

If you want to use the Lambda role directly:

### Via boto3 STS Assume Role

```python
import boto3
from botocore.exceptions import ClientError

def get_ddb_with_lambda_role():
    """Use STS to assume the Lambda role instead of current IAM user"""
    sts = boto3.client('sts', region_name='us-west-2')
    
    try:
        # Assume the Lambda role
        response = sts.assume_role(
            RoleArn='arn:aws:iam::340752797090:role/newsinsights-lambda-role',
            RoleSessionName='newsinsight-session'
        )
        
        # Create new credentials
        credentials = response['Credentials']
        
        # Create session with assumed role credentials
        session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            region_name='us-west-2'
        )
        
        return session.resource('dynamodb')
    
    except ClientError as e:
        print(f"Error assuming role: {e}")
        return None

# Usage in app.py
ddb = get_ddb_with_lambda_role()
if ddb:
    table = ddb.Table('news_metadata')
```

---

## Recommended: Solution 1 (Simpler)

**Just add DynamoDB permissions to your IAM user:**

1. ✅ Simpler to set up
2. ✅ Development-friendly
3. ✅ No extra code changes needed
4. ✅ Works immediately

---

## Permissions Needed (if creating custom policy)

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:Scan",
                "dynamodb:Query",
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:BatchGetItem",
                "dynamodb:BatchWriteItem"
            ],
            "Resource": "arn:aws:dynamodb:us-west-2:340752797090:table/news_metadata"
        }
    ]
}
```

---

## Quick Fix (2 minutes)

1. Go to AWS IAM Console
2. Find: `weathercast-s3-user`
3. Click: **Add permissions**
4. Search: `AmazonDynamoDBFullAccess`
5. Click: **Attach policies**
6. Run: `streamlit run app.py`

Done! ✅

---

## Verify It's Fixed

```bash
python TEST_API_QUICK_START.py
```

Should show:
```
✅ [Got X articles from APIs]
✅ Format successful
```

If still getting permission error:
1. Wait 2-3 minutes for AWS to propagate changes
2. Restart PowerShell terminal
3. Try again

---

## Production Setup

For production:
- Use Lambda role (Solution 2)
- Or create dedicated DynamoDB role for app
- Never use user credentials for apps
- Use environment variables for role ARN

---

## Still Having Issues?

Check your credentials:
```bash
aws sts get-caller-identity
```

Should show:
- Account: 340752797090
- Arn: Should contain `weathercast-s3-user` (or whatever your user is)
- UserId: Starting with `AIDAI...`

If it shows different account/user, your AWS credentials might be incorrect.
