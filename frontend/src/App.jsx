import { useState } from 'react';
import Dashboard from './Dashboard';
import CreateCalculation from './CreateCalculation';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');

  const navigateToCreateCalc = () => setCurrentView('create-calc');
  const navigateToDashboard = () => setCurrentView('dashboard');

  return (
    <>
      {currentView === 'dashboard' && <Dashboard onNavigateCreate={navigateToCreateCalc} />}
      {currentView === 'create-calc' && <CreateCalculation onBack={navigateToDashboard} />}
    </>
  );
}

export default App;
