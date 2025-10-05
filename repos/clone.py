import subprocess

repos = [
    "https://github.com/apache/commons-text.git",
    "https://github.com/apache/commons-io.git",
    "https://github.com/apache/commons-lang.git",
    "https://github.com/apache/commons-collections.git",
    "https://github.com/junit-team/junit4.git",
    "https://github.com/junit-team/junit-framework.git",
    "https://github.com/google/guava.git",
    "https://github.com/apache/hadoop.git",
    "https://github.com/mockito/mockito.git",
    "https://github.com/spring-projects/spring-boot.git",
    "https://github.com/apache/spark.git",
    "https://github.com/dbeaver/dbeaver.git",
    "https://github.com/jenkinsci/jenkins.git",
    "https://github.com/elastic/elasticsearch.git",
]

for repo_url in repos:
    subprocess.run(["git", "clone", repo_url])