# MagnetBank

## Features

### DONE

- Added the ability to add magnet links
- Implemented signing of Custom JSON via Keychain
- Enabled conversion of torrent files to magnet links
- Implemented duplicate check on node complete
- Added basic search functionality
- Added category selection to determine where the magnet link is stored on the blockchain
- Developed protocol for JSON storage
- Added all public trackers that support DHT to the generation of the magnet link on click
- Completed backend development

### TODO

- MVP

## Implementation Details

- Only one announce URL is saved from the magnet to save space on the blockchain request
- If no announce URL is available, a random one is selected from a list of public trackers that support DHT
  - This is an edge case where 'None' is passed from a torrent conversion, e.g. Archlinux torrent
- Only the hash of the magnet link is required for the system to function
  - If DHT and local peer discovery are turned on in the torrent client, it will eventually download the file if there are enough people nearby

## Important Notes

- This project is still in development and should not be used for production purposes
- The blockchain used for storage is currently Hive, but other blockchains may be added in the future
- The search function is currently basic and may not return accurate results
- Category selection is important as it determines where the magnet link is stored on the blockchain
- The system relies on the availability of public trackers that support DHT and may not work for private torrents or in regions where public trackers are blocked

## Getting Started

To use MagnetBank, follow these steps:

1. Clone the repository to your local machine
2. Install the necessary dependencies by running `pip install -r requirements.txt`
3. Start the server by running `python app.py`
4. Open your web browser and navigate to `http://localhost:5000`

## Usage

To add a magnet link, simply paste the link into the input field and click the "Add Magnet" button. The system will automatically convert the magnet link to a torrent file and store it on the blockchain.

To search for a magnet link, enter a search term into the search bar and click the "Search" button. The system will return a list of magnet links that match the search term.

To select a category for your magnet link, use the dropdown menu to choose a category before adding the magnet link.

## Contributing

If you would like to contribute to MagnetBank, please fork the repository and submit a pull request with your changes. We welcome all contributions, big or small!

## License

MagnetBank is licensed under the MIT License. See LICENSE for more information.
