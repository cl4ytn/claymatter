---
category: projects
---

## Momofin Document Verification System Overview

The Momofin Document Verification System is a robust cryptography-based platform designed to ensure the integrity, authenticity, and validity of digital documents. It utilizes HMAC functions to generate hash strings that detect transmission tampering, alongside advanced encryption algorithms and dynamic QR codes to prevent forgery.

## Development Tools and Technology Stack

Our development stack for Momofin leverages PostgreSQL for database management, paired with JavaScript and Java across the application layers. The frontend is built with ReactJS while the backend runs on Spring Boot. We use Figma for UI/UX wireframing, GitHub for version control, and deploy our services on Koyeb and Vercel.

## System Authentication and Access Control

Authentication requires users to first input their registered organization name. Once validated, users provide their company email and password. Access is denied with specific error messages if credentials fail. Authorization is structured across three tiers: Regular Users, Organization Admins, and Momofin System Admins, governing permissions from document editing to system-wide management.

## Core User Functionalities

Regular users can upload documents under their organization, generate metadata-encoded QR codes, and verify document authenticity. The system supports a controlled editing workflow where owners grant temporary edit permissions that automatically revoke upon committing changes. Users can also view audit logs, revoke outdated documents, and manage their passwords.

## Administrative Management and System Architecture

Organization admins manage encryption key pairs, configure organization profiles, and oversee local user accounts. Momofin system admins hold full platform control, managing all registered organizations, global users, and system-wide logs. Data migration and archiving policies ensure secure backups, encrypted credentials, and smooth transitions to production infrastructure.