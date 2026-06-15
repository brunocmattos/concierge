# Terraform that provisions the Concierge database (Postgres + pgvector)
# using the Docker provider - same tool you would use on AWS/GCP, just a different provider.

terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_image" "db" {
  name         = "pgvector/pgvector:pg16"
  keep_locally = true   # do NOT delete the image on destroy (it is shared with the compose stack)
}

resource "docker_volume" "pgdata" {
  name = "concierge_tf_pgdata"
}

resource "docker_container" "db" {
  name  = "concierge-db-tf"
  image = docker_image.db.image_id

  env = [
    "POSTGRES_USER=concierge",
    "POSTGRES_PASSWORD=concierge",
    "POSTGRES_DB=concierge",
  ]

  ports {
    internal = 5432
    external = 5433
  }

  volumes {
    volume_name    = docker_volume.pgdata.name
    container_path = "/var/lib/postgresql/data"
  }
}

output "db_endpoint" {
  value = "localhost:5433"
}