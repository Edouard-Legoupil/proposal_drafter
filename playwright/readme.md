### Running the Tests

Install playwrithgt with:

```bash
npx playwright install 
```

To run the Playwright tests, navigate to the `frontend` directory and run the following command:

```bash
npx playwright test
```

This will run all the tests in the `tests` directory. You can also run a specific test file:

```bash
npx playwright test tests/auth.spec.js
```
