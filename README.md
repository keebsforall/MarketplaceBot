# Product Listing Scraper Bot

A sophisticated web scraping bot that monitors product listings, detects new items, and sends notifications through Discord. Built with Python, Docker, and modern best practices.

## Features

- Automated web scraping with configurable intervals
- Smart duplicate detection using product URLs and IDs
- Discord webhook integration for real-time notifications
- Persistent storage of listing history
- Robust error handling and logging
- Docker containerization for easy deployment
- Rate limiting and retry mechanisms
- Type-safe implementation with mypy support

## Prerequisites

- Docker and Docker Compose
- Python 3.9+ (for local development)
- Discord webhook URL

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/product-scraper-bot.git
   cd product-scraper-bot
   ```

2. Create a `.env` file with your configuration:
   ```bash
   DISCORD_WEBHOOK_URL=your_webhook_url
   WEBSITE_URL=target_website_url
   SCRAPE_INTERVAL=300  # seconds
   MIN_LISTINGS=5
   MAX_RETRIES=3
   ```

3. Start the bot using Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Local Development

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the bot locally:
   ```bash
   python src/main.py
   ```

## Project Structure


## Deploying to Hetzner VPS

### Initial Server Setup
1. Create a new server on Hetzner Cloud
   - Choose Ubuntu 22.04 LTS
   - Select your preferred server size (CX11 is sufficient)
   - Add your SSH key during creation

2. Connect to your server:
```bash
ssh root@your_server_ip
```

3. Update system and install dependencies:
```bash
apt update && apt upgrade -y
apt install -y docker.io docker-compose git
```

4. Create a non-root user (optional but recommended):
```bash
adduser botuser
usermod -aG docker botuser
su - botuser
```

### Bot Deployment
1. Clone the repository:
```bash
git clone https://github.com/yourusername/kfa-marketplace-monitor.git
cd kfa-marketplace-monitor
```

2. Create and configure your .env file:
```bash
nano .env
```
Add your environment variables:
```
DISCORD_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=your_channel_id
OPENAI_API_KEY=your_openai_api_key
```

3. Build and start the container:
```bash
docker-compose up -d
```

### Monitoring and Maintenance
1. View logs:
```bash
docker-compose logs -f
```

2. Auto-restart on server reboot:
```bash
docker update --restart=unless-stopped $(docker ps -q)
```

3. Basic monitoring:
```bash
# Check container status
docker ps

# Check system resources
docker stats

# View application logs
docker-compose logs -f --tail=100
```

### Security Recommendations
1. Configure UFW firewall:
```bash
ufw allow OpenSSH
ufw enable
```

2. Enable automatic security updates:
```bash
apt install unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

3. Set up fail2ban (optional):
```bash
apt install fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

### Backup Strategy
1. Create a backup script:
```bash
mkdir -p /home/botuser/backups
nano /home/botuser/backup.sh
```

Add to backup.sh:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/botuser/backups"
cp previous_listings.json "$BACKUP_DIR/previous_listings_$DATE.json"
find "$BACKUP_DIR" -type f -mtime +7 -delete
```

2. Make it executable and schedule with cron:
```bash
chmod +x /home/botuser/backup.sh
crontab -e
```

Add to crontab:
```
0 0 * * * /home/botuser/backup.sh
```

### Troubleshooting VPS Issues
1. If container stops unexpectedly:
```bash
# Check logs
docker-compose logs --tail=100

# Restart container
docker-compose restart

# Check system resources
htop  # install with: apt install htop
```

2. If disk space is running low:
```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -f
```

3. Monitor system memory:
```bash
free -m
```

### Updating the Bot
1. Pull latest changes:
```bash
git pull origin main

# Rebuild and restart container
docker-compose up -d --build
```

Remember to:
- Regularly check system logs for any issues
- Keep your system and Docker up to date
- Monitor disk space and memory usage
- Back up your .env file securely
- Keep track of your SSH keys
