# filepath: /C:/Users/shish/OneDrive/Desktop/Django 5/DjangoQR/scanner/management/commands/cleanup_orphaned_qrcodes.py
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from scanner.models import QRCode

class Command(BaseCommand):
    help = 'Clean up orphaned QR code entries from the database'

    def handle(self, *args, **kwargs):
        qr_storage_path = Path(settings.MEDIA_ROOT) / 'qr_codes'
        qr_codes = QRCode.objects.all()

        for qr_code in qr_codes:
            qr_image_path = qr_storage_path / f"{qr_code.data}_{qr_code.mobile_number}.png"
            if not qr_image_path.exists():
                self.stdout.write(f"Deleting orphaned QR code entry: {qr_code.data} - {qr_code.mobile_number}")
                qr_code.delete()

        self.stdout.write(self.style.SUCCESS('Successfully cleaned up orphaned QR code entries'))