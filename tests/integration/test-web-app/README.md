# GlyphQA Test Web App

This is a test React application created for testing automation scenarios with the GlyphQA framework.

## Features

- **Bootstrap UI Components**: Uses React Bootstrap for consistent styling
- **Login Form**: Email/password form with validation
- **Sign Up Modal**: Modal dialog with registration form
- **Test Elements**: Various UI components for testing:
  - Buttons with different variants
  - Checkboxes
  - Select dropdowns
  - Alerts and notifications
- **Test IDs**: All interactive elements have `data-testid` attributes for easy automation

## Available Scripts

In the project directory, you can run:

### `npm start`
Runs the app in development mode on [http://localhost:3000](http://localhost:3000)

### `npm run build`
Builds the app for production to the `build` folder

### `npm test`
Launches the test runner in interactive watch mode

## Test Elements

The app includes the following elements for automation testing:

- Login form with email and password inputs
- Sign up modal with name, email, and password fields
- Success, warning, and danger buttons
- Checkbox and select dropdown
- Navigation bar
- Alert notifications

All interactive elements have `data-testid` attributes for reliable element selection in automated tests.