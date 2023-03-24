import requests, json, config, time, hashlib, hmac, base64, uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

api_key=config.BYBIT_TEST_API_KEY
secret_key=config.BYBTI_TEST_API_SECRET
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


def HTTP_GET_Request(endPoint,method,payload,Info):

	global time_stamp
	time_stamp=str(int(time.time() * 10 ** 3))
	signature=genSignature(payload)
	headers = {
		'X-BAPI-SIGN': signature,
		'X-BAPI-API-KEY': api_key,
		'X-BAPI-TIMESTAMP': time_stamp,
		'X-BAPI-RECV-WINDOW': recv_window,
		'cdn-request-id': 'test-001'
	}

	response = httpClient.request(method, url+endPoint+"?accountType=CONTRACT&coin=USDT", headers=headers)
	print(response.text)
	print(Info + " Elapsed Time : " + str(response.elapsed))
	return {"result": response.json()}

def genSignature(payload):
	param_str= str(time_stamp) + api_key + recv_window + payload
	hash = hmac.new(bytes(secret_key, "utf-8"), param_str.encode("utf-8"),hashlib.sha256)
	signature = hash.hexdigest()
	return signature

def getWalletBalance():
	endpoint="/v5/account/wallet-balance"
	method="GET"
	params="accountType=CONTRACT&coin=USDT"
	response = HTTP_GET_Request(endpoint,method,params,"Balance")
	print(response)
	return response

def setLeverage():
	return

def checkPrice():
	return

def placeOrder(symbol, side, quantity):
    # #Create Order
    endpoint="/v5/order/create"
    method="POST"
    orderLinkId=uuid.uuid4().hex
    preParams={"category":"linear","symbol":symbol,"side":side,"orderType":"Market","qty":quantity,"timeInForce":"IOC","positionIdx":0}
    postParams=json.dumps(preParams)
    response = HTTP_Request(endpoint,method,postParams,"Create")
    print(response)
    return {'response': response}

def closePosition(symbol, side):
	endpoint="/v5/order/create"
	method="POST"
	direction = "Sell" if side == "Buy" else "Buy"
	print(f'direction is {direction}')
	preParams = {"category":"linear","symbol":symbol,"side":direction,"orderType":"Market","qty":"0","timeInForce":"IOC","positionIdx":0, "reduceOnly":"true"}
	postParams = json.dumps(preParams)
	response = HTTP_Request(endpoint,method,postParams,"Create")
	return {'response': response}

def cancelAllOrders():
    endpoint="/v5/order/cancel-all"
    method="POST"
    params='{"category":"linear","settleCoin":"BTC"}'
    response = HTTP_Request(endpoint,method,params,"Cancel-all")
    return {'response': response}

@app.route('/cancelall', methods=['POST'])
def cancelAllOrders():
    endpoint="/v5/order/cancel-all"
    method="POST"
    params='{"category":"linear","settleCoin":"BTC"}'
    response = HTTP_Request(endpoint,method,params,"Cancel-all")
    return {'response': response}

@app.route('/walletbalance', methods=['GET'])
def walletBalance():
	response = getWalletBalance()
	print(response)
	return response

@app.route('/placelong', methods=['POST'])
def placeLong():
	longResponse = placeOrder("BTCUSDT", "Buy", "0.01")
	return {"result": longResponse}

@app.route('/placeshort', methods=['POST'])
def placeShort():
    shortResponse = placeOrder("BTCUSDT", "Sell", "0.01")
    print(shortResponse)
    return {"result": shortResponse}

@app.route('/closelong', methods=['POST'])
def closeLong():
	cancelAllOrders()
	closeLongResponse = closePosition("BTCUSDT", "Buy")
	print(f'closeLongResponse: {closeLongResponse}')
	return {'response': closeLongResponse}

@app.route('/closeshort', methods=['POST'])
def closeShort():
	cancelAllOrders()
	closeShortResponse = closePosition("BTCUSDT", "Sell")
	return {'response': closeShortResponse}