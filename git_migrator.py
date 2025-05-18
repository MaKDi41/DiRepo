#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
import requests
from urllib.parse import urlparse
import json
import time

class GitMigrator:
    def __init__(self):
        self.supported_platforms = {
            'github': {
                'api_url': 'https://api.github.com',
                'clone_url': 'https://github.com'
            },
            'gitlab': {
                'api_url': 'https://gitlab.com/api/v4',
                'clone_url': 'https://gitlab.com'
            },
            'gitea': {
                'api_url': None,  # Будет установлено при инициализации
                'clone_url': None  # Будет установлено при инициализации
            }
        }

    def set_credentials(self, source_token, target_token, source_platform, target_platform, gitea_url=None):
        self.source_token = source_token
        self.target_token = target_token
        self.source_platform = source_platform.lower()
        self.target_platform = target_platform.lower()
        
        # Настройка URL для Gitea если используется
        if gitea_url and (source_platform == 'gitea' or target_platform == 'gitea'):
            self.supported_platforms['gitea']['api_url'] = f"{gitea_url}/api/v1"
            self.supported_platforms['gitea']['clone_url'] = gitea_url

    def validate_platforms(self):
        if self.source_platform not in self.supported_platforms:
            raise ValueError(f"Source platform {self.source_platform} not supported")
        if self.target_platform not in self.supported_platforms:
            raise ValueError(f"Target platform {self.target_platform} not supported")

    def get_headers(self, platform, token):
        if platform == 'github':
            return {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
        elif platform == 'gitlab':
            return {
                'PRIVATE-TOKEN': token
            }
        elif platform == 'gitea':
            return {
                'Authorization': f'token {token}'
            }
        return {}

    def create_target_repo(self, repo_name, description=""):
        api_url = self.supported_platforms[self.target_platform]['api_url']
        headers = self.get_headers(self.target_platform, self.target_token)
        
        if self.target_platform == 'github':
            data = {
                'name': repo_name,
                'description': description,
                'private': False
            }
            response = requests.post(f"{api_url}/user/repos", headers=headers, json=data)
        
        elif self.target_platform == 'gitlab':
            data = {
                'name': repo_name,
                'description': description,
                'visibility': 'public'
            }
            response = requests.post(f"{api_url}/projects", headers=headers, json=data)
        
        elif self.target_platform == 'gitea':
            data = {
                'name': repo_name,
                'description': description,
                'private': False
            }
            response = requests.post(f"{api_url}/user/repos", headers=headers, json=data)
        
        if response.status_code not in [201, 200]:
            raise Exception(f"Failed to create repository: {response.text}")
        
        return response.json()

    def migrate_repository(self, source_url, target_namespace):
        # Извлекаем имя репозитория из URL
        repo_name = source_url.split('/')[-1].replace('.git', '')
        work_dir = f"temp_migration_{int(time.time())}"
        
        try:
            # Создаем временную директорию
            os.makedirs(work_dir, exist_ok=True)
            os.chdir(work_dir)
            
            # Клонируем исходный репозиторий
            print(f"Cloning repository {source_url}...")
            subprocess.run(['git', 'clone', '--mirror', source_url, '.'], check=True)
            
            # Создаем новый репозиторий на целевой платформе
            target_repo = self.create_target_repo(repo_name)
            
            # Получаем URL для push
            if self.target_platform == 'github':
                target_url = f"https://oauth2:{self.target_token}@github.com/{target_namespace}/{repo_name}.git"
            elif self.target_platform == 'gitlab':
                target_url = f"https://oauth2:{self.target_token}@gitlab.com/{target_namespace}/{repo_name}.git"
            elif self.target_platform == 'gitea':
                base_url = self.supported_platforms['gitea']['clone_url'].replace('https://', '')
                target_url = f"https://oauth2:{self.target_token}@{base_url}/{target_namespace}/{repo_name}.git"
            
            # Пушим все ветки и теги
            print(f"Pushing to {self.target_platform}...")
            subprocess.run(['git', 'push', '--mirror', target_url], check=True)
            
            print(f"Migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            return False
            
        finally:
            # Очистка
            os.chdir('..')
            subprocess.run(['rm', '-rf', work_dir], check=True)

def main():
    parser = argparse.ArgumentParser(description='Migrate Git repository between platforms')
    parser.add_argument('--source-platform', required=True, help='Source platform (github/gitlab/gitea)')
    parser.add_argument('--target-platform', required=True, help='Target platform (github/gitlab/gitea)')
    parser.add_argument('--source-token', required=True, help='Source platform API token')
    parser.add_argument('--target-token', required=True, help='Target platform API token')
    parser.add_argument('--source-url', required=True, help='Source repository URL')
    parser.add_argument('--target-namespace', required=True, help='Target namespace (username or organization)')
    parser.add_argument('--gitea-url', help='Gitea instance URL (required if using Gitea)')
    
    args = parser.parse_args()
    
    migrator = GitMigrator()
    migrator.set_credentials(
        args.source_token,
        args.target_token,
        args.source_platform,
        args.target_platform,
        args.gitea_url
    )
    
    migrator.validate_platforms()
    success = migrator.migrate_repository(args.source_url, args.target_namespace)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 