import requests
from bs4 import BeautifulSoup
import sys

def decode_secret_message(url):
    # Fetch the content
    response = requests.get(url)
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the table containing the coordinates
    table = soup.find('table')
    if not table:
        print("No table found in the document")
        return
    
    # Extract rows (skip header row)
    rows = table.find_all('tr')[1:]
    
    # Create a dictionary to store characters by their coordinates
    message_grid = {}
    max_x = 0
    max_y = 0
    
    for row in rows:
        cells = row.find_all('td')
        x = int(cells[0].text.strip())
        char = cells[1].text.strip()
        y = int(cells[2].text.strip())
        
        message_grid[(x, y)] = char
        
        # Track maximum coordinates to know the grid size
        max_x = max(max_x, x)
        max_y = max(max_y, y)
    
    # Reconstruct the message by reading the grid
    secret_message = []
    for y in range(max_y + 1):
        row_chars = []
        for x in range(max_x + 1):
            row_chars.append(message_grid.get((x, y), ' '))
        secret_message.append(''.join(row_chars))
    
    # Print the message
    print("\nSecret Message:\n")
    print('\n'.join(secret_message))

if __name__ == "__main__":
    # Ensure that the URL is passed as an argument
    if len(sys.argv) != 2:
        print("Usage: python decode_secret_message.py <URL>")
        sys.exit(1)

    # Get the URL from the command line argument
    URL = sys.argv[1]
    
    # Call the function with the provided URL
    decode_secret_message(URL)

