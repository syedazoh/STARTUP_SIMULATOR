// Selected release: Next standalone + one API authority + seven analysis workers.
// Controller execution and AWS rollout require operator evidence; no deploy by default.
pipeline {
    agent any
    parameters {
        string(name: 'AWS_REGION', defaultValue: 'us-east-1', description: 'AWS region for the explicitly authorized release')
        booleanParam(name: 'DEPLOY_TO_PRODUCTION', defaultValue: false,
            description: 'Explicitly publish immutable images and deploy the prepared Next topology.')
    }
    environment { AWS_REGION = "${params.AWS_REGION}" }
    stages {
        stage('Checkout') { steps { checkout scm } }
        stage('Resolve immutable images') {
            steps { script {
                env.IMAGE_TAG = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                env.REGISTRY = env.AWS_ACCOUNT_ID ? "${env.AWS_ACCOUNT_ID}.dkr.ecr.${env.AWS_REGION}.amazonaws.com" : 'local'
                env.BACKEND_IMAGE = "${env.REGISTRY}/startup-simulator-backend"
                env.WORKER_IMAGE = "${env.REGISTRY}/startup-simulator-role-worker"
                env.FRONTEND_IMAGE = "${env.REGISTRY}/startup-simulator-next"
                env.CADDY_IMAGE = "${env.REGISTRY}/startup-simulator-caddy-next"
                env.TEST_NETWORK = "startup-ci-${env.BUILD_TAG}".replaceAll('[^a-zA-Z0-9_.-]', '-')
                env.TEST_MONGO = "${env.TEST_NETWORK}-mongo"
                if (params.DEPLOY_TO_PRODUCTION && (!env.AWS_ACCOUNT_ID || !env.EC2_HOST || !env.EC2_USER || !env.EC2_DEPLOY_PATH)) {
                    error('Publishing/deployment requires configured AWS account and EC2 destination')
                }
            } }
        }
        stage('Build backend and model caches') {
            steps { sh 'docker build -t "$BACKEND_IMAGE:$IMAGE_TAG" backend' }
        }
        stage('Build minimal role worker') {
            steps { sh 'docker build -f backend/Dockerfile.worker -t "$WORKER_IMAGE:$IMAGE_TAG" backend' }
        }
        stage('Test with real isolated Mongo') {
            steps {
                sh '''
                    mkdir -p test-results
                    docker network create "$TEST_NETWORK"
                    docker run -d --name "$TEST_MONGO" --network "$TEST_NETWORK" mongo:7
                    ready=0
                    for attempt in $(seq 1 60); do
                        if docker exec "$TEST_MONGO" mongosh --quiet --eval 'db.adminCommand({ping:1})' >/dev/null 2>&1; then ready=1; break; fi
                        sleep 1
                    done
                    test "$ready" = 1
                    docker run --rm --network "$TEST_NETWORK" \
                        -e MONGODB_INTEGRATION_URL="mongodb://$TEST_MONGO:27017" \
                        -e GROQ_API_KEY= \
                        -v "$WORKSPACE/test-results:/test-results" \
                        -v "$WORKSPACE/datasets:/datasets:ro" \
                        -v "$WORKSPACE/scripts:/scripts:ro" \
                        "$BACKEND_IMAGE:$IMAGE_TAG" python -m pytest -q --junitxml=/test-results/backend.xml
                    docker run --rm -e PYTHONPATH=/app "$BACKEND_IMAGE:$IMAGE_TAG" \
                        python scripts/evaluate_knowledge.py --require-hybrid --min-pass 49 --output /tmp/knowledge-evaluation.json
                '''
            }
        }
        stage('Build and test Next image') {
            steps { sh 'docker build -f web/Dockerfile -t "$FRONTEND_IMAGE:$IMAGE_TAG" .' }
        }
        stage('Build and validate Next ingress') {
            steps { sh '''
                docker build --build-arg CADDYFILE=Caddyfile.next -t "$CADDY_IMAGE:$IMAGE_TAG" docker/caddy
                docker run --rm -e APP_DOMAIN=example.invalid -e ACME_EMAIL=operator@example.invalid \
                    "$CADDY_IMAGE:$IMAGE_TAG" caddy validate --config /etc/caddy/Caddyfile
            ''' }
        }
        stage('Rehearse selected private topology') {
            steps { sh '''
                SMOKE_WORKER_IMAGE="$WORKER_IMAGE:$IMAGE_TAG" \
                SMOKE_BACKEND_IMAGE="$BACKEND_IMAGE:$IMAGE_TAG" \
                SMOKE_FRONTEND_IMAGE="$FRONTEND_IMAGE:$IMAGE_TAG" \
                SMOKE_CADDY_IMAGE="$CADDY_IMAGE:$IMAGE_TAG" \
                  python3 scripts/smoke_next_release.py
            ''' }
        }
        stage('Push immutable images') {
            when { expression { params.DEPLOY_TO_PRODUCTION == true } }
            steps {
                withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', credentialsId: 'aws-ecr-creds']]) {
                    sh '''
                        aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$REGISTRY"
                        docker push "$BACKEND_IMAGE:$IMAGE_TAG"
                        docker push "$WORKER_IMAGE:$IMAGE_TAG"
                        docker push "$FRONTEND_IMAGE:$IMAGE_TAG"
                        docker push "$CADDY_IMAGE:$IMAGE_TAG"
                    '''
                }
            }
        }
        stage('Deploy prepared Next topology') {
            when { expression { params.DEPLOY_TO_PRODUCTION == true } }
            steps {
                withCredentials([file(credentialsId: 'ec2-known-hosts', variable: 'KNOWN_HOSTS')]) {
                    sshagent(credentials: ['ec2-deploy-key']) {
                        sh '''
                            # Operator values must be simple SSH identifiers/paths, never shell text.
                            case "$EC2_USER@$EC2_HOST:$EC2_DEPLOY_PATH" in *[!a-zA-Z0-9_@./:-]*) exit 1;; esac
                            ssh -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$KNOWN_HOSTS" "$EC2_USER@$EC2_HOST" \
                              "cd '$EC2_DEPLOY_PATH' && BACKEND_IMAGE='$BACKEND_IMAGE:$IMAGE_TAG' WORKER_IMAGE='$WORKER_IMAGE:$IMAGE_TAG' FRONTEND_IMAGE='$FRONTEND_IMAGE:$IMAGE_TAG' CADDY_IMAGE='$CADDY_IMAGE:$IMAGE_TAG' bash scripts/deploy.sh"
                        '''
                    }
                }
            }
        }
    }
    post {
        always {
            junit allowEmptyResults: true, testResults: 'test-results/*.xml'
            sh 'if [ -n "$TEST_MONGO" ]; then docker rm -f "$TEST_MONGO" || true; fi; if [ -n "$TEST_NETWORK" ]; then docker network rm "$TEST_NETWORK" || true; fi'
        }
        success { echo 'Configured gates passed. Deployment occurs only when explicitly enabled; verify controller logs and application health.' }
        failure { echo 'A release gate failed. Do not promote; preserve logs and follow the rollback runbook if a deployment was attempted.' }
    }
}
