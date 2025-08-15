import React, { useState } from 'react';
import { Container, Card, Form, Button, Alert } from 'react-bootstrap';

const Login = ({ onLoginSuccess }) => {
    const [formData, setFormData] = useState({
        email: '',
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

        // Hardcoded login logic
        setTimeout(() => {
            if (formData.email === 'admin' && formData.password === 'admin_password') {
                const userData = {
                    email: formData.email,
                    name: 'Admin User',
                    role: 'admin'
                };
                localStorage.setItem('user', JSON.stringify(userData));
                onLoginSuccess(userData);
            } else if (formData.email === 'user' && formData.password === 'password') {
                const userData = {
                    email: formData.email,
                    name: 'Regular User',
                    role: 'user'
                };
                localStorage.setItem('user', JSON.stringify(userData));
                onLoginSuccess(userData);
            } else {
                setError('Invalid credentials. Try admin/admin_password or user/password');
            }
            setLoading(false);
        }, 1000);
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
                                name="email"
                                placeholder="Enter username"
                                value={formData.email}
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
