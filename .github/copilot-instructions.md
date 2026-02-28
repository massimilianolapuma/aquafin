# Copilot Instructions for Aquafin

## Project Overview

Aquafin is a modern personal finance application targeted primarily at iOS (SwiftUI), and later web, macOS, and iPadOS. The app allows users to manage their personal finances via budget tracking, transaction categorization (manual and AI-assisted), CSV imports, scheduled payments, and basic investment tracking. The core goal is to provide a better alternative to spreadsheets and limited or premium finance apps.

## Instructions

- Follow iOS Human Interface Guidelines when building UI
- Generate clean, modular SwiftUI views with previews
- Use MVVM or feature-driven structure
- Always document functions with brief comments
- Use sensible naming conventions for variables and functions
- Write unit tests for critical logic (e.g., transaction categorization, budget calculations)
- Use Combine or async/await for asynchronous operations
- Implement error handling and edge case management
- Use Swift's Codable for data serialization
- Use dependency injection for better testability
- Use protocols for shared logic and services
- Use SwiftLint for code style consistency
- Use Swift Package Manager for managing dependencies
- Use Git for version control, with clear commit messages
- Use GitHub Issues for tracking bugs and feature requests
- Use GitHub Projects for task management
- Use GitHub Actions for CI/CD (build, test, deploy)
- Use mock data for prototyping and testing
- Use SwiftUI previews for UI components
- Use Combine or async/await for asynchronous operations
- Use Swift's Codable for data serialization
- Use dependency injection for better testability
- Use protocols for shared logic and services
- Use SwiftLint for code style consistency
- Use Swift Package Manager for managing dependencies
- Prefer testable, extensible logic
- Suggest sensible mock data for prototyping
- Recommend when a component or logic should move to shared libraries

## Key Features to Implement

- 📊 Dashboard with account balance and expense analytics
- 💸 Expense and income tracking
- 📁 Import transactions from CSV (bank exports, etc.), supported by AI for categorization.
- 🔄 Manual transaction entry
- ⏰ Scheduled recurring payments
- 🧠 AI-assisted transaction categorization
- 🧾 Budget creation and overspending alerts
- 📈 Basic investment tracking (ETF, PAC tracking)
- 📱 Mobile-first design
- 📱 Responsive design for web and desktop
- 📱 Cross-platform compatibility (iOS, macOS, iPadOS, web)
- 🔒 Secure authentication and user data management
- 🔗 Integration with third-party financial institutions (optional)
- 📊 Analytics and reporting features
- 📤 Data export functionality (CSV, JSON)

## Technical Stack

### iOS App

- SwiftUI (iOS-first, supports later macOS/iPadOS)
- Combine or async/await
- Modular architecture with separation of concerns

### Backend

- Node.js + Express **OR** .NET 8 Minimal APIs
- SQLite (MVP) or PostgreSQL (prod-ready)
- RESTful API: `/transactions`, `/budgets`, `/investments`, `/auth`

### Authentication

- JWT-based authentication
- User registration and login
- OAuth2 for third-party integrations (optional)
- User roles (admin, user)
- Secure password storage (bcrypt)
- Email verification (optional)
- Password reset functionality
- Rate limiting and security best practices
- User data encryption at rest and in transit
- User preferences for currency, language, etc.
- User data isolation (multi-tenancy)
- User activity logging for security and analytics
- User profile management (name, email, preferences)
- User notifications (email, in-app) for important events (e.g., budget overspending)
- User onboarding flow with tutorials and tips
- User data export functionality (CSV, JSON)
- User feedback mechanism (in-app surveys, feedback forms)
- User support integration (FAQs, contact support)
- User session management (token refresh, logout)
- User data backup and restore functionality
- User consent management for data processing
- User analytics for app usage and feature engagement
- User localization support (i18n)
- User accessibility features (VoiceOver, Dynamic Type)
- User data anonymization for privacy compliance

### Authorization

- Role-based access control (RBAC)
- API key management for third-party integrations
- OAuth2 scopes for third-party access
- User consent management for data sharing

### Database

- SQLite for MVP, PostgreSQL for production
- ORM (Object-Relational Mapping)

### Transaction Management

- CRUD operations for transactions
- Transaction categorization (manual and AI-assisted)
- Scheduled payments management
- Transaction history and analytics
- Transaction import from CSV with AI categorization
- Transaction search and filtering
- Transaction tagging and notes
- Transaction reconciliation with bank statements
- Transaction reminders for upcoming payments
- Transaction export functionality (CSV, JSON)
- Transaction sharing with family members or financial advisors
- Transaction archiving for long-term storage
- Transaction import validation and error handling
- Transaction grouping by categories or tags
- Transaction split functionality for shared expenses
- Transaction currency conversion for multi-currency support
- Transaction recurring payment management
- Transaction fraud detection and alerts
- Transaction data visualization (charts, graphs)
- Transaction data import from third-party financial institutions (Plaid, Yodlee)
- Transaction data synchronization with external services
- Transaction data backup and restore functionality
- Transaction data privacy and security measures
- Transaction data enrichment (merchant logos, location data)
- Transaction data normalization for consistent categorization
- Transaction data archiving for long-term storage
- Transaction data export to third-party financial management tools
- Transaction data import from third-party financial management tools
- Transaction data tagging for better organization
- Transaction data filtering by date range, amount, category, etc.
- Transaction data search functionality
- Transaction data analytics for spending patterns
- Transaction data alerts for unusual spending patterns
- Transaction data integration with budgeting tools

### Budgeting

- CRUD operations for budgets
- Budget creation and management
- Budget categories and subcategories
- Budget overspending alerts
- Budget analytics and reports
- Budget history and trends
- Budget sharing with family members or financial advisors

### Investment Tracking

- Basic investment tracking (ETFs, PACs)
- Investment portfolio management
- Investment performance analytics
- Investment transaction history
- Investment categorization (stocks, bonds, ETFs)
- Investment alerts for significant changes
- Investment data import from third-party financial institutions
- Investment data export functionality (CSV, JSON)
- Investment data synchronization with external services
- Investment data backup and restore functionality
- Investment data privacy and security measures
- Investment data enrichment (company logos, sector data)
- Investment data normalization for consistent categorization
- Investment data archiving for long-term storage
- Investment data tagging for better organization
- Investment data filtering by date range, amount, category, etc.
- Investment data search functionality
- Investment data analytics for performance trends
- Investment data alerts for unusual performance patterns
- Investment data integration with third-party financial management tools
- Investment data import from third-party financial management tools

### AI Integration

- Python microservice or OpenAI API
- Transaction categorization using machine learning
- Budget recommendations based on spending patterns
- Investment insights based on market trends
- AI-assisted financial planning
- AI-driven alerts for unusual spending patterns
- AI-powered financial goal tracking
- AI-based personalized financial advice
- AI-driven investment recommendations
- AI-assisted budgeting suggestions
- AI-powered transaction tagging and organization
- AI-based fraud detection and alerts
- AI-driven financial health scoring
- ML for transaction classification
- Optional: predictive analytics on future expenses
- Optional: natural language processing for transaction queries
- AI-driven financial education content

## Data Models (Simplified)

```swift
struct Transaction {
  let id: UUID
  let amount: Double
  let date: Date
  let description: String
  let category: String?
  let isRecurring: Bool
  let source: String? // CSV, manual, etc.
}

struct Budget {
  let
```
