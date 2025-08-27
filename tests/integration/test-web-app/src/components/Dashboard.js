import React from 'react';
import { Row, Col, Card, Alert, Badge } from 'react-bootstrap';

const Dashboard = ({ user }) => {
    const stats = [
        { title: 'Total Users', value: '1,234', variant: 'primary', },
        { title: 'Active Sessions', value: '89', variant: 'success', },
        { title: 'Pending Tasks', value: '15', variant: 'warning', },
        { title: 'System Alerts', value: '3', variant: 'danger', }
    ];

    const recentActivity = [
        { id: 1, action: 'User login', user: 'john.doe@example.com', time: '2 minutes ago' },
        { id: 2, action: 'Data export', user: 'admin@test.com', time: '15 minutes ago' },
        { id: 3, action: 'Settings updated', user: 'user@test.com', time: '1 hour ago' },
        { id: 4, action: 'New user registered', user: 'newuser@example.com', time: '2 hours ago' }
    ];

    return (
        <div>
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h2>Dashboard</h2>
                <Badge bg="info">
                    {user.role}
                </Badge>
            </div>

            <Alert variant="info">
                Welcome back, {user.username}! Here's your system overview.
            </Alert>

            <Row className="mb-4">
                {stats.map((stat, index) => (
                    <Col md={3} key={index} className="mb-3">
                        <Card>
                            <Card.Body className="text-center">
                                <h3 className={`text-${stat.variant}`}>
                                    {stat.value}
                                </h3>
                                <p className="text-muted mb-0">{stat.title}</p>
                            </Card.Body>
                        </Card>
                    </Col>
                ))}
            </Row>

            <Row>
                <Col md={8}>
                    <Card>
                        <Card.Header>
                            <h5>Recent Activity</h5>
                        </Card.Header>
                        <Card.Body>
                            <div>
                                {recentActivity.map(activity => (
                                    <div key={activity.id} className="d-flex justify-content-between align-items-center py-2 border-bottom">
                                        <div>
                                            <strong>{activity.action}</strong><br />
                                            <small className="text-muted">{activity.user}</small>
                                        </div>
                                        <small className="text-muted">{activity.time}</small>
                                    </div>
                                ))}
                            </div>
                        </Card.Body>
                    </Card>
                </Col>

                <Col md={4}>
                    <Card>
                        <Card.Header>
                            <h5>Quick Actions</h5>
                        </Card.Header>
                        <Card.Body>
                            <div className="d-grid gap-2">
                                <button className="btn btn-primary">
                                    Create New User
                                </button>
                                <button className="btn btn-outline-secondary">
                                    Export Data
                                </button>
                                <button className="btn btn-outline-info">
                                    Generate Report
                                </button>
                            </div>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default Dashboard;
