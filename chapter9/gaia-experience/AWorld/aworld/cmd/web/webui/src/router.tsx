import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

const App = lazy(() => import('./pages/App'));
const XyFlowPage = lazy(() => import('./pages/xyflow'));

const routes = [
  {
    path: '/index.html',
    element: <Navigate to="/" replace />
  },
  {
    path: '/',
    element: <App />
  },
  {
    path: '/xyflow',
    element: <XyFlowPage />
  }
];

const FallbackComponent: React.FC = () => <div style={{ opacity: 0 }}>Loading...</div>;

const AppRouter: React.FC = () => {
  return (
    <Suspense fallback={<FallbackComponent />}>
      <Routes>
        {routes.map((route, index) => (
          <Route key={index} path={route.path} element={route.element} />
        ))}
      </Routes>
    </Suspense>
  );
};

export default AppRouter;
