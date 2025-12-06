import socket
import secrets
import random
from hashlib import sha256
from tcp_json import send_json
from tcp_json import receive_json
from time import sleep

HOST = "0.0.0.0"
PORT = 8080

num_dadi = 5

alice_commitment = ""
my_move = ""
alice_move = ""
alice_nonce = ""

def determine_winner(alice_move, my_move):
    final_seed = my_move + alice_move

    random.seed(final_seed)

    alice_dice = []
    for _ in range(num_dadi):
        # random.randint usa il seed impostato sopra
        dado = random.randint(1, 6) 
        alice_dice.append(dado)

    bob_dice = []
    for _ in range(num_dadi):
        dado = random.randint(1, 6)
        bob_dice.append(dado)

    sum_alice = sum(alice_dice)
    sum_bob = sum(bob_dice)

    print(f"Dice Alice: {alice_dice} (Tot: {sum_alice})")
    print(f"Dice Bob:   {bob_dice} (Tot: {sum_bob})")

    if sum_alice > sum_bob:
        print("[Bob] Alice wins...")
        return "Alice"
    elif sum_bob > sum_alice:
        print("[Bob] I win!")
        return "Bob"
    else:
        print("[Bob] It's a draw!")
        return "Draw"

def handle_game_commitment(message, conn):
    global alice_commitment
    alice_commitment = message.get("value")
    print(f"[BOB] Received Alice's commitment: {alice_commitment}")
    
    global my_move
    my_move = secrets.randbits(256)
    print(f"[BOB] My move is: {str(my_move)}")
    
    response = {
        "type": "bob-move",
        "value": my_move
    }
    send_json(conn, response)
    print(f"[BOB] Sent my move to Alice.")   
    conn.settimeout(5.0)     
    print("[BOB] Waiting 5 seconds for Alice to reveal nonce...")

def handle_reveal_nonce(message):
    global alice_nonce
    alice_nonce = message.get("value")
    print(f"[BOB] Received Alice's nonce: {alice_nonce}")

    global alice_move
    alice_move = message.get("alice-move")
    print(f"[BOB] Received Alice's move: {str(alice_move)}")
    
    check = False
    print("[BOB] Verifying Alice's commitment...")
    if alice_move is not None:
        commitment_check = sha256((str(alice_move) + alice_nonce).encode()).hexdigest()
        if commitment_check == alice_commitment:
            check = True
    
    if check:
        print(f"[BOB] Alice move: {alice_move}")
    else:
        print("[BOB] Could not determine Alice's move from the nonce!")
        return False
    
    winner = determine_winner(alice_move, my_move)
    print(f"[BOB] The winner is: {winner}")
    return False

def handle(conn):

    while True:
        try:
            print(f"[BOB] Waiting for message...")
            msg = receive_json(conn)
            
            if not msg:
                if alice_nonce == "":
                    print(f"[Bob] Alice ran away! I win by default!")
                # Client disconnected
                break
                
            match msg.get("type"):
                case "game-commitment":
                    handle_game_commitment(msg, conn)
                case "reveal-nonce":
                    handle_reveal_nonce(msg)
                case _:
                    print(f"[Bob] Unknown message type: {msg.get('type')}")

                
        except socket.timeout:
            print(f"[Bob] Timeout waiting for Alice's nonce. I win by default!")
            break


    conn.close()
    print(f"[Bob] game over. Connection closed.")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print("[BOB] Waiting for Alice to arrive...")
        sleep(2)
        conn, addr = s.accept()
        print("[BOB] Alice has arrived.")
        message = {
            "type": "game",
        }
        send_json(conn, message)
        print("[BOB] Sent game start message to Alice.")
        handle(conn)
    
if __name__ == "__main__":
    main()