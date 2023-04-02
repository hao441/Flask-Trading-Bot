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
	
	
	jsonResponse = response.json()

	if Info == "Balance":
		return jsonResponse["result"]["list"][0]["coin"][0]["walletBalance"]
	elif Info == "Price":
		return jsonResponse["result"]["list"][0]["lastPrice"]
	elif Info == "Position":
		return jsonResponse["result"]["list"][0]["avgPrice"]
	else:
		return jsonResponse

def genSignature(payload):
	param_str= str(time_stamp) + api_key + recv_window + payload
	hash = hmac.new(bytes(secret_key, "utf-8"), param_str.encode("utf-8"),hashlib.sha256)
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

@app.route('/', methods=['GET'])
def deaultGet():
	return "Hello"

@app.route('/getposition', methods=['POST'])
def requestPosition():
	return getPosition()

@app.route('/placelong', methods=['POST'])
def placeLong():
	data = json.loads(request.data)
	leverage = data["leverage"]
	receivedStopLoss = data["stopLoss"]
	receivedTakeProfile = data["takeProfit"]		

	closePosition("Sell")
	cancelAllOrders()
	switchToIsolated(leverage)
	setLeverage(leverage)
	
	stopLossPercentage = 0.1
	takeProfitPercentage = 0.1

	walletBalance = float(getWalletBalance())
	currentPrice = float(checkPrice())
	quantity = str(round(((walletBalance*0.95)*int(leverage))/currentPrice,1))
	stopLoss = str(round(currentPrice*(1-stopLossPercentage), 1))
	takeProfit = str(round(currentPrice*(1+takeProfitPercentage),1))

	print(f'takeprofit is: {takeProfit}')

	longResponse = placeOrder("Buy", quantity, stopLoss, takeProfit)
	print(longResponse)

	# time.sleep(5)

	averagePrice = float(getPosition())
	updatedStopLoss = str(round(averagePrice*(1-stopLossPercentage), 1))
	updatedTakeProfit = str(round(averagePrice*(1+takeProfitPercentage),1))
	tradingStopResponse = tradingStopUpdate(updatedStopLoss,updatedTakeProfit)

	return {"placeOrderResponse":longResponse, "tradingStopResponse":tradingStopResponse}

@app.route('/placeshort', methods=['POST'])
def placeShort():
	data = json.loads(request.data)
	leverage = data["leverage"]

	closePosition("Buy")
	cancelAllOrders()
	switchToIsolated(leverage)
	setLeverage(leverage)
	
	stopLossPercentage = 0.1
	takeProfitPercentage = 0.1

	walletBalance = float(getWalletBalance())
	currentPrice = float(checkPrice())
	quantity = str(round(((walletBalance*0.95)*int(leverage))/currentPrice,1))
	stopLoss = str(round(currentPrice*(1+stopLossPercentage), 1))
	takeProfit = str(round(currentPrice*(1-takeProfitPercentage),1))

	print(f'takeprofit is: {takeProfit}')

	longResponse = placeOrder("Sell", quantity, stopLoss, takeProfit)
	print(longResponse)

	# time.sleep(5)

	averagePrice = float(getPosition())
	updatedStopLoss = str(round(averagePrice*(1+stopLossPercentage), 1))
	updatedTakeProfit = str(round(averagePrice*(1-takeProfitPercentage),1))
	tradingStopResponse = tradingStopUpdate(updatedStopLoss,updatedTakeProfit)

	return {"placeOrderResponse":longResponse, "tradingStopResponse":tradingStopResponse}

@app.route('/closelong', methods=['POST'])
def closeLong():
	cancelAllOrders()
	closeLongResponse = closePosition("Buy")
	
	# time.sleep(5)

	return {'response': closeLongResponse}

@app.route('/closeshort', methods=['POST'])
def closeShort():
	cancelAllOrders()
	closeShortResponse = closePosition("Sell")

	# time.sleep(5)

	return {'response': closeShortResponse}

@app.route('/test', methods=['POST'])
def helloWorld():
	data = json.loads(request.data)
	return data["leverage"]
