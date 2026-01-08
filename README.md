# Blog Management System

A full-stack Blog Management System built with **FastAPI** (backend) and **React** (frontend).  
The application supports user authentication, blog creation, secure access control, and email notifications.

---

## Features

### Authentication & Authorization
- User registration and login
- JWT-based access tokens
- Secure password hashing using bcrypt
- Token expiration handling
- Protected API endpoints

###  Blog Management
- Create blogs
- Edit blogs (only by the author)
- Delete blogs (only by the author)
- View all blogs created by the logged-in user

###  Email System
- Welcome email sent after user registration
- SMTP-based email delivery (Gmail App Password supported)
- Non-blocking email sending using FastAPI BackgroundTasks

###  User Management
- Each blog belongs to a user (author)
- Users can only manage their own content

---

## Planned Features

- Privilege system:
  - Admin users can view and manage all blogs
- Role-based access control (RBAC)
- Public blog feed
- Pagination and search
- HTML email templates

---

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- MySQL
- JWT (python-jose)
- bcrypt / passlib
- aiosmtplib
- python-dotenv

### Frontend
- React
- React Router
- Fetch API
- Tailwind CSS

---

