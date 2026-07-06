# Sprint 12 — migração dos containers locais (docker-compose.yml) e dos
# manifests de Kind (Sprint 10) para Cloud Run.
#
# EXERCÍCIO DE ARQUITETURA: não rode `terraform apply`, mesmo o Cloud Run
# tendo free tier (2M requests/mês) — mesma regra das outras duas migrações.

resource "google_artifact_registry_repository" "mlops_images" {
  location      = var.region
  repository_id = "mlops-images"
  format        = "DOCKER"
  project       = var.project_id
  # Substitui o `kind load docker-image` do Sprint 10 — no Cloud Run a
  # imagem precisa estar num registry acessível, não só no daemon local.
}

# Cloud Run é serverless: não vive dentro de uma VPC por padrão. Este
# connector é a ponte necessária para alcançar o Cloud SQL via IP privado
# (o mesmo motivo que existe o Cloud SQL Auth Proxy localmente).
resource "google_vpc_access_connector" "mlflow_connector" {
  name          = "mlflow-vpc-connector"
  region        = var.region
  network       = google_compute_network.mlops_vpc.name
  ip_cidr_range = "10.8.0.0/28"
}

resource "google_cloud_run_v2_service" "mlflow" {
  name     = "mlops-mlflow"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.mlflow_runner.email

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.mlops_images.repository_id}/mlflow:latest"

      # A URI de conexão real seria montada em runtime por um entrypoint que
      # lê POSTGRES_PASSWORD do Secret Manager — nunca literal aqui no .tf,
      # mesmo cuidado que já tomamos em cloud_sql.tf.
      env {
        name = "POSTGRES_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = "mlflow-postgres-password"
            version = "latest"
          }
        }
      }

      env {
        name  = "MLFLOW_BACKEND_STORE_URI"
        value = "postgresql://mlflow@/mlflow?host=/cloudsql/${google_sql_database_instance.mlflow_backend.connection_name}"
      }

      env {
        name  = "MLFLOW_DEFAULT_ARTIFACT_ROOT"
        value = "gs://${google_storage_bucket.mlflow_artifacts.name}/"
      }

      ports {
        container_port = 5000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 5000
        }
        initial_delay_seconds = 15
        period_seconds         = 5
      }
    }

    scaling {
      # min=1 porque o MLflow precisa estar sempre acessível para o time
      # consultar experimentos — diferente da API, ele NÃO escala a zero.
      min_instance_count = 1
      max_instance_count = 3
    }

    vpc_access {
      connector = google_vpc_access_connector.mlflow_connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }
  }
}

resource "google_cloud_run_v2_service" "api" {
  name     = "mlops-fraud-api"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.mlops_images.repository_id}/api:latest"

      env {
        name  = "MLFLOW_TRACKING_URI"
        value = google_cloud_run_v2_service.mlflow.uri # equivalente a http://mlflow:5000 no compose
      }

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          # equivalente a requests.cpu/limits.memory em deployment/k8s/api-deployment.yaml
          cpu    = "0.5"
          memory = "512Mi"
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8000
        }
        initial_delay_seconds = 15
        period_seconds         = 5
      }
    }

    scaling {
      # equivalente a minReplicas/maxReplicas em deployment/k8s/api-hpa.yaml —
      # mas aqui o gatilho é concorrência de requests, não % de CPU.
      min_instance_count = 2
      max_instance_count = 5
    }
  }
}

# Cloud Run expõe HTTPS público por padrão; este binding é o que de fato
# libera acesso externo (equivalente a um Service type=LoadBalancer no k8s).
resource "google_cloud_run_v2_service_iam_member" "api_public" {
  location = google_cloud_run_v2_service.api.location
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
