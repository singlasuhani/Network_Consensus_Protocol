import socket  # socket library provides the necessary functions and structures for network communications.
import time  # time library uses the sleep function, allowing the program to pause execution for a specified duration.

# Function to handle each client after they connect to the server
def interact_with_server(client_socket):
    try:
        # Receive a riddle from the server and decode it from bytes to a string using UTF-8 encoding.
        riddle = client_socket.recv(1024).decode('utf-8')
        print(riddle)  # Prints the riddle received from the server.

        # Prompt the user to enter an answer for the riddle and send this answer back to the server encoded as bytes using UTF-8.
        answer = input("Your answer: ").strip()
        client_socket.sendall(answer.encode('utf-8'))

        # Receive the server's response to the submitted answer, decode it, and print it.
        verification_result = client_socket.recv(1024).decode('utf-8')
        print(verification_result)

        while True:
            # Continuously prompt the user for an action until 'exit' is entered.
            action = input(">>").lower().strip()
            client_socket.sendall(action.encode('utf-8'))  # Send the action to the server encoded as bytes.

            if action == 'exit':
                break  # Break the loop and end interaction if the action is 'exit'.

            # Await the server's response to the action, decode it, and print it.
            response = client_socket.recv(1024).decode('utf-8')
            print(response)

    except Exception as e:
        print(f"An error occurred: {e}")  # Print any exceptions that occur during the interaction.
    finally:
        client_socket.close()  # Ensure the socket is closed to free up resources.

def start_client():
    try:
        # Prompt the user for the server's address and port number to connect to.
        server_address = input("Enter server address (e.g., '127.0.0.1'): ")
        server_port = int(input("Enter server port (e.g., 8080): "))

        # Create a new socket using IPv4 addressing and TCP, and connect to the server using the provided address and port.
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_address, server_port))

        # Pass the connected socket to the function that handles interaction with the server.
        interact_with_server(client_socket)

    except Exception as e:
        print(f"Error connecting to server: {e}")  # Print any errors that occur while attempting to connect to the server.
        print("Retrying in 5 seconds...")
        time.sleep(5)  # Wait for 5 seconds before attempting to reconnect.

if __name__ == "__main__":
    start_client()  # Entry point of the script. If the script is run directly, start the client.
