#!/bin/bash

## Create cold key for the owner
btcli wallet new_coldkey --wallet.name owner
echo -e "\\e[32mOwner's coldkey created succesfully\\e[0m"

## Setup miner's wallets
btcli wallet new_coldkey --wallet.name miner
btcli wallet new_hotkey --wallet.name miner --wallet.hotkey default
echo -e "\\e[32mMiner's wallets created succesfully\\e[0m"

## Setup validator's wallets
btcli wallet new_coldkey --wallet.name validator
btcli wallet new_hotkey --wallet.name validator --wallet.hotkey default
echo -e "\\e[32mValidator's wallets created succesfully\\e[0m"
