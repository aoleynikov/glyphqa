import React from 'react';
import { Container, Navbar, Nav, Button } from 'react-bootstrap';

const Layout = ({ user, activeTab, onTabChange, onLogout, children }) => {
    const allTabs = [
        { key: 'dashboard', label: 'Dashboard', roles: ['admin', 'user'] },
        { key: 'users', label: 'Users', roles: ['admin'] },
        { key: 'tickets', label: 'Tickets', roles: ['admin'] },
        { key: 'settings', label: 'Settings', roles: ['admin'] }
    ];

    // Filter tabs based on user role
    const tabs = allTabs.filter(tab => tab.roles.includes(user.role));

    return (
        <div>
            <Navbar bg="primary" variant="dark" expand="lg">
                <Container>
                    <Navbar.Brand>GlyphQA Dashboard</Navbar.Brand>
                    <Navbar.Toggle aria-controls="basic-navbar-nav" />
                    <Navbar.Collapse id="basic-navbar-nav">
                        <Nav className="me-auto">
                            {tabs.map(tab => (
                                <Nav.Link
                                    key={tab.key}
                                    active={activeTab === tab.key}
                                    onClick={() => onTabChange(tab.key)}
                                    style={{ cursor: 'pointer' }}
                                >
                                    {tab.label}
                                </Nav.Link>
                            ))}
                        </Nav>
                        <Nav>
                            <Navbar.Text className="me-3">
                                Welcome, <span>{user.username}</span>
                            </Navbar.Text>
                            <Button
                                variant="outline-light"
                                size="sm"
                                onClick={onLogout}
                            >
                                Logout
                            </Button>
                        </Nav>
                    </Navbar.Collapse>
                </Container>
            </Navbar>

            <Container className="mt-4">
                {children}
            </Container>
        </div>
    );
};

export default Layout;
