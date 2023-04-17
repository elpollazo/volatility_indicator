#!/bin/bash

file="./data/tickers.txt"

sum=1

delay=0

#Check if the file exists
if [[ -s "$file" ]]; then
  #Launching processes
  echo "Launching processes"
  while IFS= read -r pair; do
    python3 main.py "$pair" "$delay" > ./logs/$pair.txt 2>&1 &
    sleep 5
    echo "Current processes: $sum, pair: $pair"
    sum=$(($sum+1))
    if [ "$sum" -eq 500 ]; then
      delay=$(($delay+1))
    fi
  done < "$file"
else
  echo "File does not exist"
fi

echo "All process launched"