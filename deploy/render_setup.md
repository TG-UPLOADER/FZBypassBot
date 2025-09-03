# Render Deployment Guide

## Quick Deploy to Render

1. **Fork the Repository**
   - Fork this repository to your GitHub account

2. **Create Render Account**
   - Sign up at [render.com](https://render.com)
   - Connect your GitHub account

3. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Select your forked repository
   - Choose the following settings:

## Render Configuration

### Basic Settings
- **Name:** `fzbypass-bot` (or your preferred name)
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `bash start.sh`

### Environment Variables
Add all the following environment variables in Render dashboard:

#### Required Variables
```
BOT_TOKEN=your_bot_token_here
API_ID=your_api_id_here
API_HASH=your_api_hash_here
AUTH_CHATS=chat_id1 chat_id2:topic_id
```

#### Optional Variables
```
AUTO_BYPASS=False
OWNER_ID=your_telegram_user_id
LARAVEL_SESSION=your_laravel_session
XSRF_TOKEN=your_xsrf_token
GDTOT_CRYPT=your_gdtot_crypt
HUBDRIVE_CRYPT=your_hubdrive_crypt
DRIVEFIRE_CRYPT=your_drivefire_crypt
KATDRIVE_CRYPT=your_katdrive_crypt
DIRECT_INDEX=your_direct_index_url
TERA_COOKIE=your_terabox_cookie
UPSTREAM_REPO=https://github.com/SilentDemonSD/FZBypassBot
UPSTREAM_BRANCH=main
```

## Features on Render

### Advantages
- ✅ Free tier available (750 hours/month)
- ✅ Automatic deployments from GitHub
- ✅ Built-in SSL certificates
- ✅ Custom domains support
- ✅ Environment variable management
- ✅ Automatic restarts on failure
- ✅ Build and deploy logs

### Limitations
- ⚠️ Free tier has sleep mode (spins down after 15 min of inactivity)
- ⚠️ Cold start time when waking up from sleep
- ⚠️ Limited to 512MB RAM on free tier

## Auto-Deploy Setup

1. **Enable Auto-Deploy**
   - In your Render service settings
   - Enable "Auto-Deploy" from GitHub
   - Choose your main branch

2. **Webhook Configuration** (Optional)
   - Set up GitHub webhooks for instant deployments
   - Render provides webhook URLs in service settings

## Monitoring

### Health Checks
Render automatically monitors your service health. Configure:
- **Health Check Path:** `/health` (if implemented)
- **Health Check Timeout:** 30 seconds

### Logs
- Access logs via Render dashboard
- Use `/log` command in bot for application logs
- Monitor performance with `/perf` command

## Troubleshooting

### Common Issues
1. **Bot not responding:** Check environment variables
2. **Memory issues:** Upgrade to paid plan for more RAM
3. **Sleep mode:** Use paid plan or implement keep-alive ping
4. **Build failures:** Check requirements.txt and Python version

### Debug Commands
```bash
# Check service status
curl https://your-app.onrender.com/health

# View recent logs
# Use Render dashboard or bot /log command
```

## Cost Optimization

### Free Tier Tips
- Use sleep mode efficiently
- Implement request batching
- Optimize memory usage
- Monitor usage in dashboard

### Paid Tier Benefits
- No sleep mode
- More RAM and CPU
- Priority support
- Custom domains

## Security

### Best Practices
- Use environment variables for all secrets
- Enable GitHub branch protection
- Regular security updates
- Monitor access logs

### Environment Security
- Never commit secrets to repository
- Use Render's encrypted environment variables
- Rotate tokens regularly
- Limit API access where possible