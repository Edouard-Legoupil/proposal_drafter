# Microsoft Entra ID SSO Setup Tutorial

This guide walks you through the steps required to set up Single Sign-On (SSO) with Microsoft Entra ID (formerly Azure AD) for the Proposal Drafter application.

## 1. Azure App Registration

1.  **Sign in** to the [Azure Portal](https://portal.azure.com).
2.  Navigate to **Microsoft Entra ID** > **App registrations** > **New registration**.
3.  **Name**: Enter a name (e.g., `Proposal Drafter SSO`).
4.  **Supported account types**: Select "Accounts in this organizational directory only" (or as needed for your organization).
5.  **Redirect URI**:
    *   Select **Web**.
    *   Enter your backend callback URL.
    *   **IMPORTANT**: This is the endpoint on your backend that handles the login callback. It must end with `/api/callback`.
    *   Examples:
        *   Local development: `http://localhost:8502/api/callback`
        *   Production: `https://api.yourdomain.com/api/callback`
6.  Click **Register**.

## 2. Generate Client Secret

1.  In your app registration, go to **Certificates & secrets** > **Client secrets** > **New client secret**.
2.  Add a description and select an expiration time.
3.  Click **Add**.
4.  **IMPORTANT**: Copy the **Value** of the secret immediately. You won't be able to see it again.

## 3. Configure API Permissions

1.  Go to **API permissions** > **Add a permission**.
2.  Select **Microsoft Graph**.
3.  Choose **Delegated permissions**.
4.  Search for and add:
    *   `User.Read` (Sign in and read user profile)
5.  Click **Add permissions**.

## 4. Environment Variables Configuration

Update your `.env` file (or your deployment environment variables) with the following values:

### Backend Configuration
| Variable | Description |
| :--- | :--- |
| `ENTRA_TENANT_ID` | Your Microsoft Entra Tenant ID (found in Overview). |
| `ENTRA_CLIENT_ID` | Your Application (client) ID (found in Overview). |
| `ENTRA_CLIENT_SECRET` | The client secret value generated in Step 2. |
| `ENTRA_REDIRECT_URI` | (Optional) The exact callback URL. If not set, it is inferred as `[BACKEND_URL]/api/callback`. |


## 5. Role Management

By default, all new users logging in via SSO are assigned the **"proposal writer"** role. 
Users can request elevated permissions through the application UI, which an administrator can then approve in the **System Administration** panel.
