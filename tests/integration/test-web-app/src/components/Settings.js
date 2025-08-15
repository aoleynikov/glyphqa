import React, { useState } from 'react';
import { Card, Form, Button, Alert, Row, Col } from 'react-bootstrap';

const Settings = ({ user }) => {
    const [showAlert, setShowAlert] = useState(false);
    const [settings, setSettings] = useState({
        siteName: 'GlyphQA Test App',
        adminEmail: 'admin@glyphqa.com',
        enableNotifications: true,
        enableLogging: true,
        maxUsers: '1000',
        sessionTimeout: '30',
        theme: 'light',
        language: 'en'
    });

    const handleInputChange = (e) => {
        const { name, type, checked, value } = e.target;
        setSettings({
            ...settings,
            [name]: type === 'checkbox' ? checked : value
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        setShowAlert(true);
        setTimeout(() => setShowAlert(false), 3000);
    };

    return (
        <div>
            <h2>System Settings</h2>

            {showAlert && (
                <Alert variant="success">
                    Settings have been saved successfully!
                </Alert>
            )}

            <Form onSubmit={handleSubmit}>
                <Row>
                    <Col md={6}>
                        <Card className="mb-4">
                            <Card.Header>
                                <h5>General Settings</h5>
                            </Card.Header>
                            <Card.Body>
                                <Form.Group className="mb-3">
                                    <Form.Label>Site Name</Form.Label>
                                    <Form.Control
                                        type="text"
                                        name="siteName"
                                        value={settings.siteName}
                                        onChange={handleInputChange}
                                       
                                    />
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Admin Email</Form.Label>
                                    <Form.Control
                                        type="email"
                                        name="adminEmail"
                                        value={settings.adminEmail}
                                        onChange={handleInputChange}
                                       
                                    />
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Maximum Users</Form.Label>
                                    <Form.Control
                                        type="number"
                                        name="maxUsers"
                                        value={settings.maxUsers}
                                        onChange={handleInputChange}
                                       
                                    />
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Session Timeout (minutes)</Form.Label>
                                    <Form.Control
                                        type="number"
                                        name="sessionTimeout"
                                        value={settings.sessionTimeout}
                                        onChange={handleInputChange}
                                       
                                    />
                                </Form.Group>
                            </Card.Body>
                        </Card>
                    </Col>

                    <Col md={6}>
                        <Card className="mb-4">
                            <Card.Header>
                                <h5>System Preferences</h5>
                            </Card.Header>
                            <Card.Body>
                                <Form.Group className="mb-3">
                                    <Form.Label>Theme</Form.Label>
                                    <Form.Select
                                        name="theme"
                                        value={settings.theme}
                                        onChange={handleInputChange}
                                       
                                    >
                                        <option value="light">Light</option>
                                        <option value="dark">Dark</option>
                                        <option value="auto">Auto</option>
                                    </Form.Select>
                                </Form.Group>

                                <Form.Group className="mb-3">
                                    <Form.Label>Language</Form.Label>
                                    <Form.Select
                                        name="language"
                                        value={settings.language}
                                        onChange={handleInputChange}
                                       
                                    >
                                        <option value="en">English</option>
                                        <option value="es">Spanish</option>
                                        <option value="fr">French</option>
                                        <option value="de">German</option>
                                    </Form.Select>
                                </Form.Group>

                                <Form.Check
                                    type="checkbox"
                                    name="enableNotifications"
                                    label="Enable Email Notifications"
                                    checked={settings.enableNotifications}
                                    onChange={handleInputChange}
                                   
                                    className="mb-3"
                                />

                                <Form.Check
                                    type="checkbox"
                                    name="enableLogging"
                                    label="Enable System Logging"
                                    checked={settings.enableLogging}
                                    onChange={handleInputChange}
                                   
                                    className="mb-3"
                                />
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>

                <Card>
                    <Card.Header>
                        <h5>User Profile</h5>
                    </Card.Header>
                    <Card.Body>
                        <Row>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Name</Form.Label>
                                    <Form.Control
                                        type="text"
                                        value={user.name}
                                        disabled
                                       
                                    />
                                </Form.Group>
                            </Col>
                            <Col md={6}>
                                <Form.Group className="mb-3">
                                    <Form.Label>Email</Form.Label>
                                    <Form.Control
                                        type="email"
                                        value={user.email}
                                        disabled
                                       
                                    />
                                </Form.Group>
                            </Col>
                        </Row>
                    </Card.Body>
                </Card>

                <div className="mt-4">
                    <Button
                        variant="primary"
                        type="submit"
                        className="me-2"
                       
                    >
                        Save Settings
                    </Button>
                    <Button
                        variant="outline-secondary"
                       
                    >
                        Reset to Defaults
                    </Button>
                </div>
            </Form>
        </div>
    );
};

export default Settings;
