# Deployment Guide

This guide provides step-by-step instructions for deploying the AI Pull Request Review Agent. The backend is deployed on **Render**, and the frontend is deployed on **Vercel**.

## Prerequisites

1.  **Accounts**: Make sure you have accounts on [GitHub](https://github.com/), [Render](https://render.com/), and [Vercel](https://vercel.com/).
2.  **Push to GitHub**: Ensure your latest code, including all the recent changes, is pushed to a GitHub repository.

---

## Part 1: Deploying the Backend to Render

We will deploy the Python/Flask backend as a Web Service on Render.

### Steps

1.  **Create a New Web Service**:
    *   Log in to your Render dashboard.
    *   Click the **New +** button and select **Web Service**.
    *   Connect your GitHub account and select your repository.

2.  **Configure the Service**:
    *   **Name**: Give your service a name (e.g., `pr-review-agent-backend`).
    *   **Root Directory**: `backend` (This is important, as it tells Render where to find your backend code).
    *   **Environment**: `Python 3`.
    *   **Region**: Choose a region close to you.
    *   **Branch**: Select the branch you want to deploy (e.g., `main`).

3.  **Set the Build and Start Commands**:
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `gunicorn app:app`

4.  **Choose an Instance Type**:
    *   The **Free** instance type is suitable for testing and personal use.

5.  **Add Environment Variables**:
    *   Under the **Environment** section, click **Add Environment Variable** for each of the following:
        *   `NEO4J_URI`: Your Neo4j database URI.
        *   `NEO4J_USER`: Your Neo4j database username.
        *   `NEO4J_PASSWORD`: Your Neo4j database password.
        *   `GEMINI_API_KEY`: Your Google Gemini API key.
        *   `FRONTEND_URL`: Leave this blank for now. We will fill this in after deploying the frontend.

6.  **Create Web Service**:
    *   Click the **Create Web Service** button. Render will start building and deploying your application.
    *   Once the deployment is live, copy the URL provided by Render (e.g., `https-your-backend-app.onrender.com`). You will need this for the frontend deployment.

---

## Part 2: Deploying the Frontend to Vercel

We will deploy the Next.js frontend to Vercel.

### Steps

1.  **Create a New Project**:
    *   Log in to your Vercel dashboard.
    *   Click the **Add New...** button and select **Project**.
    *   Connect your GitHub account and select the same repository.

2.  **Configure the Project**:
    *   **Framework Preset**: Vercel should automatically detect that this is a **Next.js** project.
    *   **Root Directory**: Set this to `frontend`.

3.  **Add Environment Variables**:
    *   Expand the **Environment Variables** section.
    *   Add the following variable:
        *   **Name**: `NEXT_PUBLIC_API_URL`
        *   **Value**: Paste the URL of your Render backend that you copied in the previous section (e.g., `https://your-backend-app.onrender.com`).

4.  **Deploy**:
    *   Click the **Deploy** button. Vercel will build and deploy your frontend.
    *   Once the deployment is complete, Vercel will provide you with a URL for your live site (e.g., `https://your-frontend-app.vercel.app`).

---

## Part 3: Final Configuration

Finally, we need to link the frontend and backend together by updating the `FRONTEND_URL` on Render.

1.  **Update Backend Environment Variable**:
    *   Go back to your Render dashboard and navigate to your backend service.
    *   Go to the **Environment** tab.
    *   Update the `FRONTEND_URL` variable with the URL of your Vercel frontend (e.g., `https://your-frontend-app.vercel.app`).
    *   Save the changes. Render will automatically trigger a new deployment with the updated environment variable.

Your application is now fully deployed and configured! You should be able to access your frontend via the Vercel URL and have it communicate with your backend on Render.
