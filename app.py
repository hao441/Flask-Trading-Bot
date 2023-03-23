import requests, json, config, time, hashlib, hmac, base64, uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def hello_world():
	return "<p>Hi, World!</p>"


@app.route("/bybit")
api_key='XXXXXXXXX'
secret_key='XXXXXXXXX'
httpClient=requests.Session()
recv_window=str(5000)
url="https://api-testnet.bybit.com" # Testnet endpoint

def HTTP_Request(endPoint,method,payload,Info):
    global time_stamp
    time_stamp=str(int(time.time() * 10 ** 3))
    signature=genSignature(payload)
    headers = {
        'X-BAPI-API-KEY': api_key,
        'X-BAPI-SIGN': signature,
        'X-BAPI-SIGN-TYPE': '2',
        'X-BAPI-TIMESTAMP': time_stamp,
        'X-BAPI-RECV-WINDOW': recv_window,
        'Content-Type': 'application/json'
    }
    if(method=="POST"):
        response = httpClient.request(method, url+endPoint, headers=headers, data=payload)
    else:
        response = httpClient.request(method, url+endPoint+"?"+payload, headers=headers)
    print(response.text)
    print(Info + " Elapsed Time : " + str(response.elapsed))

def genSignature(payload):
    param_str= str(time_stamp) + api_key + recv_window + payload
    hash = hmac.new(bytes(secret_key, "utf-8"), param_str.encode("utf-8"),hashlib.sha256)
    signature = hash.hexdigest()
    return signature

#Create Order
endpoint="/contract/v3/private/order/create"
method="POST"
orderLinkId=uuid.uuid4().hex
params='{"symbol": "BTCUSDT","side": "Buy","positionIdx": 1,"orderType": "Limit","qty": "0.001","price": "10000","timeInForce": "GoodTillCancel","orderLinkId": "' + orderLinkId + '"}'
HTTP_Request(endpoint,method,params,"Create")

@app.route('/webhook', methods=['POST'])
def webhook():
	data = json.loads(request.data)

	if data['pass'] != config.WEBHOOK_PASS:
		return {
			"code":"error",
			"message":"incorrect pass"
		}
		
	return {
		"code":"success",
		"message":"success"
	}