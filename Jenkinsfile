pipeline {
    agent {
        node {
            label 'Yamix1'
        }
    }
    
    environment {
        DOCKER_IMAGE = 'makdi41/edik-museum'
        DOCKER_TAG = "${BUILD_NUMBER}"
        APP_PORT = '5000'
        CONTAINER_NAME = 'edik-museum'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    // Сборка Docker образа
                    sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} ."
                    // Также создаем тег latest
                    sh "docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest"
                }
            }
        }
        
        stage('Login to DockerHub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'DockerHub', usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                    sh '''
                        echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
                    '''
                }
            }
        }
        
        stage('Push to DockerHub') {
            steps {
                script {
                    // Пуш образа с номером сборки
                    sh "docker push ${DOCKER_IMAGE}:${DOCKER_TAG}"
                    // Пуш образа с тегом latest
                    sh "docker push ${DOCKER_IMAGE}:latest"
                }
            }
        }

        stage('Deploy Service') {
            steps {
                script {
                    // Остановка и удаление существующего контейнера, если он есть
                    sh '''
                        if docker ps -a | grep -q ${CONTAINER_NAME}; then
                            docker stop ${CONTAINER_NAME} || true
                            docker rm ${CONTAINER_NAME} || true
                        fi
                    '''
                    
                    // Запуск нового контейнера
                    sh """
                        docker run -d \
                            --name ${CONTAINER_NAME} \
                            -p ${APP_PORT}:${APP_PORT} \
                            --restart unless-stopped \
                            ${DOCKER_IMAGE}:${DOCKER_TAG}
                    """
                    
                    // Проверка, что сервис запустился
                    sh '''
                        sleep 10
                        if ! docker ps | grep -q ${CONTAINER_NAME}; then
                            echo "Container failed to start"
                            exit 1
                        fi
                        
                        # Проверка доступности приложения
                        for i in {1..6}; do
                            if curl -s http://localhost:${APP_PORT} > /dev/null; then
                                echo "Application is responding on port ${APP_PORT}"
                                exit 0
                            fi
                            sleep 10
                        done
                        
                        echo "Application failed to respond within timeout"
                        exit 1
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo "Deployment successful! Service is running on port ${APP_PORT}"
        }
        
        failure {
            script {
                // В случае ошибки, пытаемся очистить за собой
                sh '''
                    docker stop ${CONTAINER_NAME} || true
                    docker rm ${CONTAINER_NAME} || true
                '''
            }
        }
        
        always {
            script {
                // Логаут из Docker Hub
                sh "docker logout"
                
                // Удаление локальных образов
                sh """
                    docker rmi ${DOCKER_IMAGE}:${DOCKER_TAG} || true
                    docker rmi ${DOCKER_IMAGE}:latest || true
                """
            }
        }
    }
} 