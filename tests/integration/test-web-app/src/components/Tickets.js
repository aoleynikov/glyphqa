import React, { useState, useEffect } from 'react';
import { Card, Button, Alert, Badge } from 'react-bootstrap';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const Tickets = () => {
    const [currentTicket, setCurrentTicket] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [resolving, setResolving] = useState(false);
    const [noMoreTickets, setNoMoreTickets] = useState(false);

    const getAuthToken = () => {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        return user.token;
    };

    const fetchTodoTicket = async () => {
        setLoading(true);
        setError('');
        setNoMoreTickets(false);

        try {
            const token = getAuthToken();
            const response = await fetch(`${API_BASE_URL}/tickets/todo`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const ticket = await response.json();
                setCurrentTicket(ticket);
            } else if (response.status === 404) {
                setNoMoreTickets(true);
                setCurrentTicket(null);
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Failed to fetch ticket');
            }
        } catch (err) {
            setError('Network error while fetching ticket');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchTodoTicket();
    }, []);

    const handleResolve = async (action) => {
        if (!currentTicket) return;

        setResolving(true);
        setError('');

        try {
            const token = getAuthToken();
            const response = await fetch(`${API_BASE_URL}/tickets/${currentTicket.id}/resolve`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ action })
            });

            if (response.ok) {
                fetchTodoTicket();
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Failed to resolve ticket');
            }
        } catch (err) {
            setError('Network error while resolving ticket');
        } finally {
            setResolving(false);
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString();
    };

    if (loading) {
        return <div>Loading ticket...</div>;
    }

    return (
        <div>
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h2>Ticket Review</h2>
            </div>

            {error && (
                <Alert variant="danger" className="mb-3">
                    {error}
                </Alert>
            )}

            {noMoreTickets ? (
                <Card>
                    <Card.Body className="text-center">
                        <h5>No more tickets to review</h5>
                        <p className="text-muted">All ToDo tickets have been processed.</p>
                    </Card.Body>
                </Card>
            ) : currentTicket ? (
                <Card>
                    <Card.Header>
                        <div className="d-flex justify-content-between align-items-center">
                            <span>Ticket #{currentTicket.id.slice(-6)}</span>
                            <Badge bg="warning">{currentTicket.status}</Badge>
                        </div>
                    </Card.Header>
                    <Card.Body>
                        <div className="mb-3">
                            <strong>Submitted:</strong> {formatDate(currentTicket.submitted_at)}
                        </div>
                        {currentTicket.submitter && (
                            <div className="mb-3">
                                <strong>Submitter:</strong> {currentTicket.submitter}
                            </div>
                        )}
                        {!currentTicket.submitter && (
                            <div className="mb-3">
                                <strong>Submitter:</strong> <span className="text-muted">Anonymous</span>
                            </div>
                        )}
                        <div className="mb-3">
                            <strong>Content:</strong>
                            <div className="mt-2 p-3 bg-light rounded">
                                {currentTicket.content}
                            </div>
                        </div>
                        <div className="d-flex gap-2 justify-content-end">
                            <Button
                                variant="success"
                                onClick={() => handleResolve('accept')}
                                disabled={resolving}
                            >
                                Accept
                            </Button>
                            <Button
                                variant="danger"
                                onClick={() => handleResolve('reject')}
                                disabled={resolving}
                            >
                                Reject
                            </Button>
                        </div>
                    </Card.Body>
                </Card>
            ) : null}
        </div>
    );
};

export default Tickets;

