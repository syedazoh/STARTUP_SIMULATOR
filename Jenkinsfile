// CD pipeline: build -> test -> push to ECR -> deploy to EC2 via docker-compose.prod.yml.
// GitHub Actions (.github/workflows/) still runs fast PR-gating CI; this pipeline
// is the deployment path, triggered on merges to main.
//
// Required Jenkins credentials (Manage Jenkins > Credentials):
//   aws-ecr-creds   - AWS access key/secret with ECR push permissions
//   ec2-deploy-key  - SSH private key for the deploy user on the EC2 host
//
// Required Jenkins environment / parameters (set in the job configuration):
//   AWS_ACCOUNT_ID, AWS_REGION, EC2_HOST, EC2_USER, EC2_DEPLOY_PATH, VITE_API_URL
// (EC2_DEPLOY_PATH is where docker-compose.prod.yml + .env already live on the host —
//  see docs/deployment.md for the one-time EC2 setup that puts them there.)
// (VITE_API_URL is baked into the frontend bundle at build time, so set it to the
//  public HTTPS origin, e.g. https://app.example.com — the caddy service serves
//  /api/* from the same origin as the bundle.)

pipeline {
    agent any

    environment {
        AWS_REGION     = "${params.AWS_REGION ?: 'us-east-1'}"
        ECR_REGISTRY   = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        BACKEND_IMAGE  = "${ECR_REGISTRY}/startup-simulator-backend"
        FRONTEND_IMAGE = "${ECR_REGISTRY}/startup-simulator-frontend"
        CADDY_IMAGE     = "${ECR_REGISTRY}/startup-simulator-caddy"
        IMAGE_TAG      = "${env.GIT_COMMIT.take(7)}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Backend Image') {
            steps {
                dir('backend') {
                    sh "docker build -t ${BACKEND_IMAGE}:${IMAGE_TAG} -t ${BACKEND_IMAGE}:latest ."
                }
            }
        }

        stage('Test Backend') {
            steps {
                // No real GROQ_API_KEY needed: every test replaces each agent's
                // _structured_llm with a fake before exercising it.
                sh "docker run --rm ${BACKEND_IMAGE}:${IMAGE_TAG} python -m pytest -q"
            }
        }

        stage('Build Frontend Image') {
            steps {
                dir('frontend') {
                    sh """
                        docker build -f Dockerfile.prod \
                            --build-arg VITE_API_URL=${VITE_API_URL} \
                            -t ${FRONTEND_IMAGE}:${IMAGE_TAG} -t ${FRONTEND_IMAGE}:latest .
                    """
                }
            }
        }

        stage('Build Caddy Image') {
            steps {
                // Tiny image that just bakes in the Caddyfile, so the TLS config
                // ships with the commit instead of being synced onto the host.
                dir('docker/caddy') {
                    sh "docker build -t ${CADDY_IMAGE}:${IMAGE_TAG} -t ${CADDY_IMAGE}:latest ."
                }
            }
        }

        stage('Push to ECR') {
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-ecr-creds']]) {
                    sh """
                        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
                        docker push ${BACKEND_IMAGE}:${IMAGE_TAG}
                        docker push ${BACKEND_IMAGE}:latest
                        docker push ${FRONTEND_IMAGE}:${IMAGE_TAG}
                        docker push ${FRONTEND_IMAGE}:latest
                        docker push ${CADDY_IMAGE}:${IMAGE_TAG}
                        docker push ${CADDY_IMAGE}:latest
                    """
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                sshagent(credentials: ['ec2-deploy-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${EC2_USER}@${EC2_HOST} '
                            cd ${EC2_DEPLOY_PATH} &&
                            export BACKEND_IMAGE=${BACKEND_IMAGE}:${IMAGE_TAG} &&
                            export FRONTEND_IMAGE=${FRONTEND_IMAGE}:${IMAGE_TAG} &&
                            export CADDY_IMAGE=${CADDY_IMAGE}:${IMAGE_TAG} &&
                            docker compose -f docker-compose.prod.yml pull &&
                            docker compose -f docker-compose.prod.yml up -d &&
                            docker image prune -f
                        '
                    """
                }
            }
        }
    }

    post {
        success {
            echo "Deployed ${IMAGE_TAG} to ${EC2_HOST}."
        }
        failure {
            echo 'Pipeline failed — check the stage logs above. Nothing was deployed if Build/Test/Push failed; if Deploy itself failed, roll back per docs/deployment.md.'
        }
    }
}
