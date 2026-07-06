# Sprint 12 — migração do Postgres local (docker/docker-compose.yml) para Cloud SQL.
#
# EXERCÍCIO DE ARQUITETURA: não rode `terraform apply` neste arquivo.
# Cloud SQL não tem tier "always free" (diferente de Cloud Run e GCS), então
# esta etapa do Sprint 12 fica só no papel, por decisão explícita de custo.

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

variable "project_id" {
  description = "ID do projeto GCP"
  type        = string
}

variable "region" {
  description = "Região onde a instância roda"
  type        = string
  default     = "us-central1"
}

# --- Rede e identidade (provisório para este exercício) ---
# Em um deploy real, network.tf e iam.tf existiriam separados; aqui ficam
# juntos só para o arquivo ser autocontido e fácil de ler.

resource "google_compute_network" "mlops_vpc" {
  name                    = "mlops-vpc"
  auto_create_subnetworks = false
}

resource "google_service_account" "mlflow_runner" {
  account_id   = "mlflow-runner"
  display_name = "Service account usada pelo MLflow rodando no Cloud Run"
}

# Senha do usuário mlflow tradicional. Nunca em texto puro no .tf — o Secret
# Manager cumpre aqui o mesmo papel que o .env cumpre hoje localmente.
data "google_secret_manager_secret_version" "postgres_password" {
  secret = "mlflow-postgres-password"
}

resource "google_sql_database_instance" "mlflow_backend" {
  name              = "mlops-mlflow-backend"
  database_version  = "POSTGRES_16" # mesma major version do postgres:16-alpine local
  region            = var.region
  project           = var.project_id

  settings {
    # db-f1-micro é a menor instância disponível — ainda assim, cobrada.
    tier = "db-f1-micro"

    ip_configuration {
      ipv4_enabled    = false # sem IP público: só via VPC privada ou Cloud SQL Auth Proxy
      private_network = google_compute_network.mlops_vpc.id
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }

    # Habilita autenticação via IAM (service account do Cloud Run) como
    # alternativa a usuário/senha — ver comentário na Opção B abaixo.
    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }
  }

  # Protege contra `terraform destroy` acidental derrubar o banco de produção.
  deletion_protection = true
}

resource "google_sql_database" "mlflow_db" {
  name     = "mlflow" # equivalente a POSTGRES_DB no docker-compose.yml
  instance = google_sql_database_instance.mlflow_backend.name
}

# --- Opção A: usuário/senha tradicional (Secret Manager) ---
# Troca direta do .env local — mesmo modelo mental, só muda onde a senha mora.
# Indicado para projetos didáticos/simples.
resource "google_sql_user" "mlflow_user" {
  name     = "mlflow" # equivalente a POSTGRES_USER
  instance = google_sql_database_instance.mlflow_backend.name
  password = data.google_secret_manager_secret_version.postgres_password.secret_data
}

# --- Opção B: IAM database authentication (produção) ---
# Não existe senha estática: o Cloud Run se autentica com a identidade da
# service_account abaixo, e o Cloud SQL troca isso por um token OAuth de
# curta duração, renovado automaticamente. A connection string do MLflow
# continua no mesmo formato postgresql://— só a forma de autenticar muda.
resource "google_sql_user" "mlflow_service_account" {
  name     = google_service_account.mlflow_runner.email
  instance = google_sql_database_instance.mlflow_backend.name
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
}
