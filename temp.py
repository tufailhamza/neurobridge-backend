import cloudinary
import cloudinary.uploader
import cloudinary.api

# Configure
cloudinary.config( 
  cloud_name = "dbqa116an", 
  api_key = "423497448488434", 
  api_secret = "iUV-JvHD8ZL4b_SFyPctBOYGpKg" 
)
image_path = r"a.jpg" 
# Try uploading a test image
result = cloudinary.uploader.upload(image_path)
print(result["secure_url"])
