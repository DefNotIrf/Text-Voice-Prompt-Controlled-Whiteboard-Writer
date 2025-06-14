import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scopes required to upload files
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_drive():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('IDPcredentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def upload_image_to_drive(service, file_path, folder_id=None):
    file_metadata = {
        'name': os.path.basename(file_path),
    }
    if folder_id:
        file_metadata['parents'] = [folder_id]

    media = MediaFileUpload(file_path, mimetype='image/jpeg')
    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name'
    ).execute()

    print(f"✅ Uploaded '{uploaded['name']}' with ID: {uploaded['id']}")


def main():
    image_path = r"C:\Users\syabab\Desktop\cloud\example.png"
    folder_id = '1LtO4g8B6tWDX3msP9UlH1YNEc5ohiKSJ'  # Your target folder ID

    if not os.path.isfile(image_path):
        print("❌ File not found. Please check the path.")
        return

    service = authenticate_drive()
    upload_image_to_drive(service, image_path, folder_id)


if __name__ == '__main__':
    main()
