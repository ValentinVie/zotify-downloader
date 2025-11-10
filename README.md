# Zotify Downloader

An automated music downloader that monitors your Spotify listening activity and automatically downloads tracks you're currently playing.

## Overview

This project extends [zotify](https://github.com/zotify-dev/zotify) to create an automated music download system. It uses two Spotify accounts:

- **Listening Account**: Monitors what you're currently playing using the Spotify Web API
- **Downloading Account**: Downloads tracks from the backlog using zotify

When you play a track on your listening account, it's automatically added to a backlog and downloaded by the downloading account.

## Features

- 🎵 **Automatic Detection**: Monitors your Spotify listening activity in real-time
- 📋 **Backlog System**: Queues tracks for download, preventing duplicates
- 🐳 **Docker Support**: Easy deployment with Docker and Docker Compose
- 📁 **Organized Storage**: Downloads organized in Jellyfin-compatible folder structure (`Artist/Album/Song.ext`)
- ⚙️ **Configurable**: Adjustable intervals for listening checks and download processing
- 🔄 **Deduplication**: Prevents duplicate downloads both in backlog and on disk

## Architecture

- **Spotify Listener**: Uses Spotify Web API to monitor currently playing tracks
- **Backlog Manager**: JSON-based queue system for tracks waiting to be downloaded
- **Download Processor**: Processes backlog using zotify with configurable intervals
- **Docker Container**: Runs both services concurrently in separate threads

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Two Spotify accounts (can be the same account)
- Spotify Web API credentials for the listening account

### Setup

1. **Get Spotify Web API Credentials**
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app and get Client ID, Client Secret, and Refresh Token

2. **Configure Environment Variables**
   - Create a `.env` file in the project root
   - See [SETUP.md](SETUP.md) for detailed configuration instructions

3. **Build and Run**
   ```bash
   docker-compose build
   docker-compose up -d
   docker-compose logs -f
   ```

For detailed setup instructions, see [SETUP.md](SETUP.md).

## How It Works

1. **Listener Service**: Continuously polls the Spotify Web API (every 30 seconds by default) to detect new tracks you're playing
2. **Backlog**: New tracks are added to a JSON backlog file, with duplicate prevention
3. **Download Processor**: Periodically processes the backlog (every 15 minutes by default) and downloads tracks using zotify
4. **File Organization**: Downloads are saved in `Artist/Album/Song.ext` format, compatible with Jellyfin

## Download Folder Structure

Music files are organized in the [Jellyfin recommended structure](https://jellyfin.org/docs/general/server/media/music/):

```
Music/
├── Some Artist/
│   ├── Album A/
│   │   ├── Song 1.flac
│   │   └── Song 2.flac
│   └── Album B/
│       └── Track 1.m4a
└── Album X/
    └── Whatever You.mp3
```

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LISTENING_CLIENT_ID` | Spotify Web API Client ID | Required |
| `LISTENING_CLIENT_SECRET` | Spotify Web API Client Secret | Required |
| `LISTENING_REFRESH_TOKEN` | Spotify Web API Refresh Token | Required |
| `DOWNLOAD_USERNAME` | Spotify username for downloading | Required |
| `DOWNLOAD_PASSWORD` | Spotify password for downloading | Required |
| `DOWNLOAD_FOLDER` | Folder to save downloads | `/app/downloads/Music` |
| `LISTEN_CHECK_INTERVAL` | Seconds between listening checks | `30` |
| `DOWNLOAD_INTERVAL` | Seconds between download runs | `900` (15 min) |

See [SETUP.md](SETUP.md) for complete configuration details.

## Docker Usage

```bash
# Build the image
docker-compose build

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

## Troubleshooting

- **Check if listener is working**: `docker-compose logs | grep "New track detected"`
- **Check backlog**: `cat data/backlog.json`
- **View all logs**: `docker-compose logs -f`

For more troubleshooting tips, see [SETUP.md](SETUP.md).

## Notes

- The backlog prevents duplicate entries by track ID
- Zotify prevents duplicate downloads using `skip_existing=True`
- Failed downloads remain in the backlog for retry
- Downloads are organized in Jellyfin-compatible structure

## Disclaimer

This project is intended for educational, private and fair use. Users are responsible for compliance with applicable laws and terms of service.

## Contributing

Please refer to [CONTRIBUTING](CONTRIBUTING.md)

## License

See [LICENSE](LICENSE)
