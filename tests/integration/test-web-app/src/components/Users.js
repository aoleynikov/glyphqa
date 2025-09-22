import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Badge, Alert } from 'react-bootstrap';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const Users = () => {
    const [showModal, setShowModal] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [userToDelete, setUserToDelete] = useState(null);
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [deleting, setDeleting] = useState(false);

    const [newUser, setNewUser] = useState({
        username: '',
        email: '',
        password: '',
        role: 'user'
    });

    // Get current user token
    const getAuthToken = () => {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        return user.token;
    };

    // Fetch users from API
    const fetchUsers = async () => {
        try {
            const token = getAuthToken();
            const response = await fetch(`${API_BASE_URL}/users`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                setUsers(data);
            } else {
                setError('Failed to fetch users');
            }
        } catch (err) {
            setError('Network error while fetching users');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleInputChange = (e) => {
        setNewUser({
            ...newUser,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        setError('');

        try {
            const token = getAuthToken();
            const response = await fetch(`${API_BASE_URL}/users`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(newUser)
            });

            if (response.ok) {
                setShowModal(false);
                setNewUser({ username: '', email: '', password: '', role: 'user' });
                fetchUsers(); // Refresh the list
            } else {
                const errorData = await response.json();
                let errorMessage = 'Failed to create user';

                if (errorData.detail) {
                    if (errorData.detail.includes('Username already exists')) {
                        errorMessage = 'Username already exists. Please choose a different username.';
                    } else if (errorData.detail.includes('Email already exists')) {
                        errorMessage = 'Email already exists. Please use a different email address.';
                    } else {
                        errorMessage = errorData.detail;
                    }
                }

                setError(errorMessage);
            }
        } catch (err) {
            setError('Network error while creating user');
        } finally {
            setSubmitting(false);
        }
    };

    const handleDeleteClick = (user) => {
        setUserToDelete(user);
        setShowDeleteModal(true);
        setError('');
    };

    const handleDeleteConfirm = async () => {
        if (!userToDelete) return;

        setDeleting(true);
        setError('');

        try {
            const token = getAuthToken();
            const response = await fetch(`${API_BASE_URL}/users/${userToDelete.id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                setShowDeleteModal(false);
                setUserToDelete(null);
                fetchUsers(); // Refresh the list
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Failed to delete user');
            }
        } catch (err) {
            setError('Network error while deleting user');
        } finally {
            setDeleting(false);
        }
    };

    const handleDeleteCancel = () => {
        setShowDeleteModal(false);
        setUserToDelete(null);
        setError('');
    };

    const getRoleVariant = (role) => {
        switch (role) {
            case 'admin': return 'warning';
            case 'user': return 'primary';
            default: return 'secondary';
        }
    };

    if (loading) {
        return <div>Loading users...</div>;
    }

    return (
        <div>
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h2>Users Management</h2>
                <Button
                    variant="primary"
                    onClick={() => setShowModal(true)}
                >
                    Create User
                </Button>
            </div>

            {error && (
                <Alert variant="danger" className="mb-3">
                    {error}
                </Alert>
            )}

            <Card>
                <Card.Body>
                    <Table responsive>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Username</th>
                                <th>Email</th>
                                <th>Role</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(user => (
                                <tr key={user.id}>
                                    <td>{user.id}</td>
                                    <td>{user.username}</td>
                                    <td>{user.email}</td>
                                    <td>
                                        <Badge bg={getRoleVariant(user.role)}>
                                            {user.role}
                                        </Badge>
                                    </td>
                                    <td>
                                        <Button
                                            variant="outline-primary"
                                            size="sm"
                                            className="me-2"
                                        >
                                            Edit
                                        </Button>
                                        <Button
                                            variant="outline-danger"
                                            size="sm"
                                            onClick={() => handleDeleteClick(user)}
                                        >
                                            Delete
                                        </Button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </Table>
                </Card.Body>
            </Card>

            <Modal show={showModal} onHide={() => setShowModal(false)}>
                <Modal.Header closeButton>
                    <Modal.Title>Create User</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {error && (
                        <Alert variant="danger" className="mb-3">
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
                                value={newUser.username}
                                onChange={handleInputChange}
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Email address</Form.Label>
                            <Form.Control
                                type="email"
                                name="email"
                                placeholder="Enter email"
                                value={newUser.email}
                                onChange={handleInputChange}
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Password</Form.Label>
                            <Form.Control
                                type="password"
                                name="password"
                                placeholder="Enter password"
                                value={newUser.password}
                                onChange={handleInputChange}
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Role</Form.Label>
                            <Form.Select
                                name="role"
                                value={newUser.role}
                                onChange={handleInputChange}
                            >
                                <option value="user">User</option>
                                <option value="admin">Admin</option>
                            </Form.Select>
                        </Form.Group>

                        <Button
                            variant="primary"
                            type="submit"
                            disabled={submitting}
                        >
                            {submitting ? 'Creating...' : 'Create User'}
                        </Button>
                    </Form>
                </Modal.Body>
            </Modal>

            {/* Delete Confirmation Modal */}
            <Modal show={showDeleteModal} onHide={handleDeleteCancel}>
                <Modal.Header closeButton>
                    <Modal.Title>Confirm Delete</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {error && (
                        <Alert variant="danger" className="mb-3">
                            {error}
                        </Alert>
                    )}

                    <p>
                        Are you sure you want to delete user <strong>{userToDelete?.username}</strong>?
                    </p>
                    <p className="text-muted">
                        This action cannot be undone.
                    </p>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={handleDeleteCancel}>
                        Cancel
                    </Button>
                    <Button
                        variant="danger"
                        onClick={handleDeleteConfirm}
                        disabled={deleting}
                    >
                        {deleting ? 'Deleting...' : 'Delete User'}
                    </Button>
                </Modal.Footer>
            </Modal>
        </div>
    );
};

export default Users;
