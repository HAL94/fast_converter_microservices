# Fast Converter Microservices

A sample microservices app with UV workspaces to build a video to mp3 converter system, for learning purposes.

# The objective

I wanted to try microservices, this project is based on the video tutorial by [`kantan coding`](https://www.youtube.com/watch?v=hmkF77F9TLw), however I did not follow the tutorial completely, I took the requriements and attempted to achieve it myself, the requirements are surmised as follows:

`A user uploads a video, and the system will convert the video to MP3 format, and notify the user by email and provide a download link for the file as an MP3 file.`

One thing I have not attempted to do is apply infrastructure `yaml` files for `Kubernetes`.

# Components
- **Gateway**
- **Auth**
- **RabbitMQ**
- **Video-to-MP3**
- **Notification**
- **Minio Storage**

# To Get Started
## Infrastructure
There are a few requirements, make sure to have the following installed:
- `Docker`
- `docker compose`
## Email Service API Key
Get your key from [Resend API Key](https://resend.com/), replace in `.env` file for the `notification` service.
## Environment
- For each `service` under the `services`, create an `.env` file, follow the `.env.example`.
- In root, also create an `.env` file (an `.env.example` is also available)
## To run the app
Use `docker compose up --build` in root


