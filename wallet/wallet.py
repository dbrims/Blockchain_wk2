from constants import *
from bit import wif_to_key, PrivateKey,PrivateKeyTestnet
import subprocess
import json
import os
from web3 import Web3
from dotenv import load_dotenv
from web3.middleware import geth_poa_middleware
from eth_account import Account
import time
from getpass import getpass
from bit import PrivateKeyTestnet, PrivateKey
import requests
from bitcoinlib.wallets import HDWallet

def validate_coin(coin):
    if coin==ETH or coin==BTCTEST or coin==BTC or coin==LTC:
        return 1
    else:
        print('That is not one of the supported coins.')
        return 0
    
def validate_amount(amount, coin):
    if coin==BTC or coin==BTCTEST:
        try:
            if amount[0]=='$':
                value=float(amount[1:])
            else:
                value=float(amount)
            return 1, value
        except:
            print(f'{amount} is not a valid value, please reenter')
        return 0, amount
    else: # the value entered is actually in wei, we need to convert it to eth
        try:
            if amount[0]=='$':
                wei=int(amount[1:])
                eth=int(wei*1000000000000000000)
            else:
                wei=int(amount)
                eth=int(wei*1000000000000000000)
            return 1, eth
        except:
            print(f'{amount} is not a valid value, please reenter an integer number')
        return 0, amount
    
def trans_data():
    c=0
    while c==0:
        coin=input("what crypto do you want to trade? (BTC, BTC-test, ETH, and LTC supported) ").lower()
        c=validate_coin(coin)
    print('Good Choice')
    a=0
    while a==0:
        amount_str=input(f"What amount of {coin.upper()}, do you want to trade? ")
        a, amount = validate_amount(amount_str, coin)
    print(f'We will send {amount/1000000000000000000} {coin.upper()}')
    a=0
    while a==0:
        to=input(f'What is the account you want to send {amount/1000000000000000000} {coin.upper()} to: ')
        confirm=input(f'is {to} the correct address? (yes/no)').lower()
        if confirm=='yes':
            a=1
    print('we are processing your request now!')
    return coin, amount, to

def derive_wallets():
    mnem=os.getenv("MNEMONIC")
    coins={}
    types=[BTC, BTCTEST, ETH, LTC]
    for type in types:
        command = f'php derive -g --mnemonic=mnem --coin={type} --numderive=3 --format=json'
        p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        keys = json.loads(output)
        coins[type]=keys
    return coins

def priv_key_to_account(coin, coins):
    if coin==ETH:
        key=coins[coin][0]['privkey']
        return Account.privateKeyToAccount(key)
    elif coin==BTC:
        key=coins[coin][0]['privkey']
        return PrivateKey(key)
    elif coin==BTCTEST:
        key=coins[coin][0]['privkey']
        return PrivateKeyTestnet(key)
    elif coin==LTC:
        key=coins[coin][0]['privkey']
        return HDWallet.create(name='Simple_Wallet2', keys=key)
    
def create_tx(coin, account, to, amount):
    if coin==ETH:
        w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
        gasEstimate = w3.eth.estimateGas(
        {"from": account.address, "to": to, "value": amount}
        )
        return {
            "from": account.address,
            "to": to,
            "value": amount,
            "gasPrice": w3.eth.gasPrice,
            "gas": gasEstimate,
            "nonce": w3.eth.getTransactionCount(account.address),
        }
    elif coin==BTC or coin==BTCTEST:
        return account.create_transaction([(to, amount, BTC)])
    elif coin==LTC:
        return account.transaction_create([(to, amount, BTC)], network='litecoin')
    
def send_tx(coin, account, to, amount):
    tx = create_tx(coin,account, to, amount)
    if coin==ETH:
        w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
        signed_tx = account.sign_transaction(tx)
        result=w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return result.hex()
    elif coin==BTC or coin==BTCTEST:
        result=account.send([(to, amount, BTC)])
        return result
    elif coin==LTC:
        return account.send([(to, amount, BTC)], network='litecoin', offline=True)
    
# docs for trans api is here https://sochain.com/api#get-tx    
def track_trans(result, coin):
    if coin==ETH:
        w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
        return w3.eth.getTransaction(result)
    elif coin==BTC: 
        time.sleep(30)
        url = f'https://sochain.com/api/v2/get_tx/BTC/{result}'
        response_data = requests.get(url)
        return response_data.json() 
    elif coin==BTCTEST:
        time.sleep(30)
        url=f'https://sochain.com/api/v2/get_tx/BTCTEST/{result}'
        response_data = requests.get(url)
        return response_data.json() 
    elif coin==LTC:
        time.sleep(30)
        url=f'https://sochain.com/api/v2/get_tx/LTC/{result}'
        response_data = requests.get(url)
        return response_data.json() 
    
def script():  
    coins=derive_wallets()
    coin, amount, to = trans_data()
    account=priv_key_to_account(coin, coins)
    result=send_tx(coin, account, to, amount)
    print('*'*40)
    print(f'\nTransaction Hash: {result}')
    trans_log=track_trans(result, coin)
    print('\nThe transaction data is:')
    return trans_log



    
