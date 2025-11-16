# Zotify Downloader Setup Guide

This project extends zotify to automatically download music from Spotify based on what you're currently playing on your listening account.

## Architecture

- **Listening Account**: Uses Spotify Web API to monitor currently playing tracks
- **Downloading Account**: Uses zotify to download tracks from the backlog
- **Backlog**: JSON file storing tracks waiting to be downloaded
- **Cron Job**: Periodically processes the backlog

## Prerequisites

1. Ideally two Spotify accounts, they can be the same one:
   - One for listening (needs Spotify Web API access)
   - One for downloading (used by zotify)

2. Docker and Docker Compose installed

## Setup Instructions

### 1. Get Spotify Web API Credentials (Listening Account)

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your **listening account**
3. Create a new app
4. Note your **Client ID** and **Client Secret**
5. Set redirect URI to `http://localhost:8888/callback` (or any localhost URL)
6. Get a refresh token using one of these methods:
   - Use the [Authorization Code Flow](https://developer.spotify.com/documentation/web-api/tutorials/code-flow)
   - Use a tool like [spotify-refresh-token](https://github.com/tobychui/spotify-refresh-token) or similar
   - Use the Spotify Web API tutorial to get the refresh token

### 2. Configure Environment Variables

1. Create a `.env` file in the project root and fill in your credentials:
   ```env
   # Listening Account (Spotify Web API)
   LISTENING_CLIENT_ID=your_client_id_here
   LISTENING_CLIENT_SECRET=your_client_secret_here
   LISTENING_REFRESH_TOKEN=your_refresh_token_here
   
   # Downloading Account (zotify)
   DOWNLOAD_USERNAME=your_download_username
   DOWNLOAD_PASSWORD=your_download_password
   
   # Configuration
   DOWNLOAD_FOLDER=/app/downloads/Music
   BACKLOG_FILE=/app/data/backlog.json
   LISTEN_CHECK_INTERVAL=30
   DOWNLOAD_INTERVAL=900
   ```

### 3. Build and Run

```bash
# Build the Docker image
docker-compose build

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f
```

## How It Works

1. **Listener Service**: Continuously monitors your listening account's currently playing track using the Spotify Web API. It checks every `LISTEN_CHECK_INTERVAL` seconds (default: 30s). When a new track is detected, it's added to the backlog.

2. **Backlog**: A JSON file (`/app/data/backlog.json`) stores all tracks waiting to be downloaded.

3. **Download Processor**: Runs periodically based on `DOWNLOAD_INTERVAL` (default: 900 seconds / 15 minutes) to process tracks from the backlog using your downloading account. The processor runs in a separate thread and processes available tracks periodically.

4. **Downloads**: Tracks are downloaded to the configured download folder, organized by artist and album.

**Why two different intervals?**
- `LISTEN_CHECK_INTERVAL`: Controls how quickly new tracks are detected and added to backlog (frequent polling)
- `DOWNLOAD_INTERVAL`: Controls how often downloads are processed (less frequent to avoid overwhelming the system). Specified in seconds.

## Download Folder Structure

Music files are automatically organized in the following structure. This is [Jellyfin recommended structure](https://jellyfin.org/docs/general/server/media/music/):

```
Music/
├── Some Artist/
│   ├── Album A/
│   │   ├── Song 1.flac
│   │   ├── Song 2.flac
│   │   └── Song 3.flac
│   └── Album B/
│       ├── Track 1.m4a
│       ├── Track 2.m4a
│       └── Track 3.m4a
└── Album X/
    ├── Whatever You.mp3
    ├── Like To.mp3
    ├── Name Your.mp3
    └── Music Files.mp3
```

The structure follows the pattern: `{artist}/{album}/{song_name}.{ext}`

- If a track has an artist and album, it's organized as: `Artist/Album/Song.ext`
- If a track only has an album (no artist), it's organized as: `Album/Song.ext`
- The file format (ext) depends on your zotify configuration (default: ogg)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LISTENING_CLIENT_ID` | Spotify Web API Client ID | Required |
| `LISTENING_CLIENT_SECRET` | Spotify Web API Client Secret | Required |
| `LISTENING_REFRESH_TOKEN` | Spotify Web API Refresh Token | Required |
| `DOWNLOAD_USERNAME` | Spotify username for downloading | Required |
| `DOWNLOAD_PASSWORD` | Spotify password for downloading | Required |
| `DOWNLOAD_FOLDER` | Folder to save downloads (Music folder) | `/app/downloads/Music` |
| `BACKLOG_FILE` | Path to backlog JSON file | `/app/data/backlog.json` |
| `LISTEN_CHECK_INTERVAL` | Seconds between checks for new tracks (listener service polling) | `30` |
| `DOWNLOAD_INTERVAL` | Seconds between download processor runs | `900` (15 minutes) |

## Download Interval

The `DOWNLOAD_INTERVAL` is specified in seconds. `900` - Every 15 minutes is the default.

## Volumes

The Docker container uses these volumes:
- `./downloads/Music` - Downloaded music files (mapped directly to Music folder)
- `./data` - Backlog and other data files for docker container

## Troubleshooting

### Check if listener is working:
```bash
docker-compose logs | grep "New track detected"
```

### Check backlog:
```bash
cat data/backlog.json
```

### Manual backlog processing:
```bash
docker-compose exec spotify-downloader python3 -m downloader.downloader
```

## Getting a Refresh Token

To get a refresh token for the Spotify Web API, you can:

1. Use the [Authorization Code Flow tutorial](https://developer.spotify.com/documentation/web-api/tutorials/code-flow)
2. Use a Python script or tool to get the refresh token
3. Use online tools (be careful with credentials)

The refresh token allows the app to access the Spotify Web API without user interaction.

## Notes

- The listening account needs to have Spotify Web API access enabled
- The downloading account is used by zotify and should ideally be a separate account
- Downloads are stored in the `downloads/Music` folder, organized by artist and album
- The backlog prevents duplicate downloads in the backlog. Zotify prevents downloading the same song twice using the argument `skip_existing=True`.
- Failed downloads remain in the backlog for retry

