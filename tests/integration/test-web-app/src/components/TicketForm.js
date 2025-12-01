import React, { useState } from 'react';
import { Container, Card, Form, Button, Alert } from 'react-bootstrap';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const TicketForm = ({ user }) => {
    const [content, setContent] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);

    const getAuthToken = () => {
        if (!user) return null;
        return user.token;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');

        try {
            const token = getAuthToken();
            const headers = {
                'Content-Type': 'application/json',
            };

            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch(`${API_BASE_URL}/tickets`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ content })
            });

            if (response.ok) {
                setContent('');
                setSuccess('Ticket submitted successfully!');
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Failed to submit ticket');
            }
        } catch (err) {
            setError('Network error. Please check if the backend is running.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container className="d-flex justify-content-center align-items-center min-vh-100">
            <Card style={{ width: '600px' }}>
                <Card.Header className="text-center">
                    <h4>Submit a Ticket</h4>
                </Card.Header>
                <Card.Body>
                    {user && (
                        <Alert variant="info" className="mb-3">
                            Submitting as: <strong>{user.username}</strong>
                        </Alert>
                    )}

                    {error && (
                        <Alert variant="danger">
                            {error}
                        </Alert>
                    )}

                    {success && (
                        <Alert variant="success">
                            {success}
                        </Alert>
                    )}

                    <Form onSubmit={handleSubmit}>
                        <Form.Group className="mb-3">
                            <Form.Label>Ticket Content</Form.Label>
                            <Form.Control
                                as="textarea"
                                rows={6}
                                placeholder="Describe your issue or request..."
                                value={content}
                                onChange={(e) => setContent(e.target.value)}
                                required
                            />
                        </Form.Group>

                        <div className="d-grid">
                            <Button
                                variant="primary"
                                type="submit"
                                disabled={loading}
                            >
                                {loading ? 'Submitting...' : 'Submit Ticket'}
                            </Button>
                        </div>
                    </Form>
                </Card.Body>
            </Card>
        </Container>
    );
};

export default TicketForm;

