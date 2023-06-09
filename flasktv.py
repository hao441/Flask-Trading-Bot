import requests, json, os, time, hashlib, hmac, uuid, math
from flask import Flask, request, jsonify

app = Flask(__name__)
#test env variables
# webhook_pass="d41d8cd98f00b204e9800998ecf8427e"
# api_key='NiCJLp1G33Jdus1Rnr'
# secret_key='ZEVyJNm3rSa2JwrjjT1HY1TXU62gSf3grgAZ'

#prod env variables
webhook_pass=str(os.getenv('WEBHOOK_PASS'))
api_key=str(os.getenv('BYBIT_TEST_API_KEY'))
secret_key=str(os.getenv('BYBIT_TEST_API_SECRET'))

print(f"api_key is: {api_key}")
print(f"secret_key is: {secret_key}")

httpClient=requests.Session()
recv_window=str(5000)
url="https://api-testnet.bybit.com" # Testnet endpoint

def create_app():
	return app

def HTTP_Request(endPoint,method,payload,Info):

	global time_stamp
	time_stamp=str(int(time.time() * 10 ** 3))
	signature=genSignature(payload)
	if(method=="POST"):
		headers = {
			'X-BAPI-API-KEY': api_key,
			'X-BAPI-SIGN': signature,
			'X-BAPI-SIGN-TYPE': '2',
			'X-BAPI-TIMESTAMP': time_stamp,
			'X-BAPI-RECV-WINDOW': recv_window,
			'Content-Type': 'application/json'
		}
	else:
		headers = {
		'X-BAPI-SIGN': signature,
		'X-BAPI-API-KEY': api_key,
		'X-BAPI-TIMESTAMP': time_stamp,
		'X-BAPI-RECV-WINDOW': recv_window,
		'cdn-request-id': 'test-001'
		}

	if(method=="POST"):
		response = httpClient.request(method, url+endPoint, headers=headers, data=payload)
	else:
		response = httpClient.request(method, url+endPoint+"?"+payload, headers=headers)
	
	print(response)
	jsonResponse = response.json()

	if Info == "Balance":
		return jsonResponse["result"]["list"][0]["coin"][0]["walletBalance"]
	elif Info == "Price":
		return jsonResponse["result"]["list"][0]["lastPrice"]
	elif Info == "Position":
		print(jsonResponse)
		return jsonResponse["result"]["list"][0]["avgPrice"]
	else:
		return jsonResponse

def genSignature(payload):
	param_str= str(time_stamp) + str(api_key) + recv_window + payload
	hash = hmac.new(bytes(str(secret_key), "utf-8"), param_str.encode("utf-8"),hashlib.sha256)
	signature = hash.hexdigest()
	return signature

def getWalletBalance():
	endpoint="/v5/account/wallet-balance"
	method="GET"
	params="accountType=CONTRACT&coin=USDT"
	response = HTTP_Request(endpoint,method,params,"Balance")
	print(response)
	return response

def switchToIsolated(leverage):
	endpoint="/v5/position/switch-isolated"
	method="POST"
	preParams={"category":"linear","symbol":"BTCUSDT","tradeMode":1, "buyLeverage":leverage, "sellLeverage":leverage}
	postParams=json.dumps(preParams)
	response = HTTP_Request(endpoint,method,postParams,"Leverage")
	print(response)
	return response

def setLeverage(leverage):
	endpoint="/v5/position/set-leverage"
	method="POST"
	preParams={"category":"linear","symbol":"BTCUSDT","buyLeverage":leverage, "sellLeverage":leverage}
	postParams=json.dumps(preParams)
	response = HTTP_Request(endpoint,method,postParams,"Leverage")
	print(response)
	return response

def checkPrice():
	endpoint="/v5/market/tickers"
	method="GET"
	params="category=linear&symbol=BTCUSDT"
	response = HTTP_Request(endpoint,method,params,"Price")
	print(response)
	return response

def placeOrder(side, quantity, stopLoss, takeProfit):
    # #Create Order
    endpoint="/v5/order/create"
    method="POST"
    orderLinkId=uuid.uuid4().hex
    preParams={"category":"linear","symbol":"BTCUSDT","side":side,"orderType":"Market","qty":quantity,"timeInForce":"IOC","positionIdx":0, "stopLoss": stopLoss, "takeProfit":takeProfit}
    postParams=json.dumps(preParams)
    response = HTTP_Request(endpoint,method,postParams,"Create")
    print(response)
    return {'response': response}

def closePosition(side):
	endpoint="/v5/order/create"
	method="POST"
	direction = "Sell" if side == "Buy" else "Buy"
	print(f'direction is {direction}')
	preParams = {"category":"linear","symbol":"BTCUSDT","side":direction,"orderType":"Market","qty":"0","timeInForce":"IOC","positionIdx":0, "reduceOnly":"true"}
	postParams = json.dumps(preParams)
	response = HTTP_Request(endpoint,method,postParams,"Create")
	return {'response': response}

def cancelAllOrders():
    endpoint="/v5/order/cancel-all"
    method="POST"
    params='{"category":"linear","settleCoin":"BTC"}'
    response = HTTP_Request(endpoint,method,params,"Cancel-all")
    return {'response': response}

def getPosition():
	endpoint="/v5/position/list"
	method="GET"
	params="category=linear&symbol=BTCUSDT"
	response = HTTP_Request(endpoint,method,params,"Position")
	print(response)
	return response

def tradingStopUpdate(stopLoss, takeProfit):
    endpoint="/v5/position/trading-stop"
    method="POST"
    preParams={"category":"linear","symbol":"BTCUSDT","stopLoss": stopLoss,"takeProfit":takeProfit, "positionIdx":0}
    postParams=json.dumps(preParams)
    response = HTTP_Request(endpoint,method,postParams,"Trading-Stop-Update")
    return {'response': response}

@app.route('/')
def deaultGet():
	return "Hello"

@app.route('/getposition', methods=['POST'])
def requestPosition():
	return getPosition()

@app.route('/placelong', methods=['POST'])
def placeLong():
	data = json.loads(request.data)

	webhook_auth = data["auth_key"]

	if webhook_auth != webhook_pass:
		return {"reuslt": "fail", "message": "no"}

	leverage = data["leverage"]
	receivedStopLoss = data["stopLoss"]
	receivedTakeProfit = data["takeProfit"]		

	closePosition("Sell")
	cancelAllOrders()
	switchToIsolated(leverage)
	setLeverage(leverage)

	walletBalance = float(getWalletBalance())
	currentPrice = float(checkPrice())
	quantity = str(math.floor((((walletBalance*0.95)*int(leverage))/currentPrice)*1000)/1000.0)
	stopLoss = str(round(currentPrice*(1-receivedStopLoss), 2))
	takeProfit = str(round(currentPrice*(1+receivedTakeProfit),2))

	print(f'wallet balance is: {walletBalance}')
	print(f'takeprofit is: {takeProfit}')

	longResponse = placeOrder("Buy", quantity, stopLoss, takeProfit)
	print(longResponse)

	# time.sleep(5)

	averagePrice = float(getPosition())
	updatedStopLoss = str(round(averagePrice*(1-receivedStopLoss), 2))
	updatedTakeProfit = str(round(averagePrice*(1+receivedTakeProfit),2))
	tradingStopResponse = tradingStopUpdate(updatedStopLoss,updatedTakeProfit)

	return {"placeOrderResponse":longResponse, "tradingStopResponse":tradingStopResponse}

@app.route('/placeshort', methods=['POST'])
def placeShort():
	data = json.loads(request.data)

	webhook_auth = data["auth_key"]

	if webhook_auth != webhook_pass:
		return {"reuslt": "fail", "message": "no"}

	leverage = data["leverage"]
	receivedStopLoss = data["stopLoss"]
	receivedTakeProfit = data["takeProfit"]


	closePosition("Buy")
	cancelAllOrders()
	switchToIsolated(leverage)
	setLeverage(leverage)

	walletBalance = float(getWalletBalance())
	currentPrice = float(checkPrice())
	quantity = str(math.floor((((walletBalance*0.95)*int(leverage))/currentPrice)*1000)/1000.0)
	stopLoss = str(round(currentPrice*(1+receivedStopLoss), 1))
	takeProfit = str(round(currentPrice*(1-receivedTakeProfit),1))

	print(f'takeprofit is: {takeProfit}')

	longResponse = placeOrder("Sell", quantity, stopLoss, takeProfit)
	print(longResponse)

	# time.sleep(5)

	averagePrice = float(getPosition())
	updatedStopLoss = str(round(averagePrice*(1+receivedStopLoss), 1))
	updatedTakeProfit = str(round(averagePrice*(1-receivedTakeProfit),1))
	tradingStopResponse = tradingStopUpdate(updatedStopLoss,updatedTakeProfit)

	return {"placeOrderResponse":longResponse, "tradingStopResponse":tradingStopResponse}

@app.route('/closelong', methods=['POST'])
def closeLong():
	data = json.loads(request.data)

	webhook_auth = data["auth_key"]

	if webhook_auth != webhook_pass:
		return {"reuslt": "fail", "message": "no"}
	
	cancelAllOrders()
	closeLongResponse = closePosition("Buy")
	
	# time.sleep(5)

	return {'response': closeLongResponse}

@app.route('/closeshort', methods=['POST'])
def closeShort():
	data = json.loads(request.data)

	webhook_auth = data["auth_key"]

	if webhook_auth != webhook_pass:
		return {"reuslt": "fail", "message": "no"}
	
	cancelAllOrders()
	closeShortResponse = closePosition("Sell")

	# time.sleep(5)

	return {'response': closeShortResponse}

@app.route('/test', methods=['POST'])
def helloWorld():
	data = json.loads(request.data)
	return data["leverage"]

if __name__ == '__main__':
	app.run()