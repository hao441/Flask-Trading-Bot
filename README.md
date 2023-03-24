<<<<<<< HEAD
<<<<<<< HEAD
# Flask Trading Bot
A trading bot built on flask that has the ability to convert alert notifications from TradingView strategies into futures orders on exchanges.

The Bot supports four core functions that manage the alerts.
=======
# Flask Trading Bot
A trading bot built on flask that has the ability to convert alert notifications from TradingView strategies into futures orders on exchanges.

<<<<<<< HEAD
The Bot is supports four core functions that manage the alerts.
>>>>>>> 7072f48 (README Updated)
=======
The Bot supports four core functions that manage the alerts.
>>>>>>> d42a58a (README Updated)

## Place Long
    
    endpoint: /placelong
    
This Endpoint manages new Long orders issued by the tradingview alert.

Exchange API Sequence
1. Cancel All Orders
2. Close all Positions
3. Switch to Isolated Margin
4. Set Leverage
5. Get Wallet Balance
6. Get Latest Price of Asset
7. Place Long Order

    - Calculate quantity as: 
    ```
    rount([wallet_balance]*[leverage]*0.95)/[latest_price],2)
    ```
    - Calculate Stop Loss as 
    ```
    rount([latest_price]*(1-[stop_loss_percentage]),2)
    ```
    - Calculate Take Profit as 
    ```
    rount([latest_price]*(1+[stop_loss_percentage]),2)
    ```
8. Get Average Order Price
9. Update Stop Loss and Take Profit with Average Order Price

## Place Short
    
    endpoint: /placeshort
    
This Endpoint manages new Short orders issued by the tradingview alert.

Exchange API Sequence
1. Cancel All Orders
2. Close all Positions
3. Switch to Isolated Margin
4. Set Leverage
5. Get Wallet Balance
6. Get Latest Price of Asset
7. Place Short Order

    - Calculate quantity as: 
    ```
    rount([wallet_balance]*[leverage]*0.95)/[latest_price],2)
    ```
    - Calculate Stop Loss as 
    ```
    rount([latest_price]*(1+[stop_loss_percentage]),2)
    ```
    - Calculate Take Profit as 
    ```
    rount([latest_price]*(1-[stop_loss_percentage]),2)
    ```
8. Get Average Order Price
9. Update Stop Loss and Take Profit with Average Order Price

## Close Long
    
    endpoint: /closelong
    
This Endpoint manages close long requests issued by the tradingview alert.

Exchange API Sequence
1. Cancel Short Orders
2. Close all Long Positions

## Close Short
    
    endpoint: /closeshort
    
This Endpoint manages close short requests issued by the tradingview alert.

Exchange API Sequence
1. Cancel Short Orders
2. Close all Short Positions

<<<<<<< HEAD
=======
Flask Trading Bot
>>>>>>> 5e75ecc (first commit)
=======
>>>>>>> 7072f48 (README Updated)
