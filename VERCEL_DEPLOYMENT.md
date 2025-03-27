# Deploying Central Search to Vercel

This guide provides instructions for deploying the Central Search project to Vercel to make it accessible at https://sheikh-bot.vercel.app/ or your own custom domain.

## Prerequisites

1. A [Vercel](https://vercel.com/) account
2. The Central Search repository (this repository)
3. Git installed on your local machine

## Deployment Steps

### Option 1: Deploy directly from GitHub

1. Fork or clone this repository to your GitHub account
2. Log in to your Vercel account
3. Click "New Project"
4. Import your GitHub repository
5. Configure the project:
   - Framework Preset: Other
   - Build Command: Leave blank (not required for static sites)
   - Output Directory: Leave blank (uses root directory)
   - Install Command: Leave blank
6. Click "Deploy"

### Option 2: Deploy using Vercel CLI

1. Install the Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Log in to your Vercel account:
   ```bash
   vercel login
   ```

3. Navigate to your project directory and deploy:
   ```bash
   cd path/to/sheikhbot
   vercel
   ```

4. Follow the prompts to complete the deployment

## Configuration

The project includes a `vercel.json` file that configures the deployment with:

- Static file handling for HTML and asset files
- Route configuration for clean URLs
- Redirects for common paths like `/search`, `/seo`, etc.

## Custom Domain Setup

To use a custom domain instead of the default `sheikh-bot.vercel.app`:

1. Go to your project in the Vercel dashboard
2. Navigate to "Settings" > "Domains"
3. Add your custom domain and follow the verification steps

## Environment Variables

If you need to set environment variables for the Central Search API:

1. Go to your project in the Vercel dashboard
2. Navigate to "Settings" > "Environment Variables"
3. Add variables as needed (e.g., `CLIENT_SECRET`, API keys, etc.)

## Continuous Deployment

Vercel automatically deploys changes when you push to your repository. If you need to disable this:

1. Go to your project in the Vercel dashboard
2. Navigate to "Settings" > "Git"
3. Configure your preferred deployment settings

## Troubleshooting

- **404 Errors**: Check the routes in `vercel.json` to ensure proper path handling
- **Missing Assets**: Ensure all required files are committed to your repository
- **Deployment Failures**: Check the Vercel deployment logs for detailed error messages

## Need Help?

If you encounter any issues with your Vercel deployment, consult the [Vercel documentation](https://vercel.com/docs) or open an issue in this repository. 