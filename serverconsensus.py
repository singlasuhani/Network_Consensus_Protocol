import socket
import threading
import random
import string

# Server details
SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 12345
# riddle details (for compatability w/ other groups?)
riddle = "What has keys but can't open locks?"
correct_answer = "keyboard"

# Function to generate a random 3-digit PIN for each client
def generate_pin():
    return ''.join(random.choices(string.digits, k=3))

# Function to broadcast consensus to authenticated clients
def broadcast_consensus(authenticated_clients, consensus):
    for client in authenticated_clients:             # Loop through each client in 'authenticated client' list
        try:
            client.send(f"Consensus reached: '{consensus}'.\n\n<<'setup' to declare node info\n<<'discover' to discover nodes\n<<'negotiate' to negotiate with server (store node info)\n<<'receive' to recieve stored node info from server\n<<'vote' to enter voting consensus\n<<'stats' to view current consensus statistics\n<<'exit' to exit consensus protocol\n [Select an option]".encode('utf-8'))     # Send consensus message to clients
        except Exception as e:
            print(f"Error broadcasting consensus: {e}")                             # Only sent if there's an error while broadcasting consensus
def check_for_majority(votes, authenticated_clients):
    if not votes:  # No votes to check
        return None

    # Find the vote counts
    vote_counts = {vote: votes.count(vote) for vote in set(votes)}
    sorted_votes = sorted(vote_counts.items(), key=lambda item: item[1], reverse=True)

    # Check for majority and handle tie situation
    if len(sorted_votes) > 1 and sorted_votes[0][1] == sorted_votes[1][1]:
        print("There is a tie, no consensus.")
        return None  # No consensus due to tie
    else:
        consensus = sorted_votes[0][0]
        vote_count = sorted_votes[0][1]
        if vote_count > len(authenticated_clients) / 2:
            print(f"Majority consensus is '{consensus}' with {vote_count} votes.")
            return consensus  # A consensus has been reached
    return None  # No consensus


def calculate_vote_stats(votes):
    total_votes = len(votes)
    vote_stats = {}

    for vote in set(votes):
        frequency = votes.count(vote)
        percentage = (frequency / total_votes) * 100
        vote_stats[vote] = percentage

    return vote_stats

# Function to handle individual client connections
def handle_client(client_socket, address, votes, connected_clients, authenticated_clients, vote_lock, client_info, negotiation_info):
    try:
        client_socket.send(f"RIDDLE: {riddle}\n-------Your answer-------\n".encode('utf-8'))           # Send the riddle to the client socket
        answer = client_socket.recv(1024).decode('utf-8').lower().strip()   # Receive the answer from the client socket

        if answer == correct_answer:                                            # If the answer is correct{
            authenticated_clients.add(client_socket)                            # Add the client socket to authenticated clients list
            pin = generate_pin()                                                # Generate a PIN for the client
            client_info[pin] = {'client_socket': client_socket, 'info': None}   # Store client identification (IP, Port) and tie to their respective generated PIN
            # Send confirmation and PIN to the client socket}
            client_socket.send(f"Correct! You may now vote and request for node discovery and negotiation.\nYour PIN is: {pin}\n<<'setup' to declare node info\n<<'discover' to discover nodes\n<<'negotiate' to negotiate with server (store node info)\n<<'receive' to recieve stored node info from server\n<<'vote' to enter voting consensus\n<<'stats' to view current consensus statistics\n<<'exit' to exit consensus protocol\n [Select an option]".encode('utf-8'))

        else:
            client_socket.send("Incorrect answer. You cannot participate in voting, discovery, or negotiation.\n".encode('utf-8'))     # Send incorrect answer message to client and return
            return

        while True:                                                             # Infinite loop to handle client requests              
            request = client_socket.recv(1024).decode('utf-8').strip()          # Receive request from client socket
            if request.lower() == 'discover':                                   # If request is for node discovery("({
                with vote_lock:                                                 # Send information on all active nodes (IP, Port, Pin) to client}
                    active_nodes = '\n'.join([f"Client {i+1} - {info['client_socket'].getpeername()} ]|[ PIN: {pin}" for i, (pin, info) in enumerate(client_info.items())])
                    client_socket.send(f"Active nodes:\n{active_nodes}\n\n<<'setup' to declare node info\n<<'discover' to discover nodes\n<<'negotiate' to negotiate with server (store node info)\n<<'receive' to recieve stored node info from server\n<<'vote' to enter voting consensus\n<<'stats' to view current consensus statistics\n<<'exit' to exit consensus protocol\n [Select an option]".encode('utf-8'))
     
            elif request.lower().startswith('negotiate'):   # Else if request is for negotiation[
                pin = [pin for pin, value in client_info.items() if value['client_socket'] == client_socket][0]
                if client_info[pin]['info'] is None:        # Check if client info is None
                    client_socket.send("Please set up your node info before negotiating. Use 'setup' action.\n".encode('utf-8'))
                else:
                    negotiation_details = request[10:].strip()  # Extract negotiation details from request
                    with vote_lock:                              # Update client information with negotiation details
                        pin = [pin for pin, value in client_info.items() if value['client_socket'] == client_socket][0]
                        client_info[pin]['info'] = node_info
                        all_negotiations = '; '.join([f"{pin}: {info['info']}" for pin, info in client_info.items()])   # Compile all negotiation details
                        client_socket.send(f"\nNegotiation info collected: {all_negotiations}\n[Press Enter to Continue]".encode('utf-8'))         # Send confirmation of negotiation info collection
                    
                    # Commence the Negotiation process
                    print(f"Requesting node information from {address} with PIN '{pin}'...")
                    while True: 
                        # Keep asking until a valid response is received
                       print(f"Obtaining node information from {address} with PIN '{pin}'...")
                       client_socket.send("\nServer requesting node information\n[Accept?(Y/N)]".encode('utf-8'))
                       raw_response = client_socket.recv(1024).decode('utf-8')
                       permission_response = raw_response.strip().upper()  # Normalize the response

                       if permission_response.upper() == 'Y':   # If client grants permission
                               print(f"Information received from {address} with PIN '{pin}'")   # Permission granted, acknowledge in output and proceed}
                               client_socket.send("Permission Granted\n\n<<'setup' to declare node info\n<<'discover' to discover nodes\n<<'negotiate' to negotiate with server (store node info)\n<<'receive' to recieve stored node info from server\n<<'vote' to enter voting consensus\n<<'stats' to view current consensus statistics\n<<'exit' to exit consensus protocol\n [Select an option]".encode('utf-8'))
                               break  # Break the loop as we've received a valid response
                       elif permission_response.upper() == 'N':  # If client denies permission
                               print(f"Failed to receive information from {address}")           # Permission denied, acknowledge in output and handle}]
                               client_socket.send("Permission Denied\n\n<<'setup' to declare node info\n<<'discover' to discover nodes\n<<'negotiate' to negotiate with server (store node info)\n<<'receive' to recieve stored node info from server\n<<'vote' to enter voting consensus\n<<'stats' to view current consensus statistics\n<<'exit' to exit consensus protocol\n [Select an option]".encode('utf-8'))
                               break  # Break the loop as we've received a valid response
                       else:
                               client_socket.send("\nInvalid response. Please reply with 'Y' for Yes or 'N' for No.\n[Press Enter to Continue]".encode('utf-8'))

            elif request.lower() == 'receive':              # Else if request is for receiving node information[
                with vote_lock:                             # Handle request to receive node information
                    client_socket.send(f"\n[Enter PIN to receive node information of a specific client, or 'all' for all clients]".encode('utf-8'))
                    pin_request = client_socket.recv(1024).decode('utf-8').strip()  # Receive PIN request from client input
                    if pin_request.lower() == 'all':     # If client inputs 'all' instead of PIN{
                        all_nodes_info = '\n'.join([f"PIN: {pin}, Info: {info['info']}" for pin, info in client_info.items()])      # Send information of all nodes to client}
                        client_socket.send(f"All Nodes Information:\n{all_nodes_info}\n\n<<'setup' to declare node info\n<<'discover' to discover nodes\n<<'negotiate' to negotiate with server (store node info)\n<<'receive' to recieve stored node info from server\n<<'vote' to enter voting consensus\n<<'stats' to view current consensus statistics\n<<'exit' to exit consensus protocol\n [Select an option]".encode('utf-8'))
                    elif pin_request in client_info:                    # Else if specific node information is requested (PIN given){
                        node_info = client_info[pin_request]['info']    # Send information of requested node to client}
                        client_socket.send(f"Node Information for PIN {pin_request}:\n{node_info}\n\n<<'setup' to declare node info\n<<'discover' to discover nodes\n<<'negotiate' to negotiate with server (store node info)\n<<'receive' to recieve stored node info from server\n<<'vote' to enter voting consensus\n<<'stats' to view current consensus statistics\n<<'exit' to exit consensus protocol\n [Select an option]".encode('utf-8'))
                    else:
                        client_socket.send("Invalid PIN. Please try again.\n".encode('utf-8'))      # Otherwise send message for invalid PIN]

            elif request.lower() == 'setup':                                    # If request is for node setup
                pin = [pin for pin, value in client_info.items() if value['client_socket'] == client_socket][0]
                if client_info[pin]['info'] is None:                             # Check if client info is None
                    client_socket.send("Enter Services:".encode('utf-8'))        # Prompt client to enter services
                    services = client_socket.recv(1024).decode('utf-8').strip() # Receive services from client
                    client_socket.send("Enter Capabilities:".encode('utf-8'))    # Prompt client to enter capabilities
                    capabilities = client_socket.recv(1024).decode('utf-8').strip() # Receive capabilities from client
                    client_socket.send("Enter Constraints:".encode('utf-8'))     # Prompt client to enter constraints
                    constraints = client_socket.recv(1024).decode('utf-8').strip() # Receive constraints from client
                    node_info = f"Services: {services}; Capabilities: {capabilities}; Constraints: {constraints}"  # Combine all information
                    client_info[pin]['info'] = node_info                         # Store node info
                    client_socket.send("Node info set up successfully. You can now proceed with negotiation.\n\n<<'setup' to declare node info\n<<'discover' to discover nodes\n<<'negotiate' to negotiate with server (store node info)\n<<'receive' to recieve stored node info from server\n<<'vote' to enter voting consensus\n<<'stats' to view current consensus statistics\n<<'exit' to exit consensus protocol\n [Select an option]".encode('utf-8'))
                else:
                    client_socket.send("Node info already set up. You can proceed with negotiation.\n\n<<'discover' to discover nodes\n<<'negotiate' to negotiate with server (store node info)\n<<'receive' to recieve stored node info from server\n<<'vote' to enter voting consensus\n<<'stats' to view current consensus statistics\n<<'exit' to exit consensus protocol\n [Select an option]".encode('utf-8'))

            elif request.lower() == 'stats':  # Calculate voting statistics
                with vote_lock:
                    if votes:
                        vote_count = len(votes)
                        unique_votes = set(votes)
                        stats_msg = "Voting Statistics:\n"
                        for vote in unique_votes:
                            vote_percent = (votes.count(vote) / vote_count) * 100
                            stats_msg += f"{vote}: {vote_percent:.2f}%\n"
                        client_socket.send(stats_msg.encode('utf-8'))
                        client_socket.send("\n<<'setup' to declare node info\n<<'discover' to discover nodes\n<<'negotiate' to negotiate with server (store node info)\n<<'receive' to recieve stored node info from server\n<<'vote' to enter voting consensus\n<<'stats' to view current consensus statistics\n<<'exit' to exit consensus protocol\n [Select an option]".encode('utf-8'))
                    else:
                        client_socket.send("Invalid selection.\n\n<<'setup' to declare node info\n<<'discover' to discover nodes\n<<'vote' to enter voting consensus\n<<'negotiate' to negotiate with server (store node info)\n<<'receive' to recieve stored node info from server\n<<'stats' to get voting statistics\n<<'exit' to exit consensus protocol\n [Select an option]".encode('utf-8'))

            elif request.lower() == 'exit':     # Else if request is to exit{
                break                           # Break out of the loop to terminate client handling function})")
                            
                
            elif request.lower() == 'vote':  # This is the modified block for voting
              client_socket.send("\n###Would you rather (A) always be 10 minutes late or (B) always be 20 minutes early?###\n[Enter your vote(A/B)]".encode('utf-8'))
              vote = client_socket.recv(1024).decode('utf-8').strip()
              with vote_lock:
                   print(f"Vote '{vote}' received from {address}")
                   votes.append(vote)
                   consensus = check_for_majority(votes, authenticated_clients)
                   if consensus:   # If consensus is reached
                    print(f"The current consensus with a majority is: '{consensus}'")
                    broadcast_consensus(authenticated_clients, consensus)
                   else:  # No consensus yet
                    client_socket.send(f"Your vote for '{vote}' has been counted. No consensus yet.\n\n<<'setup' to declare node info\n<<'discover' to discover nodes\n<<'negotiate' to negotiate with server (store node info)\n<<'receive' to recieve stored node info from server\n<<'vote' to enter voting consensus\n<<'stats' to view current consensus statistics\n<<'exit' to exit consensus protocol\n [Select an option]".encode('utf-8'))

            else:
                client_socket.send("Invalid selection.\n\n<<'setup' to declare node info\n<<'discover' to discover nodes\n<<'negotiate' to negotiate with server (store node info)\n<<'receive' to recieve stored node info from server\n<<'vote' to enter voting consensus\n<<'stats' to view current consensus statistics\n<<'exit' to exit consensus protocol\n [Select an option]".encode('utf-8'))

    except Exception as e:
        print(f"Error handling client {address}: {e}")  # Print error message if exception occurs while handling client
    # Memory clean-up operations
    finally:
        with vote_lock:
            if pin in client_info:      # If client information (identified with PIN) is present in the server{
                del client_info[pin]    # Delete its memory}
            if client_socket in authenticated_clients:      # If client present in authenticated client list{
                authenticated_clients.remove(client_socket) # Remove client from list} 
        connected_clients.remove(client_socket)     # Remove client from connected clients
        client_socket.close()                       # Close socket

# Function to start the server
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       # Create a server socket
    server_socket.bind((SERVER_ADDRESS, SERVER_PORT))                       # Bind the socket to the server address and port
    server_socket.listen(5)                                                 # Start listening for incoming connections
    print(f"Consensus server listening on {SERVER_ADDRESS}:{SERVER_PORT}")  # Print server information

    votes = []                      # List to store votes
    connected_clients = []          # List to store connected clients
    authenticated_clients = set()   # Set to store authenticated clients
    vote_lock = threading.Lock()    # Lock for thread safety in voting
    client_info = {}                # Dictionary to store client information
    negotiation_info = {}           # Dictionary to store negotiation information

    try:
        while True:     # Infinite loop to accept incoming connections
            client_socket, client_address = server_socket.accept()      # Accept incoming connection
            connected_clients.append(client_socket)                     # Add client socket to connected clients list
            print(f"Accepted connection from {client_address}")         # Print accepted connection information
            client_handler = threading.Thread(                          # Create a new thread for handling client
                target=handle_client,
                args=(client_socket, client_address, votes, connected_clients, authenticated_clients, vote_lock, client_info, negotiation_info)
            )
            client_handler.start()                                      # Start the client handling thread

    except OSError as e:
        print(f"Server exception: {e}")     # Print server exception error for if a server is already set up
    finally:
        server_socket.close()               # Close server

if __name__ == "__main__":      # If the script is being run directly(no other servers)
    start_server()              # Start the server