import React, { useState, useEffect } from 'react';
import Login from './components/Login';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';
import Users from './components/Users';
import Settings from './components/Settings';

function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Check for persisted login on app start
  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
      try {
        const userData = JSON.parse(savedUser);
        // Check if token exists and is not expired
        if (userData.token) {
          setUser(userData);
        } else {
          localStorage.removeItem('user');
        }
      } catch (error) {
        localStorage.removeItem('user');
      }
    }
  }, []);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    setActiveTab('dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    setUser(null);
    setActiveTab('dashboard');
  };

  const renderContent = () => {
    // Check if user has access to the current tab
    const hasAccess = (tab) => {
      if (tab === 'dashboard') return true;
      if (tab === 'users' || tab === 'settings') return user.role === 'admin';
      return true;
    };

    if (!hasAccess(activeTab)) {
      setActiveTab('dashboard');
      return <Dashboard user={user} />;
    }

    switch (activeTab) {
      case 'dashboard':
        return <Dashboard user={user} onTabChange={setActiveTab} />;
      case 'users':
        return <Users />;
      case 'settings':
        return <Settings user={user} />;
      default:
        return <Dashboard user={user} onTabChange={setActiveTab} />;
    }
  };

  if (!user) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <Layout
      user={user}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      onLogout={handleLogout}
    >
      {renderContent()}
    </Layout>
  );
}

export default App;