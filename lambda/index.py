# lambda/index.py
import json
import re
import urllib.request

# FastAPIの公開URL（Colab上で動作中のもの）
FASTAPI_URL = "https://55aa-34-83-99-13.ngrok-free.app/predict"

# Lambda コンテキストからリージョンを抽出する関数
def extract_region_from_arn(arn):
    match = re.search('arn:aws:lambda:([^:]+):', arn)
    if match:
        return match.group(1)
    return "us-east-1"  # デフォルト値

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))

        # Cognitoユーザー情報（オプション）
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")

        # リクエストの読み取り
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        print("Processing message:", message)

        # FastAPI へのペイロード作成
        fastapi_payload = {
            "message": message,
            "conversationHistory": conversation_history
        }

        # FastAPI に POST リクエストを送信
        req = urllib.request.Request(
            FASTAPI_URL,
            data=json.dumps(fastapi_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req) as res:
            fastapi_response = json.loads(res.read().decode("utf-8"))

        assistant_response = fastapi_response["response"]

        # 会話履歴を更新
        updated_history = conversation_history.copy()
        updated_history.append({"role": "user", "content": message})
        updated_history.append({"role": "assistant", "content": assistant_response})

        # 正常レスポンス
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": updated_history
            })
        }

    except Exception as error:
        print("Error:", str(error))

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
