# Frontend Application

This directory contains the frontend of the proposal drafting application, built with React and Vite.

## Code Structure

The frontend code is organized into the following directories:

-   **`public/`**: This directory contains static assets that are publicly accessible, such as the application's favicon.

-   **`src/`**: This is the main directory for the application's source code.
    -   **`assets/`**: This directory contains static assets that are imported into the application, such as images and fonts.
    -   **`components/`**: This directory contains reusable React components that are used throughout the application.
    -   **`screens/`**: This directory contains the main screens or pages of the application. Each screen is a combination of components and represents a distinct view in the application.
    -   **`mocks/`**: This directory contains mock data and server handlers for testing purposes.
    -   **`App.jsx`**: The main application component. It sets up the application's routing and renders the different screens.
    -   **`main.jsx`**: The entry point of the application. It renders the `App` component into the DOM.
    -   **`index.css`**: The main stylesheet for the application.

-   **`vite.config.js`**: The configuration file for Vite, the build tool used by the application.

-   **`vitest.config.js`**: The configuration file for Vitest, the testing framework used by the application.

## Running the Application

To run the application locally, you will need to have Node.js and npm installed. From this directory, run:

```bash
npm install
npm run dev
```

The application will be available at `http://localhost:8503`.

## Environment Variables

The application uses environment variables for configuration. You can find a list of the required variables in `.env.example`. Create a `.env` file in this directory with your own values.
