import hmac
import hashlib
import binascii
import math
from PyV8 import JSContext
from collections import deque


class History:
    def __init__(self, size=50):
        self.buffer = deque(maxlen=size)

    def first(self):
        return self.buffer[0] if self.buffer else None

    def last(self):
        return self.buffer[-1] if self.buffer else None

    def toArray(self):
        return list(self.buffer)

    def size(self):
        return len(self.buffer)


class UserInfo:
    def __init__(self, uname, balance):
        self.uname = uname
        self.balance = balance


class Engine:
    def __init__(self):
        self.subscribers = {}
        self.history = History()
        self.current_bet = None
        self.current_payout = None

    def on(self, event_name, callback):
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)

    def off(self, event_name, callback):
        if event_name in self.subscribers:
            self.subscribers[event_name].remove(callback)

    def once(self, event_name, callback):
        def wrapper(*args, **kwargs):
            self.off(event_name, wrapper)
            return callback(*args, **kwargs)

        self.on(event_name, wrapper)

    def emit(self, event_name, *args, **kwargs):
        if event_name in self.subscribers:
            for callback in self.subscribers[event_name]:
                callback(*args, **kwargs)

    def bet(self, wager, payout):
        if self.current_bet is not None:
            raise Exception("Bet already placed for this game")
        self.current_bet = wager
        self.current_payout = payout
        userInfo.balance -= wager

def generate_games(hash_value, num_games):
    salt = '0000000000000000004d6ec16dafe9d8370958664c1dc422f452892264c59526'.encode()
    hashobj = hmac.new(salt, binascii.unhexlify(hash_value), hashlib.sha256)

    game_results = []
    for i in range(num_games):
        number = 0
        intversion = int(hashobj.hexdigest()[0:int(52/4)], 16)
        number = max(1, math.floor(100 / (1 - (intversion / (2 ** 52)))) / 101)
        game_results.append({'hash': hash_value, 'result': number})
        hash_value = hashlib.sha256(hash_value.encode()).hexdigest()
        hashobj = hmac.new(salt, binascii.unhexlify(hash_value), hashlib.sha256)

    return game_results

def gameResultFromHash(self, hash_value):
    return generate_games(hash_value, 1)[0]['result']

with JSContext() as ctxt:
    user_info = UserInfo("player1", 1000)  # Example user info
    engine = Engine()

    ctxt.locals.userInfo = user_info
    ctxt.locals.engine = engine
    ctxt.exposeFunction("gameResultFromHash", gameResultFromHash)

    # Simulating game flow
    hash_value = "some_hash_value"  # Example hash value
    results = generate_games(hash_value, 50)

    for result in results:
        hash_value, number = result['hash'], result['result']

        # GAME_STARTING event
        engine.emit('GAME_STARTING')
        # GAME_STARTED event
        engine.emit('GAME_STARTED')
        # Check if player won
        if engine.current_bet and engine.current_payout <= number:
            user_info.balance += engine.current_bet * engine.current_payout

        # Add to history
        engine.history.buffer.append(result)
        # GAME_ENDED event
        engine.emit('GAME_ENDED')

        # Reset for next game
        engine.current_bet = None
        engine.current_payout = None

