# Deployment Instructions

## IMPORTANT: The deploy.sh script must be run on your Linux server, NOT on Windows

I see you're trying to run the deploy.sh script directly on Windows, which won't work because it's a Linux bash script that requires Linux commands.

## How to Deploy to Your Cloud Server

Follow these steps to deploy the fixes:

### Step 1: Upload the Modified Files to Your Server

1. Upload these files to your cloud server using SFTP/SCP:
   - `deploy.sh` - The updated script that creates virtual environment at the beginning
   - `backend/app/main.py` - The fixed main.py with the missing `/api/auth/me` endpoint
   - `api-test.html` - For testing the authentication (optional)

### Step 2: SSH into Your Server and Run the Deploy Script

```bash
# SSH into your server
ssh your-username@your-server-ip

# Navigate to where you uploaded the files
cd /path/to/uploaded/files

# Make the script executable
sudo apt install -y dos2unix
dos2unix deploy.sh
chmod +x deploy.sh

# Run the deployment script
sudo ./deploy.sh
```

### Step 3: Test the Login

After deployment completes, test the login:

1. Visit your website: https://ajingolik.fun/
2. Login with username `hamza` and password `AFINasahbi@-11`
3. The login should now work correctly

## Troubleshooting

If you still encounter issues:

1. Check the service status:
```bash
sudo systemctl status tfrtita333
```

2. View the error logs:
```bash
sudo journalctl -u tfrtita333 -n 50
```

3. Restart the service:
```bash
sudo systemctl restart tfrtita333
```

4. Upload the `api-test.html` file to your server and access it directly to test the auth endpoints.

## Windows Testing

If you want to test the authentication logic locally on Windows, you can:

1. Set up a Python virtual environment on Windows:
```
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn python-jose pydantic
```

2. Create a minimal test script using just the authentication code
3. Run it with `uvicorn` to test the auth endpoints

But the full deployment must be done on Linux. The deploy.sh script contains Linux-specific commands.
