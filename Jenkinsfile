pipeline {
  agent { node { label 'ubuntu_docker_label' } }
  parameters{
    string(name: 'RELEASE_IMAGE_VERSION ', defaultValue: '', description: 'Release version?') 
  }
  environment{
    IMAGE_REGISTRY = infobloxcto
  }
  stages{
    stage("Build image"){
      steps{      
        withDockerRegistry([credentialsId: "dockerhub-bloxcicd", url: ""]) {      
          sh "make image"
        }
      }
    }
    stage("Build and push image"){
      when { not { changeRequest() } }
      steps{      
        withDockerRegistry([credentialsId: "dockerhub-bloxcicd", url: ""]) {      
          sh "make push"
        }
      }
    }
  }
  post{
    always {
      sh "make clean || true"
    }
  }
}