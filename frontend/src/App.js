import React, { useState } from 'react';
import SignupForm from './components/SignupForm';
import LoginForm from './components/LoginForm';
import Dashboard from './components/Dashboard';
import Footer from './components/Footer';

function App() {
  const [page, setPage] = useState('login');

  // Set different titles based on the current page
  const getPageTitle = () => {
    switch (page) {
      case 'signup':
        return 'Create Your Account';
      case 'login':
        return 'Welcome To Login';
      case 'dashboard':
        return 'Smart Finance Console';
      default:
        return '';
    }
  };

  return (
    <div className="app-container">
      <h1 className="title">{getPageTitle()}</h1>

      {page === 'signup' && <SignupForm setPage={setPage} />}
      {page === 'login' && <LoginForm setPage={setPage} />}
      {page === 'dashboard' && <Dashboard />}
      
      <Footer />
    </div>
  );
}

export default App;
