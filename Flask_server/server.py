import os
import time
import requests
import cloudinary
import cloudinary.api
import cloudinary.uploader
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from sign_to_text import video_to_text
from flask_cors import CORS
from text_to_sign import generate_sentence_video

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Cloudinary with credentials from environment variables
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Create temp_videos directory if it doesn't exist
TEMP_VIDEOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_videos')
os.makedirs(TEMP_VIDEOS_DIR, exist_ok=True)

# Global variable to store the latest sign text result
latest_sign_text = ""
latest_video_id = ""

def check_and_download_videos():
    """
    Check Cloudinary for new videos, download them, and delete them from Cloudinary.
    Only processes videos in the sign-to-text folder.
    """
    global latest_sign_text, latest_video_id
    
    try:
        # Get list of videos from Cloudinary
        result = cloudinary.api.resources(resource_type="video", max_results=30)
        
        if not result.get('resources'):
            return
        
        print(f"Found {len(result['resources'])} videos in Cloudinary")
        
        # Process each video
        for resource in result['resources']:
            video_url = resource['secure_url']
            public_id = resource['public_id']
            format_extension = resource['format']
            
            # Only process videos in the sign-to-text folder
            if not public_id.startswith('sign-to-text/'):
                print(f"Skipping video not in sign-to-text folder: {public_id}")
                continue
            
            # Extract just the filename without folder structure for local storage
            base_filename = public_id.split('/')[-1]
            
            # Create a filename for the downloaded video
            filename = f"{base_filename}.{format_extension}"
            local_path = os.path.join(TEMP_VIDEOS_DIR, filename)
            
            # Download the video
            print(f"Downloading {filename} from sign-to-text folder...")
            response = requests.get(video_url)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print(f"Successfully downloaded {filename} to {local_path}")
                
                # Delete the video from Cloudinary
                cloudinary.uploader.destroy(public_id, resource_type="video")
                print(f"Deleted {filename} from Cloudinary")
                
                # Use the full path when calling video_to_text
                sign_text = video_to_text(local_path)
                print(f"Prediction result: {sign_text}")
                
                # Update the latest prediction result
                latest_sign_text = sign_text
                latest_video_id = public_id
            else:
                print(f"Failed to download {filename}: HTTP {response.status_code}")
    except Exception as e:
        print(f"Error checking and downloading videos: {str(e)}")

# Create a scheduler to check for videos periodically
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_and_download_videos, trigger="interval", seconds=10)
scheduler.start()

@app.route('/status', methods=['GET'])
def status():
    """Endpoint to check server status."""
    return jsonify({
        "status": "running",
        "temp_videos_directory": TEMP_VIDEOS_DIR,
        "videos_count": len([f for f in os.listdir(TEMP_VIDEOS_DIR) if os.path.isfile(os.path.join(TEMP_VIDEOS_DIR, f))])
    })

@app.route('/latest-translation', methods=['GET'])
def get_latest_translation():
    """Endpoint to get the latest sign language translation."""
    global latest_sign_text, latest_video_id
    
    # Extract the folder information if present in the video_id
    folder = "none"
    if '/' in latest_video_id:
        folder = latest_video_id.split('/')[0]
    
    return jsonify({
        "text": latest_sign_text,
        "video_id": latest_video_id,
        "folder": folder,
        "timestamp": time.time()
    })

@app.route('/trigger-check', methods=['POST'])
def trigger_check():
    """Manually trigger the check for new videos."""
    check_and_download_videos()
    return jsonify({"status": "success", "message": "Triggered check for new videos"})

@app.route('/videos', methods=['GET'])
def list_videos():
    """List all videos in the temp_videos directory."""
    videos = [f for f in os.listdir(TEMP_VIDEOS_DIR) if os.path.isfile(os.path.join(TEMP_VIDEOS_DIR, f))]
    return jsonify({
        "count": len(videos),
        "videos": videos
    })

@app.route('/webhook', methods=['POST'])
def cloudinary_webhook():
    """Webhook endpoint for Cloudinary notifications."""
    # This would be configured in Cloudinary to send notifications when new videos are uploaded
    try:
        data = request.json
        print(f"Received webhook from Cloudinary: {data}")
        # You could trigger an immediate check here
        check_and_download_videos()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/text-to-sign', methods=['POST'])
def text_to_sign():
    """Convert text to sign language video and return Cloudinary URL."""
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"status": "error", "message": "No text provided"}), 400
        
        text = data['text']
        print(f"Converting text to sign: '{text}'")
        
        # Create temp_uploads directory if it doesn't exist
        TEMP_UPLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_uploads')
        os.makedirs(TEMP_UPLOADS_DIR, exist_ok=True)
        
        # Generate a unique filename based on timestamp
        timestamp = int(time.time())
        output_path = os.path.join(TEMP_UPLOADS_DIR, f"text_to_sign_{timestamp}.mp4")
        
        # Generate the sign language video
        dataset_path = "Python_AI/Example_videos"
        generate_sentence_video(text, dataset_path, output_path)
        
        if not os.path.exists(output_path):
            return jsonify({
                "status": "error", 
                "message": "Failed to generate sign language video"
            }), 500
        
        # Folder name to store text-to-sign videos (protected from automatic processing)
        folder_name = "text-to-sign"
        
        # Upload to Cloudinary in the text-to-sign folder
        # Using a folder keeps these videos separate from the sign-to-text videos
        # and prevents them from being automatically downloaded and processed
        upload_result = cloudinary.uploader.upload(
            output_path,
            resource_type="video",
            folder=folder_name,
            public_id=f"text_to_sign_{timestamp}"
        )
        
        # Print Cloudinary upload details for debugging
        print(f"Cloudinary upload successful. Public ID: {upload_result['public_id']}")
        print(f"This video is stored in the '{folder_name}' folder and won't be automatically processed")
        
        # Delete the local file after uploading
        os.remove(output_path)
        
        return jsonify({
            "status": "success",
            "message": "Text converted to sign language",
            "video_url": upload_result['secure_url'],
            "public_id": upload_result['public_id']
        })
        
    except Exception as e:
        print(f"Error in text-to-sign conversion: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete-cloudinary-resource', methods=['POST'])
def delete_cloudinary_resource():
    """Delete a resource from Cloudinary."""
    try:
        data = request.json
        if not data or 'public_id' not in data:
            return jsonify({"status": "error", "message": "No public_id provided"}), 400
        
        public_id = data['public_id']
        resource_type = data.get('resource_type', 'image')  # Default to image if not specified
        
        print(f"Attempting to delete {resource_type} from Cloudinary: {public_id}")
        
        try:
            # Delete the resource from Cloudinary - public_id already includes folder path if present
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            print(f"Cloudinary delete result: {result}")
            
            if result.get('result') == 'ok':
                return jsonify({
                    "status": "success",
                    "message": f"Resource {public_id} deleted successfully"
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": f"Failed to delete resource: {result.get('result')}",
                    "details": result
                }), 400
        except Exception as inner_error:
            print(f"Inner error deleting from Cloudinary: {str(inner_error)}")
            return jsonify({
                "status": "error", 
                "message": f"Cloudinary delete error: {str(inner_error)}",
                "public_id": public_id
            }), 400
            
    except Exception as e:
        print(f"Error in delete_cloudinary_resource endpoint: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    if not all([os.getenv("CLOUDINARY_CLOUD_NAME"), os.getenv("CLOUDINARY_API_KEY"), os.getenv("CLOUDINARY_API_SECRET")]):
        print("Error: Cloudinary credentials not set. Please update your .env file.")
        exit(1)
    
    # Process any pending videos in the sign-to-text folder
    print("Processing any pending videos in the sign-to-text folder...")
    check_and_download_videos()
        
    print(f"Starting Flask server. Videos will be saved to {TEMP_VIDEOS_DIR}")
    print("Checking for new videos in the sign-to-text folder every 10 seconds...")
    app.run(host='0.0.0.0', port=5000, debug=True) 