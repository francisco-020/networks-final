import socket
import time
import random
import threading
from datetime import datetime

HOST = "0.0.0.0"
PORT = 5050
WINNING_SCORE = 3

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = []
player_names = []
scores = [0, 0]
reaction_times = [[], []]

winner = None
false_starter = None
start_time = 0
winner_reaction_time = 0
lock = threading.Lock()


def log(message):
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"[{current_time}] {message}")


def calculate_average(times):
    if len(times) == 0:
        return None
    return sum(times) / len(times)


def listen_for_early_click(player_index, client_socket):
    global false_starter

    try:
        client_socket.settimeout(0.1)
        message = client_socket.recv(1024).decode()

        if message == "EARLY":
            with lock:
                if false_starter is None:
                    false_starter = player_index

    except socket.timeout:
        pass

    except ConnectionResetError:
        log(f"{player_names[player_index]} disconnected unexpectedly.")

    finally:
        client_socket.settimeout(None)


def listen_for_response(player_index, client_socket):
    global winner, winner_reaction_time

    try:
        message = client_socket.recv(1024).decode()

        if message == "PRESSED":
            reaction_time = time.perf_counter() - start_time

            with lock:
                if winner is None:
                    winner = player_index
                    winner_reaction_time = reaction_time

    except ConnectionResetError:
        log(f"{player_names[player_index]} disconnected unexpectedly.")


log("Server is running...")
log(f"Waiting for 2 clients on port {PORT}...")

while len(clients) < 2:
    client_socket, client_address = server.accept()
    clients.append(client_socket)

    player_name = client_socket.recv(1024).decode()
    player_names.append(player_name)

    log(f"{player_name} connected from {client_address}")
    client_socket.send(f"Welcome, {player_name}! You are Player {len(clients)}".encode())

log("Both players connected!")
log(f"Players: {player_names[0]} vs {player_names[1]}")

input("Press Enter to start the game...")
log("Game started by server host.")

round_number = 1

while max(scores) < WINNING_SCORE:
    winner = None
    false_starter = None
    winner_reaction_time = 0

    log(f"Starting Round {round_number}")

    for client in clients:
        client.send(f"Round {round_number} starting soon...".encode())

    time.sleep(2)

    for client in clients:
        client.send("Get ready...".encode())

    wait_time = random.randint(2, 5)
    early_threads = []
    early_check_start = time.perf_counter()

    while time.perf_counter() - early_check_start < wait_time:
        for i, client in enumerate(clients):
            thread = threading.Thread(target=listen_for_early_click, args=(i, client))
            early_threads.append(thread)
            thread.start()

        for thread in early_threads:
            thread.join()

        if false_starter is not None:
            break

        early_threads.clear()

    if false_starter is not None:
        other_player = 1 - false_starter
        scores[other_player] += 1

        log(f"False start by {player_names[false_starter]}")
        log(f"Round {round_number} winner: {player_names[other_player]}")
        log(f"Score: {player_names[0]} {scores[0]} - {player_names[1]} {scores[1]}")

        clients[false_starter].send(
            f"False start! You clicked before GO. {player_names[other_player]} wins Round {round_number}.".encode()
        )

        clients[other_player].send(
            f"{player_names[false_starter]} false-started. You win Round {round_number}!".encode()
        )

        score_message = f"Score: {player_names[0]} {scores[0]} - {player_names[1]} {scores[1]}"

        for client in clients:
            client.send(score_message.encode())

        round_number += 1
        time.sleep(2)
        continue

    start_time = time.perf_counter()

    for client in clients:
        client.send("GO!".encode())

    threads = []

    for i, client in enumerate(clients):
        thread = threading.Thread(target=listen_for_response, args=(i, client))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    scores[winner] += 1
    reaction_times[winner].append(winner_reaction_time)

    log(f"Round {round_number} winner: {player_names[winner]}")
    log(f"Reaction time: {winner_reaction_time:.3f} seconds")
    log(f"Score: {player_names[0]} {scores[0]} - {player_names[1]} {scores[1]}")

    for i, client in enumerate(clients):
        if i == winner:
            client.send(
                f"You won Round {round_number}! Reaction time: {winner_reaction_time:.3f} seconds".encode()
            )
        else:
            client.send(
                f"You lost Round {round_number}. Winner reaction time: {winner_reaction_time:.3f} seconds".encode()
            )

    score_message = f"Score: {player_names[0]} {scores[0]} - {player_names[1]} {scores[1]}"

    for client in clients:
        client.send(score_message.encode())

    round_number += 1
    time.sleep(2)

final_winner = scores.index(max(scores))

avg_player_1 = calculate_average(reaction_times[0])
avg_player_2 = calculate_average(reaction_times[1])

for client in clients:
    client.send(f"Game over! Final winner: {player_names[final_winner]}".encode())

if avg_player_1 is not None:
    player_1_stats = f"{player_names[0]} average winning reaction time: {avg_player_1:.3f} seconds"
else:
    player_1_stats = f"{player_names[0]} had no valid winning reaction times."

if avg_player_2 is not None:
    player_2_stats = f"{player_names[1]} average winning reaction time: {avg_player_2:.3f} seconds"
else:
    player_2_stats = f"{player_names[1]} had no valid winning reaction times."

for client in clients:
    client.send(player_1_stats.encode())
    client.send(player_2_stats.encode())

log(f"Game over! Final winner: {player_names[final_winner]}")
log(player_1_stats)
log(player_2_stats)

for client in clients:
    client.close()

server.close()