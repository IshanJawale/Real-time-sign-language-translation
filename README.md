# Real-time-sign-language-translation

Watch the demo video here: [Watch Demo Video](https://youtube.com/shorts/O0ovKKJHVVg)

# Cloudinary Video Manager

This Flask server automatically monitors your Cloudinary account for new videos, downloads them to a local directory, and then deletes them from Cloudinary.

## Features

- Checks Cloudinary for new videos every 30 seconds
- Downloads videos to a local `temp_videos` folder
- Automatically deletes videos from Cloudinary after downloading
- Provides API endpoints to check status and manually trigger checks
- Includes a webhook endpoint for Cloudinary notifications

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your Cloudinary credentials:
   ```
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret
   ```

3. Run the server:
   ```bash
   python server.py
   ```

## API Endpoints

- `GET /status` - Check server status and video count
- `POST /trigger-check` - Manually trigger a check for new videos
- `GET /videos` - List all videos in the temp_videos directory
- `POST /webhook` - Webhook endpoint for Cloudinary notifications

## Setting up Cloudinary Webhook (Optional)

To get real-time notifications when videos are uploaded to Cloudinary:

1. Go to your Cloudinary Dashboard > Settings > Notifications
2. Create a new webhook with the URL `http://your-server-address:5000/webhook`
3. Select the "Resource" event type

## Integrating with React Native App

When you upload a video from your React Native app, the server will automatically detect it, download it, and remove it from Cloudinary. 

Your videos will be stored in the `temp_videos` folder in the server directory.

## Customization

- Change the check interval by modifying the `seconds` parameter in `scheduler.add_job`
- Adjust the maximum number of videos to retrieve by changing the `max_results` parameter in `cloudinary.api.resources` 