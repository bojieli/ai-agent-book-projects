import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { HashRouter } from 'react-router-dom'
import './global.less'
import Router from './router'
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <HashRouter>
      <Router />
    </HashRouter>
  </StrictMode>,
)
