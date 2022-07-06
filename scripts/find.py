from web3 import Web3
from hexbytes import HexBytes
import string
from itertools import permutations
import random
import math
from multiprocessing import Process, Queue
import time


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def find_selector(function_names, q, param_signature):
    # brute force search through the function names
    # identify which function name produces the function selector
    # with the most number of leading zeros
    min_selector = math.inf
    best_name = None
    best_selector = None
    for function_name in function_names:
        # parse out the selector (first 4 bytes of the keccak hash)
        selector = Web3.keccak(text=f'{function_name}({param_signature})').hex()[:10]

        # convert function selector to integer
        selector_int = int.from_bytes(bytes(HexBytes(selector)), 'big')

        # find the smallest function selector (most leading zeros)
        if selector_int < min_selector:
            min_selector = selector_int
            best_name = function_name
            best_selector = selector
    
    q.put({
        'name': best_name,
        'selector': best_selector,
        'int': min_selector
    })

def find(param_signature):
    # load in 10,000 common google searched words
    with open('words.txt', 'r') as f:
        words = [word.strip() for word in f.readlines()]

    # construct camelCase permutations of word pairs
    # i.e. words = [dog, cat], combos = [dogDog, catCat, dogCat, catDog]
    combos = [f'{word[0]}{word[1].capitalize()}' for word in permutations(random.sample(words, 2000), 2)]
    
    # 3 letter function names will also be considered
    alphabet = list(string.ascii_lowercase)
    triplets = [''.join(perm) for perm in permutations(alphabet, 3)]

    # construct a global list of function names to brute force through
    function_names = words + combos + triplets
    print(f"Searching through {len(function_names)} function names")

    # split the brute force search across multiple processes
    jobs = []
    q = Queue()
    for chunk in chunks(function_names, 500_000):
        p = Process(target=find_selector, args=(chunk, q, param_signature))
        p.start()
        jobs.append(p)
        time.sleep(0.1)
    
    # iterate the results to determine the best
    min_selector = math.inf
    best_name = None
    best_selector = None
    for job in jobs:
        job.join()
        result = q.get()
        if result['int'] < min_selector:
            min_selector = result['int']
            best_name = result['name']
            best_selector = result['selector']

    print(f'{best_name} ({best_selector})')

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Run as python find.py uint256,uint256")
        print("\tReplace the parameter signature as you wish. No Spaces")
        sys.exit(-1)
    find(sys.argv[1])