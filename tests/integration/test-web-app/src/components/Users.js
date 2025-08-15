import React, { useState } from 'react';
import { Card, Table, Button, Modal, Form, Badge } from 'react-bootstrap';

const Users = () => {
    const [showModal, setShowModal] = useState(false);
    const [users] = useState([
        { id: 1, name: 'John Doe', email: 'john.doe@example.com', role: 'user', status: 'active' },
        { id: 2, name: 'Jane Smith', email: 'jane.smith@example.com', role: 'admin', status: 'active' },
        { id: 3, name: 'Bob Johnson', email: 'bob.johnson@example.com', role: 'user', status: 'inactive' },
        { id: 4, name: 'Admin User', email: 'admin@test.com', role: 'administrator', status: 'active' },
        { id: 5, name: 'Regular User', email: 'user@test.com', role: 'user', status: 'active' }
    ]);

    const [newUser, setNewUser] = useState({
        name: '',
        email: '',
        role: 'user'
    });

    const handleInputChange = (e) => {
        setNewUser({
            ...newUser,
            [e.target.name]: e.target.value
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        setShowModal(false);
        setNewUser({ name: '', email: '', role: 'user' });
    };

    const getRoleVariant = (role) => {
        switch (role) {
            case 'administrator': return 'danger';
            case 'admin': return 'warning';
            case 'user': return 'primary';
            default: return 'secondary';
        }
    };

    const getStatusVariant = (status) => {
        return status === 'active' ? 'success' : 'secondary';
    };

    return (
        <div>
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h2>Users Management</h2>
                <Button
                    variant="primary"
                    onClick={() => setShowModal(true)}
                   
                >
                    Add New User
                </Button>
            </div>

            <Card>
                <Card.Body>
                    <Table responsive>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Role</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(user => (
                                <tr key={user.id}>
                                    <td>{user.id}</td>
                                    <td>{user.name}</td>
                                    <td>{user.email}</td>
                                    <td>
                                        <Badge bg={getRoleVariant(user.role)}>
                                            {user.role}
                                        </Badge>
                                    </td>
                                    <td>
                                        <Badge bg={getStatusVariant(user.status)}>
                                            {user.status}
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
                    <Modal.Title>Add New User</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form onSubmit={handleSubmit}>
                        <Form.Group className="mb-3">
                            <Form.Label>Full Name</Form.Label>
                            <Form.Control
                                type="text"
                                name="name"
                                placeholder="Enter full name"
                                value={newUser.name}
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
                            <Form.Label>Role</Form.Label>
                            <Form.Select
                                name="role"
                                value={newUser.role}
                                onChange={handleInputChange}
                               
                            >
                                <option value="user">User</option>
                                <option value="admin">Admin</option>
                                <option value="administrator">Administrator</option>
                            </Form.Select>
                        </Form.Group>

                        <Button variant="primary" type="submit">
                            Save User
                        </Button>
                    </Form>
                </Modal.Body>
            </Modal>
        </div>
    );
};

export default Users;
