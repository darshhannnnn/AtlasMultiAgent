import React from 'react';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import LiquidCursor from './components/ui/LiquidCursor';
import { useAppStore } from './store/useAppStore';

function App() {
  const isAuthenticated = useAppStore((s) => s.isAuthenticated);

  return (
    <>
      {/* GLSL Metaball Cursor */}
      <LiquidCursor />

      {isAuthenticated ? <Dashboard /> : <Login />}
    </>
  );
}

export default App;
