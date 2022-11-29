from web3 import Web3
from termcolor import cprint
import time
import json
import random
from tqdm import tqdm
import decimal
import requests
from tabulate import tabulate
from decimal import Decimal


currency_price = []
def prices():
    response = requests.get(url=f'https://api.gateio.ws/api/v4/spot/tickers')
    currency_price.append(response.json())

def intToDecimal(qty, decimal):
    return int(qty * int("".join(["1"] + ["0"]*decimal)))

def decimalToInt(qty, decimal):
    return qty / int("".join((["1"]+ ["0"]*decimal)))


def check_balance(privatekey, rpc_chain, symbol):
    try:
            
        web3 = Web3(Web3.HTTPProvider(rpc_chain))
        account = web3.eth.account.privateKeyToAccount(privatekey)
        balance = web3.eth.get_balance(web3.toChecksumAddress(account.address))

        humanReadable = web3.fromWei(balance,'ether')

        # check price of token
        for currency in currency_price[0]:
            if currency['currency_pair'] == f'{symbol}_USDT':
                price_ = Decimal(currency['last'])
                price = price_ + price_ * Decimal(0.2)

        gas = web3.eth.gas_price
        gasPrice = decimalToInt(gas, 18)

        return round(Decimal(humanReadable) - Decimal(Decimal(gasPrice)*Decimal(price)) - Decimal(0.001), 7)


    except Exception as error:
        # cprint(f'error : {error}', 'yellow')
        None

def check_token_balance(privatekey, rpc_chain, address_contract, ERC20_ABI):
    try:

        web3 = Web3(Web3.HTTPProvider(rpc_chain))
        account = web3.eth.account.privateKeyToAccount(privatekey)
        wallet = account.address
        token_contract = web3.eth.contract(address=web3.toChecksumAddress(address_contract), abi=ERC20_ABI) 
        token_balance = token_contract.functions.balanceOf(web3.toChecksumAddress(wallet)).call()

        symbol = token_contract.functions.symbol().call()
        token_decimal = token_contract.functions.decimals().call()

        humanReadable = decimalToInt(token_balance, token_decimal) 

        cprint(f'\nbalance : {round(humanReadable, 5)} {symbol}', 'white')

        return humanReadable

    except Exception as error:
        # cprint(f'error : {error}', 'yellow')
        None

table = []
def transfer_token(privatekey, amount_to_transfer, to_address, chain_id, scan, rpc_chain, address_contract, ERC20_ABI):
    try:

        web3 = Web3(Web3.HTTPProvider(rpc_chain))

        token_contract = web3.eth.contract(address=Web3.toChecksumAddress(address_contract), abi=ERC20_ABI)
        account = web3.eth.account.privateKeyToAccount(privatekey)
        address = account.address
        nonce = web3.eth.getTransactionCount(address)

        symbol = token_contract.functions.symbol().call()
        token_decimal = token_contract.functions.decimals().call()

        amount = intToDecimal(amount_to_transfer, token_decimal) 
        gasLimit = web3.eth.estimate_gas({'to': Web3.toChecksumAddress(to_address), 'from': Web3.toChecksumAddress(address),'value': web3.toWei(0.0001, 'ether')}) + random.randint(70000, 200000)
        
        tx_built = token_contract.functions.transfer(
            Web3.toChecksumAddress(to_address),
            int(amount)
            ).buildTransaction({
                'chainId': chain_id,
                'gas': gasLimit,
                'gasPrice': web3.eth.gas_price,
                'nonce': nonce,
            })

        tx_signed = web3.eth.account.signTransaction(tx_built, privatekey)
        tx_hash = web3.eth.sendRawTransaction(tx_signed.rawTransaction)

        cprint(f'>>> transfer : {decimal.Decimal(str(amount_to_transfer))} {symbol} | {address} => {to_address} | {scan}/{web3.toHex(tx_hash)}', 'green')
        table.append([f'{decimal.Decimal(str(amount_to_transfer))} {symbol}', address, to_address, '\u001b[32msend\u001b[0m'])

    except Exception as error:
        cprint(f'>>> transfer : {privatekey} | {error}', 'red')
        try:
            table.append([f'{decimal.Decimal(str(amount_to_transfer))} {symbol}', address, to_address, '\u001b[31merror\u001b[0m'])
        except:
            table.append([f'{symbol}', address, to_address, '\u001b[31merror\u001b[0m'])
    
def transfer_eth(privatekey, amount_to_transfer, to_address, chain_id, scan, rpc_chain, symbol):
    try:

        web3 = Web3(Web3.HTTPProvider(rpc_chain))

        account = web3.eth.account.privateKeyToAccount(privatekey)
        address = account.address
        nonce = web3.eth.getTransactionCount(address)

        amount = intToDecimal(amount_to_transfer, 18) 
        gasLimit = web3.eth.estimate_gas({'to': Web3.toChecksumAddress(to_address), 'from': Web3.toChecksumAddress(address),'value': web3.toWei(0.0001, 'ether')}) + random.randint(10000, 30000)

        tx_built = {
            'chainId': chain_id,
            'gas': gasLimit,
            'gasPrice': web3.eth.gas_price,
            'nonce': nonce,
            'to': Web3.toChecksumAddress(to_address),
            'value': int(amount)
        }

        tx_signed = web3.eth.account.signTransaction(tx_built, privatekey)
        tx_hash = web3.eth.sendRawTransaction(tx_signed.rawTransaction)

        cprint(f'>>> transfer : {decimal.Decimal(str(amount_to_transfer))} {symbol} | {address} => {to_address} | {scan}/{web3.toHex(tx_hash)}', 'green')
        table.append([f'{decimal.Decimal(str(amount_to_transfer))} {symbol}', address, to_address, '\u001b[32msend\u001b[0m'])

    except Exception as error:
        cprint(f'>>> transfer : {privatekey} | {error}', 'red')
        try:
            table.append([f'{decimal.Decimal(str(amount_to_transfer))} {symbol}', address, to_address, '\u001b[31merror\u001b[0m'])
        except:
            table.append([f'{symbol}', address, to_address, '\u001b[31merror\u001b[0m'])

RPC = [
    {'chain': 'Ethereum', 'chain_id': 1, 'rpc': 'https://rpc.ankr.com/eth', 'scan': 'https://etherscan.io/tx', 'token': 'ETH'},

    {'chain': 'Optimism', 'chain_id': 10, 'rpc': 'https://rpc.ankr.com/optimism', 'scan': 'https://optimistic.etherscan.io/tx', 'token': 'ETH'},

    {'chain': 'BSC', 'chain_id': 56, 'rpc': 'https://bsc-dataseed.binance.org', 'scan': 'https://bscscan.com/tx', 'token': 'BNB'},

    {'chain': 'Polygon', 'chain_id': 137, 'rpc': 'https://polygon-rpc.com', 'scan': 'https://polygonscan.com/tx', 'token': 'MATIC'},

    {'chain': 'Arbitrum One', 'chain_id': 42161, 'rpc': 'https://arb1.arbitrum.io/rpc', 'scan': 'https://arbiscan.io/tx', 'token': 'ETH'},

    {'chain': 'AVAX', 'chain_id': 43114, 'rpc': 'https://api.avax.network/ext/bc/C/rpc', 'scan': 'https://snowtrace.io/tx', 'token': 'AVAX'},

    {'chain': 'Arbitrum Nova', 'chain_id': 42170, 'rpc': 'https://nova.arbitrum.io/rpc', 'scan': 'https://nova-explorer.arbitrum.io/tx', 'token': 'ETH'},

    {'chain': 'Fantom', 'chain_id': 250, 'rpc': 'https://rpc.ankr.com/fantom', 'scan': 'https://ftmscan.com/tx', 'token': 'FTM'},
]

if __name__ == "__main__":

    cprint(f'\n============================================= hodlmod.eth =============================================', 'cyan')

    cprint(f'\nsubscribe to us : https://t.me/hodlmodeth', 'magenta')
    
    with open("private_keys.txt", "r") as f:
        keys_list = [row.strip() for row in f]

    with open("recepients.txt", "r") as f:
        recepients = [row.strip() for row in f]

    with open("erc20.json", "r") as file:
        ERC20_ABI = json.load(file)

    prices()

    zero = -1
    for privatekey in keys_list:
        zero = zero + 1
        cprint(f'\n=============== start : {privatekey} ===============', 'white')

        to_address = recepients[zero]

        AMOUNT_TO_TRANSFER = round(random.uniform(1, 3), 5) # от 1 до 3, 5 цифр после точки
        # AMOUNT_TO_TRANSFER = 0.1 # фиксированный amount
        # AMOUNT_TO_TRANSFER = 'all_balance' # весь баланс
        CHAIN = 'Optimism' # Ethereum | Optimism | BSC | Polygon | Fantom | Arbitrum One | Arbitrum Nova | AVAX
        ADDRESS_CONTRACT = '0x4200000000000000000000000000000000000042' # пусто если eth

        for x in RPC:
            if x['chain'] == CHAIN:
                chain_id = x['chain_id']
                scan = x['scan']
                rpc_chain = x['rpc']
                symbol_chain = x['token']

        if ADDRESS_CONTRACT == '':

            if AMOUNT_TO_TRANSFER == 'all_balance':
                AMOUNT_TO_TRANSFER = check_balance(privatekey, rpc_chain, symbol_chain)

            transfer_eth(
                privatekey, 
                AMOUNT_TO_TRANSFER, 
                to_address, 
                chain_id, 
                scan, 
                rpc_chain, 
                symbol_chain
            )

        else:

            if AMOUNT_TO_TRANSFER == 'all_balance':
                AMOUNT_TO_TRANSFER = check_token_balance(privatekey, rpc_chain, ADDRESS_CONTRACT, ERC20_ABI)

            transfer_token(
                privatekey, 
                AMOUNT_TO_TRANSFER, 
                to_address, 
                chain_id, 
                scan, 
                rpc_chain, 
                ADDRESS_CONTRACT,
                ERC20_ABI
            )


        x = random.randint(20, 60)
        for i in tqdm(range(x), desc='sleep ', bar_format='{desc}: {n_fmt}/{total_fmt}'):
            time.sleep(1)

    headers = ['amount', 'from', 'to', 'result']
    cprint(tabulate(table, headers, tablefmt='double_outline'), 'white')
