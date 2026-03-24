# docker-fastapi 

A sample project for deploying to a PaaS Service like Render or CSC Rahti.

### For deployment to Render

- Log in to https://render.com/
- Create a New Web Service.
- Connect to GitHub and choose Connect Credentials.
- Set Language to Docker.
- Select the EU Central region (or whatever is nearest to you)
- Choose Instance Type: Free.

### For deployment to CSC Rahti (OpenShift)

Note: Change the Git reference setting in OpenShift to *main*:    
    Edit BuildConfig ==> Show advanced git options ==> Git reference: `main`

### For local real-time development

Rename `.env-example` to `.env` to override the `MODE=production`set in the `Dockerfile`. Note that this needs a valueless declaration of `MODE` in `docker-compose.yml`

To run the container locally:
`docker-compose up --build`
