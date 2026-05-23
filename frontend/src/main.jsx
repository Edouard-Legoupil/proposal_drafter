import './index.css'

import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import App from './App.jsx'
import { WizardProvider } from './context/WizardContext'

createRoot(document.getElementById('root')).render(
  <BrowserRouter basename={import.meta.env.BASE_URL}>
    <WizardProvider>
      <App />
    </WizardProvider>
  </BrowserRouter>
);
