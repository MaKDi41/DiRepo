pipeline {
    agent {
        node {
            label 'Yamix1'
        }
    }
    
    environment {
        DOCKERHUB_CREDENTIALS = credentials('DockerHub')
        DOCKER_IMAGE = 'makdi41/edik-museum'
        DOCKER_TAG = "${BUILD_NUMBER}"
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
                script {
                    // Логин в Docker Hub
                    sh "echo ${DOCKERHUB_CREDENTIALS_PSW} | docker login -u ${DOCKERHUB_CREDENTIALS_USR} --password-stdin"
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
    }
    
    post {
        always {
            // Очистка
            script {
                // Логаут из Docker Hub
                sh "docker logout"
                
                // Удаление локальных образов
                sh "docker rmi ${DOCKER_IMAGE}:${DOCKER_TAG}"
                sh "docker rmi ${DOCKER_IMAGE}:latest"
            }
        }
    }
} 