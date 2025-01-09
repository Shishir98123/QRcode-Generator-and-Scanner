from django.shortcuts import render
from .models import QRCode
from django.core.files.storage import FileSystemStorage
import qrcode  # For generating QR codes
from io import BytesIO  # For working with in-memory byte streams
from pathlib import Path
from PIL import Image  # For handling images
# To convert byte data to a Django file
from django.core.files.base import ContentFile
from django.conf import settings  # For accessing project settings
import uuid  # To generate unique filenames for QR code images
import cv2  # OpenCV for QR code decoding


# Utility function to generate a random filename with a given extension (default is 'png')
# def generate_random_filename(extension="png"):
#     return f"{uuid.uuid4()}.{extension}"  # Example: 'b3f9d3e9-5e84-4b99-8b92-2d8d6a3b2e07.png'

def generate_qr(request):
    qr_image_url = None  # Initialize the variable to hold the URL of the generated QR code

    if request.method == "POST":
        # Extract the mobile number and QR data from the form
        mobile_number = request.POST.get('mobile_number')  # Get the mobile number
        data = request.POST.get('qr_data')  # Get the QR data

        # Validate the mobile number
        if not mobile_number or len(mobile_number) != 10 or not mobile_number.isdigit():
            return render(request, 'scanner/generate_qr.html', {'error': 'Invalid mobile number.'})

        # Combine data and mobile number to create the QR code content
        qr_content = f"{data}|{mobile_number}"
        qr = qrcode.make(qr_content)  # Generate the QR code

        # Save the QR code image in memory
        qr_image_io = BytesIO()
        qr.save(qr_image_io, 'PNG')
        qr_image_io.seek(0)

        # Define the storage path for QR codes
        qr_storage_path = Path(settings.MEDIA_ROOT) / 'qr_codes'
        fs = FileSystemStorage(location=str(qr_storage_path), base_url='/media/qr_codes/')

        # Save the QR code image with a unique filename
        # filename = generate_random_filename()
        filename = f"{data}_{mobile_number}.png"
        qr_image_content = ContentFile(qr_image_io.read(), name=filename)
        fs.save(filename, qr_image_content)
        # Get the public URL of the saved image
        qr_image_url = fs.url(filename)

        # Save the QR code data and mobile number in the database
        QRCode.objects.create(data=data, mobile_number=mobile_number)

    return render(request, 'scanner/generate_qr.html', {'qr_image_url': qr_image_url})


# Function to decode QR codes using OpenCV
def decode_qr_with_opencv(image_path):
    detector = cv2.QRCodeDetector()  # Initialize the QR code detector
    image = cv2.imread(str(image_path))  # Load the image using OpenCV
    data, _, _ = detector.detectAndDecode(image)  # Detect and decode the QR code
    return data  # Return the decoded data (or None if no QR code is found)


def scan_qr(request):
    result = None  # Initialize the result message

    if request.method == "POST" and request.FILES.get('qr_image'):
        mobile_number = request.POST.get('mobile_number')
        qr_image = request.FILES['qr_image']

        # Validate the mobile number
        if not mobile_number or len(mobile_number) != 10 or not mobile_number.isdigit():
            return render(request, 'scanner/scan_qr.html', {'error': 'Invalid mobile number'})

        # Save the uploaded image temporarily
        fs = FileSystemStorage()
        filename = fs.save(qr_image.name, qr_image)
        image_path = Path(fs.location) / filename

        try:
            # Decode the QR code using OpenCV
            decoded_data = decode_qr_with_opencv(image_path)

            if decoded_data:
                # Parse the decoded QR content
                qr_content = decoded_data.strip()
                qr_data, qr_mobile_number = qr_content.split('|')

                # Verify the QR code data and mobile number
                qr_entry = QRCode.objects.filter(data=qr_data, mobile_number=qr_mobile_number).first()

                if qr_entry and qr_mobile_number == mobile_number:
                    result = "Scan Success: Valid QR Code for the provided mobile number"

                    # Remove the QR code entry from the database
                    qr_entry.delete()

                    qr_image_path = settings.MEDIA_ROOT / 'qr_codes' / f"{qr_data}_{qr_mobile_number}.png"
                    if qr_image_path.exists():
                        qr_image_path.unlink()

                    if image_path.exists():
                        image_path.unlink()

                else:
                    result = "Scan Failed: Invalid QR Code or mobile number mismatch"

            else:
                result = "No QR Code detected in the image"

        except Exception as e:
            result = f"Error processing the image: {str(e)}"

        finally:
             if image_path.exists():
                  image_path.unlink()
    return render(request, 'scanner/scan_qr.html', {'result': result})