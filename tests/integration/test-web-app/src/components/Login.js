import React, { useState } from 'react';
import { Container, Card, Form, Button, Alert } from 'react-bootstrap';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const Login = ({ onLoginSuccess }) => {
    const [formData, setFormData] = useState({
        username: '',
        password: ''
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleInputChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
        if (error) setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: formData.username,
                    password: formData.password
                })
            });

            if (response.ok) {
                const data = await response.json();
                
                // Get user info
                const userResponse = await fetch(`${API_BASE_URL}/users/me`, {
                    headers: {
                        'Authorization': `Bearer ${data.access_token}`
                    }
                });
                
                if (userResponse.ok) {
                    const userData = await userResponse.json();
                    const userInfo = {
                        ...userData,
                        token: data.access_token
                    };
                    localStorage.setItem('user', JSON.stringify(userInfo));
                    onLoginSuccess(userInfo);
                } else {
                    setError('Failed to get user information');
                }
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Login failed');
            }
        } catch (err) {
            setError('Network error. Please check if the backend is running.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container className="d-flex justify-content-center align-items-center min-vh-100">
            <Card style={{ width: '400px' }}>
                <Card.Header className="text-center">
                    <h4>GlyphQA Login</h4>
                </Card.Header>
                <Card.Body>
                    {error && (
                        <Alert variant="danger">
                            {error}
                        </Alert>
                    )}

                    <Form onSubmit={handleSubmit}>
                        <Form.Group className="mb-3">
                            <Form.Label>Username</Form.Label>
                            <Form.Control
                                type="text"
                                name="username"
                                placeholder="Enter username"
                                value={formData.username}
                                onChange={handleInputChange}
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Password</Form.Label>
                            <Form.Control
                                type="password"
                                name="password"
                                placeholder="Password"
                                value={formData.password}
                                onChange={handleInputChange}
                                required
                            />
                        </Form.Group>

                        <div className="d-grid">
                            <Button
                                variant="primary"
                                type="submit"
                                disabled={loading}
                            >
                                {loading ? 'Logging in...' : 'Login'}
                            </Button>
                        </div>
                    </Form>

                    <div className="mt-3 text-muted small">
                        <strong>Test Credentials:</strong><br />
                        Admin: admin / admin_password<br />
                        User: user / password
                    </div>
                </Card.Body>
            </Card>
        </Container>
    );
};

export default Login;
