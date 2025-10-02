#!/usr/bin/env python3
"""
Update README.md with dynamic content from various sources
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
import requests
import yaml


class GitHubProfileUpdater:
    def __init__(self):
        self.github_token = os.environ.get('GH_TOKEN', "")
        self.headers = {
            'Authorization': f'Bearer {self.github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.username = 'sshailabh'
        self.readme_path = Path('README.md')
        
    def get_github_data(self):
        """Fetch data from GitHub API"""
        query = """
        query($username: String!) {
          user(login: $username) {
            repositories(first: 100, ownerAffiliations: OWNER, isFork: false, orderBy: {field: UPDATED_AT, direction: DESC}) {
              totalCount
              nodes {
                name
                description
                url
                stargazerCount
                forkCount
                primaryLanguage {
                  name
                  color
                }
                updatedAt
                isPrivate
              }
            }
            contributionsCollection {
              totalCommitContributions
              totalIssueContributions
              totalPullRequestContributions
              totalPullRequestReviewContributions
            }
          }
        }
        """
        
        response = requests.post(
            'https://api.github.com/graphql',
            json={'query': query, 'variables': {'username': self.username}},
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()['data']['user']
        else:
            print(f"Failed to fetch GitHub data: {response.status_code}")
            return None
    
    def get_template_engine_stats(self):
        """Get stats from awesome-template-engine repository"""
        try:
            # Try to read from the awesome-template-engine repo if it exists locally
            yaml_path = Path('../awesome-template-engine/gen/template-engines.yaml')
            if yaml_path.exists():
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    template_engines = data.get('template_engines', {})
                    total_engines = sum(len(engines) for engines in template_engines.values())
                    total_languages = len(template_engines)
                    return {
                        'total_engines': total_engines,
                        'total_languages': total_languages,
                        'last_update': datetime.now().strftime('%Y-%m-%d')
                    }
            else:
                # Fallback: fetch from GitHub
                response = requests.get(
                    f'https://api.github.com/repos/{self.username}/awesome-template-engine',
                    headers=self.headers
                )
                if response.status_code == 200:
                    repo_data = response.json()
                    return {
                        'total_engines': '150+',  # Approximate from README
                        'total_languages': '20+',  # Approximate
                        'last_update': repo_data.get('updated_at', '')[:10]
                    }
        except Exception as e:
            print(f"Error fetching template engine stats: {e}")
            return {
                'total_engines': 'N/A',
                'total_languages': 'N/A',
                'last_update': 'N/A'
            }
    
    def get_recent_activity(self, limit=5):
        """Get recent GitHub activity"""
        response = requests.get(
            f'https://api.github.com/users/{self.username}/events/public',
            headers=self.headers,
            params={'per_page': 30}
        )
        
        if response.status_code != 200:
            return []
        
        events = response.json()
        activities = []
        
        for event in events:
            activity = None
            event_type = event.get('type', '')
            repo_name = event.get('repo', {}).get('name', '')
            created_at = event.get('created_at', '')[:10]
            
            if event_type == 'PushEvent':
                commits = event.get('payload', {}).get('commits', [])
                if commits:
                    activity = f"🔨 Pushed {len(commits)} commit(s) to [{repo_name}](https://github.com/{repo_name})"
            elif event_type == 'CreateEvent':
                ref_type = event.get('payload', {}).get('ref_type', '')
                if ref_type == 'repository':
                    activity = f"📦 Created new repository [{repo_name}](https://github.com/{repo_name})"
            elif event_type == 'PullRequestEvent':
                action = event.get('payload', {}).get('action', '')
                pr_number = event.get('payload', {}).get('pull_request', {}).get('number', '')
                if action == 'opened':
                    activity = f"🔄 Opened PR [#{pr_number}](https://github.com/{repo_name}/pull/{pr_number}) in {repo_name}"
            elif event_type == 'IssuesEvent':
                action = event.get('payload', {}).get('action', '')
                issue_number = event.get('payload', {}).get('issue', {}).get('number', '')
                if action == 'opened':
                    activity = f"📝 Opened issue [#{issue_number}](https://github.com/{repo_name}/issues/{issue_number}) in {repo_name}"
            elif event_type == 'WatchEvent':
                activity = f"⭐ Starred [{repo_name}](https://github.com/{repo_name})"
            
            if activity and len(activities) < limit:
                activities.append(f"- {activity} - {created_at}")
        
        return activities
    
    def update_section(self, content, start_marker, end_marker, new_content):
        """Update a section in the README between markers"""
        pattern = re.compile(
            rf'({re.escape(start_marker)})(.*?)({re.escape(end_marker)})',
            re.DOTALL
        )
        replacement = f'{start_marker}\n{new_content}\n{end_marker}'
        return pattern.sub(replacement, content)
    
    def update_readme(self):
        """Update README with latest data"""
        if not self.readme_path.exists():
            print("README.md not found!")
            return
        
        with open(self.readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update current focus (you can customize this)
        now_content = """- 🤖 Building AI Copilots and intelligent assistants at Adobe
- 📚 Exploring advanced Neural Topic Modeling techniques
- 🔧 Developing Domain-Specific Languages for better developer experience
- 🌐 Working on scalable distributed systems
- 📝 Maintaining [awesome-template-engine](https://github.com/sshailabh/awesome-template-engine) - A curated list of template engines"""
        content = self.update_section(content, '<!-- START:now -->', '<!-- END:now -->', now_content)
        
        # Update template engine stats
        template_stats = self.get_template_engine_stats()
        stats_content = f"""**Total Template Engines Tracked**: {template_stats['total_engines']}  
**Languages Covered**: {template_stats['total_languages']}  
**Last Updated**: {template_stats['last_update']}"""
        content = self.update_section(content, '<!-- START:template-stats -->', '<!-- END:template-stats -->', stats_content)
        
        # Update recent activity
        activities = self.get_recent_activity()
        if activities:
            activity_content = '\n'.join(activities)
        else:
            activity_content = "*No recent public activity*"
        content = self.update_section(content, '<!-- START:activity -->', '<!-- END:activity -->', activity_content)
        
        # Update featured projects (can be enhanced with more logic)
        github_data = self.get_github_data()
        if github_data:
            repos = [repo for repo in github_data['repositories']['nodes'] if not repo['isPrivate']]
            # Sort by stars and recent updates
            featured_repos = sorted(repos, key=lambda x: (x['stargazerCount'], x['updatedAt']), reverse=True)[:2]
            
            projects_content = ""
            for repo in featured_repos:
                lang = repo['primaryLanguage']['name'] if repo['primaryLanguage'] else 'N/A'
                projects_content += f"""### [{repo['name']}]({repo['url']})
{repo['description'] or 'No description available'}

**Language**: {lang} | **Stars**: {repo['stargazerCount']} | **Forks**: {repo['forkCount']}

"""
            
            content = self.update_section(content, '<!-- START:projects -->', '<!-- END:projects -->', projects_content.strip())
        
        # Write updated content
        with open(self.readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ README.md updated successfully at {datetime.now()}")


if __name__ == '__main__':
    updater = GitHubProfileUpdater()
    updater.update_readme()