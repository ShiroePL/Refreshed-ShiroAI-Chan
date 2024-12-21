import asyncio
import pyvts

# Define your plugin information
plugin_info = {
    "plugin_name": "Shiro chan",
    "developer": "Madrus",
    "authentication_token_path": "./token.txt"  # Path to store the authentication token
}

async def main():
    # Create a VTS instance with your plugin information
    vts = pyvts.vts(plugin_info=plugin_info)
    
    # Connect to VTube Studio
    await vts.connect()
    
    # Request a new authentication token
    await vts.request_authenticate_token()
    
    # Authenticate using the new token
    authenticated = await vts.request_authenticate()
    
    if authenticated:
        print("Successfully authenticated with VTube Studio!")
        # You can now send other requests, like triggering hotkeys
        # await vts.request(vts.vts_request.requestTriggerHotKey(hotkeyID="YourHotkeyID"))
    else:
        print("Authentication failed. Please check the token and try again.")
    
    # Close the connection
    await vts.close()

if __name__ == "__main__":
    asyncio.run(main())
