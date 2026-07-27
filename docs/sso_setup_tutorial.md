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

Update `backend/.env` for local development, or set these values in the deployment environment. Do not commit the file.

### Backend Configuration
| Variable | Description |
| :--- | :--- |
| `ENTRA_TENANT_ID` | Your Microsoft Entra Tenant ID (found in Overview). |
| `ENTRA_CLIENT_ID` | Your Application (client) ID (found in Overview). |
| `ENTRA_CLIENT_SECRET` | The client secret value generated in Step 2. |
| `ENTRA_REDIRECT_URI` | Production: required and must exactly match the registered public callback. Development: optional; when absent, the callback is inferred from the request. |

When `ENTRA_REDIRECT_URI` is absent in local development, the application infers
`http://localhost:8502/api/callback` from the request. You must still register this exact local URI in Entra.

In production, set `ENTRA_REDIRECT_URI` explicitly to the public callback URI registered in Entra. The values must match exactly.

Locally, `/api/sso-status` requires the three Entra credentials: `ENTRA_TENANT_ID`, `ENTRA_CLIENT_ID`, and
`ENTRA_CLIENT_SECRET`. Production additionally requires `ENTRA_REDIRECT_URI`.

## 5. Verify the integration

1. Start the backend and open `http://localhost:8502/api/sso-status`.
2. Confirm the response is `{"enabled": true}`.
3. Open `http://localhost:8502/api/sso-login` and complete the Entra sign-in.
4. Confirm that Entra redirects to the registered callback URI and the application then opens `/dashboard`.

An `Invalid OAuth state` response usually means the browser did not return the short-lived state cookie. Confirm that the
login and callback use the same host and scheme and that cookies are enabled.


## 6. Role Management

By default, all new users logging in via SSO are assigned the **"proposal writer"** role.
Users can request elevated permissions through the application UI, which an administrator can then approve in the **System Administration** panel.
