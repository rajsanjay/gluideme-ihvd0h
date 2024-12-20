# Transfer Requirements Management System - Frontend

A comprehensive web-based platform built with Next.js 13+ for managing course transfer requirements between California community colleges and 4-year institutions. This frontend application provides intuitive interfaces for administrators and students, focusing on scalability, performance, and accessibility.

## 🚀 Features

- Server-side rendered interface with Next.js App Router
- Accessible component library using ShadcnUI
- Type-safe development with TypeScript
- Responsive design with Tailwind CSS
- Form handling with React Hook Form and Zod validation
- Real-time data fetching with SWR
- Comprehensive test coverage with Jest and Testing Library
- Production-grade security with CSP headers and CORS policies

## 📋 Prerequisites

- Node.js 18+ (LTS version recommended)
- npm 9+ or yarn 1.22+
- Docker 24+ and Docker Compose 2.20+ (for containerized development)
- Backend API service (running locally or accessible endpoint)
- Git 2.40+ for version control
- VS Code with recommended extensions (optional)

## 🛠️ Tech Stack

| Technology | Version | Purpose |
|------------|---------|----------|
| Next.js | 13.4.0 | React framework with App Router |
| TypeScript | 5.0.4 | Static typing and enhanced DX |
| ShadcnUI | 0.1.0 | Accessible component library |
| Tailwind CSS | 3.3.2 | Utility-first styling |
| React Hook Form | 7.45.0 | Form state management |
| Zod | 3.21.4 | Runtime schema validation |
| Axios | 1.4.0 | HTTP client with interceptors |
| Jest | 29.5.0 | Testing framework |
| ESLint | 8.40.0 | Code quality tools |

## 🚦 Getting Started

1. Clone the repository:
```bash
git clone <repository_url>
cd src/web
```

2. Set up environment variables:
```bash
cp .env.example .env
```

3. Install dependencies:
```bash
npm install
```

4. Start development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## 🏗️ Build and Test

```bash
# Run linting
npm run lint

# Type checking
npm run type-check

# Run tests
npm run test

# Production build
npm run build

# Start production server
npm run start
```

## 🌲 Project Structure

```
src/web/
├── app/                 # Next.js App Router pages
├── components/          # Reusable UI components
├── lib/                 # Utility functions and hooks
├── styles/             # Global styles and Tailwind config
├── types/              # TypeScript type definitions
├── public/             # Static assets
└── tests/              # Test files
```

## 🔄 Development Workflow

### Branching Strategy
- Main branch: `main` (production)
- Feature branches: `feature/*`
- Bug fixes: `fix/*`
- Release branches: `release/*`

### Code Review Process
1. Create feature branch from `main`
2. Implement changes with tests
3. Submit PR with 2 required reviewers
4. Pass CI checks and code review
5. Merge to `main`

### Testing Requirements
- Unit test coverage > 90%
- E2E tests passing
- Accessibility tests passing
- Performance benchmarks met

## 🚀 Deployment

### Environments
1. Development
   - Local Docker environment
   - Hot reloading enabled
   - Debug tools active

2. Staging
   - Vercel Preview Deployments
   - Automated from PR
   - E2E testing environment

3. Production
   - Vercel Production Environment
   - Automated from `main`
   - Performance monitoring

## 🔧 Troubleshooting

### API Connection Issues
- Verify `NEXT_PUBLIC_API_URL` in `.env`
- Check CORS configuration
- Validate API health endpoint

### Type Errors
- Run `npm run type-check`
- Verify TypeScript configuration
- Check for outdated type definitions

### Build Failures
1. Clear build cache:
```bash
rm -rf .next
rm -rf node_modules
rm package-lock.json
npm install
```

2. Verify environment variables
3. Check for conflicting dependencies

## 🔍 Maintenance

### Regular Tasks
- Weekly dependency updates via Dependabot
- Daily automated security scans
- Performance monitoring via Vercel Analytics
- Type checking in CI pipeline

### Performance Optimization
- Bundle analysis with `npm run analyze`
- Implement code splitting
- Optimize image loading
- Monitor Core Web Vitals

## 🔒 Security

- CSP headers configured
- HTTPS enforced
- CORS policies implemented
- Security headers via Next.js config
- Regular dependency audits
- Protected API routes

## 📚 Documentation

Additional documentation:
- [Component Library](./docs/components.md)
- [API Integration](./docs/api.md)
- [Testing Guide](./docs/testing.md)
- [Deployment Guide](./docs/deployment.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Submit Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.