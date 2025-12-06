import secrets
import socket
import random
from hashlib import sha256

from time import sleep
from tcp_json import send_json
from tcp_json import receive_json

HOST = 'bob'
PORT = 8080

num_dices = 5
num_alice_wins = 0
num_bob_wins = 0
count_games = 0

my_move = ""
my_nonce = ""
bob_move = ""

def determine_winner(my_move, bob_move):
    final_seed = my_move + bob_move

    random.seed(final_seed)

    alice_dice = []
    for _ in range(num_dices):
        dado = random.randint(1, 6) 
        alice_dice.append(dado)

    bob_dice = []
    for _ in range(num_dices):
        dado = random.randint(1, 6)
        bob_dice.append(dado)

    sum_alice = sum(alice_dice)
    sum_bob = sum(bob_dice)

    print(f"Dice Alice: {alice_dice} (Tot: {sum_alice})")
    print(f"Dice Bob:   {bob_dice} (Tot: {sum_bob})")

    global num_alice_wins, num_bob_wins, count_games
    count_games += 1

    if sum_alice > sum_bob:
        print("[Alice] I win!")
        num_alice_wins += 1
        return "Alice"
    elif sum_bob > sum_alice:
        print("[Alice] Bob wins...")
        num_bob_wins += 1
        return "Bob"
    else:
        print("[Alice] It's a draw!")
        return "Draw"

def handle_bob_move(message, conn):
    global bob_move
    bob_move = message.get("value")
    print(f"[Alice] Received Bob's move: {str(bob_move)}")
    
    winner = determine_winner(my_move, bob_move)
    print(f"[Alice] The winner is: {winner}")
    if winner == "Bob":
        print("[Alice] Should I send the nonce to Bob? I can escape...(yes/no)")
        choice = input().strip().lower()
        if choice == "yes":
            #print(F"[alice][DEBUG] my_move: {my_move} my_nonce: {my_nonce}.")
            response = {
                "type": "reveal-nonce",
                "value": my_nonce,
                "alice-move": my_move
            }
            send_json(conn, response)
            print("[alice] Sent nonce to Bob.")
        else:
            print("[alice] I chose not to send the nonce to Bob. I have to run!")
    else:
        response = {
            "type": "reveal-nonce",
            "value": my_nonce,
            "alice-move": my_move
        }
        send_json(conn, response)
        print("[alice] Sent nonce to Bob.")
    return True
    

def game(message, conn):
    global my_move, my_nonce
    my_move = secrets.randbits(256)
    my_nonce = secrets.token_hex(16)
    commitment = sha256((str(my_move) + my_nonce).encode()).hexdigest()
    message = {
        "type" : "game-commitment",
        "value" : commitment
    }
    
    send_json(conn, message)
    print(f"[Alice] Sent my move ({str(my_move)}) without nonce ({my_nonce}), I want to be sure that Bob cannot cheat")
    return True
    

def handle(message, conn):
    msg_type = message.get("type")
    match msg_type:
        case "game":
            return game(message, conn)
        case "bob-move":
            return handle_bob_move(message, conn)
            

def main():

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
        print("[Alice] I'm going to meet Bob...")
        sleep(2)
        conn.connect((HOST, PORT))
        conn.settimeout(5.0)
        print("[Alice] Arrived to Bob.")

        while True and count_games < 5:
            print("[Alice] Waiting for message...")
            if count_games > 0:
                game({}, conn)
            
            message = receive_json(conn)
            if not message:
                print("[Alice] No message received, closing connection")
                break
            #print(f"message received : {message}")
            if handle(message, conn) == False:
                break
        conn.close()
        print("[Alice] game over, connection closed.")
    print(f"[Alice] Total Alice wins: {num_alice_wins}, Total Bob wins: {num_bob_wins}, Total games played: {count_games}")
    

if __name__ == "__main__":
    main()